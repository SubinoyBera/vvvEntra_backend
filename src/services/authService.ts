import crypto from "crypto";
import { config } from "../config.js";
import { store } from "../db/store.js";
import {
  AccountSuspended,
  EmailAlreadyRegistered,
  InvalidCredentials,
  RefreshConflict,
  RefreshTokenInvalid,
  WrongRole,
} from "../core/exceptions.js";
import {
  createAccessToken,
  generateRefreshToken,
  hashPassword,
  hashToken,
  verifyPassword,
} from "../core/security.js";
import { verifyGoogleIdToken } from "../core/googleAuth.js";
import { RefreshTokenRecord, User, UserRole, UserStatus } from "../types/index.js";

const ROLE_LABELS: Record<string, string> = {
  [UserRole.INVESTOR]: "Investor / Buyer",
  [UserRole.ARCHITECT]: "Architect / Creator",
};

export interface SessionResult {
  user: User;
  accessToken: string;
  expiresIn: number;
  refreshToken: string;
  refreshMaxAgeSeconds: number | null;
}

export interface GoogleSessionResult extends SessionResult {
  isNewUser: boolean;
}

export async function issueSession(
  user: User,
  options: {
    rememberMe: boolean;
    userAgent: string | null;
    ipAddress: string | null;
    familyId?: string | null;
  }
): Promise<SessionResult> {
  const { accessToken, expiresIn } = createAccessToken(user.id, user.role);
  const { raw: rawRefresh, hash: refreshHash } = generateRefreshToken();
  const days = options.rememberMe ? config.refreshTokenRememberDays : config.refreshTokenDays;

  const record: RefreshTokenRecord = {
    id: crypto.randomUUID(),
    userId: user.id,
    tokenHash: refreshHash,
    familyId: options.familyId || crypto.randomUUID(),
    rememberMe: options.rememberMe,
    expiresAt: new Date(Date.now() + days * 86400 * 1000),
    usedAt: null,
    revokedAt: null,
    createdAt: new Date(),
    userAgent: options.userAgent ? options.userAgent.slice(0, 255) : null,
    ipAddress: options.ipAddress || null,
  };

  store.refreshTokens.set(refreshHash, record);

  return {
    user,
    accessToken,
    expiresIn,
    refreshToken: rawRefresh,
    refreshMaxAgeSeconds: options.rememberMe ? days * 86400 : null,
  };
}

export async function registerUser(params: {
  email: string;
  password: string;
  role: UserRole;
  rememberMe: boolean;
  userAgent: string | null;
  ipAddress: string | null;
}): Promise<SessionResult> {
  const email = params.email.trim().toLowerCase();
  if (store.usersByEmail.has(email)) {
    throw new EmailAlreadyRegistered();
  }

  const id = crypto.randomUUID();
  const now = new Date().toISOString();
  const passwordHash = await hashPassword(params.password);

  const user: User = {
    id,
    email,
    passwordHash,
    fullName: null,
    role: params.role,
    status: UserStatus.ONBOARDING,
    emailVerifiedAt: null,
    googleSub: null,
    reviewedAt: null,
    reviewedById: null,
    lastLoginAt: null,
    createdAt: now,
    updatedAt: now,
  };

  store.users.set(id, user);
  store.usersByEmail.set(email, id);

  return issueSession(user, {
    rememberMe: params.rememberMe,
    userAgent: params.userAgent,
    ipAddress: params.ipAddress,
  });
}

export async function loginUser(params: {
  email: string;
  password: string;
  expectedRole?: UserRole | null;
  rememberMe: boolean;
  userAgent: string | null;
  ipAddress: string | null;
}): Promise<SessionResult> {
  const email = params.email.trim().toLowerCase();
  const userId = store.usersByEmail.get(email);
  const user = userId ? store.users.get(userId) : null;

  if (!user || !user.passwordHash) {
    throw new InvalidCredentials();
  }

  const passwordOk = await verifyPassword(params.password, user.passwordHash);
  if (!passwordOk) {
    throw new InvalidCredentials();
  }

  if (user.status === UserStatus.SUSPENDED) {
    throw new AccountSuspended();
  }

  if (params.expectedRole && params.expectedRole !== user.role) {
    const label = ROLE_LABELS[user.role] || user.role;
    throw new WrongRole(`This email is registered as an ${label} account.`);
  }

  user.lastLoginAt = new Date().toISOString();
  user.updatedAt = new Date().toISOString();

  return issueSession(user, {
    rememberMe: params.rememberMe,
    userAgent: params.userAgent,
    ipAddress: params.ipAddress,
  });
}

export async function refreshSession(params: {
  rawToken?: string | null;
  userAgent: string | null;
  ipAddress: string | null;
}): Promise<SessionResult> {
  if (!params.rawToken) {
    throw new RefreshTokenInvalid();
  }

  const hash = hashToken(params.rawToken);
  const token = store.refreshTokens.get(hash);
  if (!token) {
    throw new RefreshTokenInvalid();
  }

  const now = new Date();
  if (token.revokedAt || token.expiresAt <= now) {
    throw new RefreshTokenInvalid();
  }

  if (token.usedAt) {
    const elapsedSeconds = (now.getTime() - token.usedAt.getTime()) / 1000;
    if (elapsedSeconds <= 10) {
      throw new RefreshConflict();
    }

    // Revoke entire token family on replay attack
    for (const t of store.refreshTokens.values()) {
      if (t.familyId === token.familyId) {
        t.revokedAt = now;
      }
    }
    throw new RefreshTokenInvalid();
  }

  const user = store.users.get(token.userId);
  if (!user) {
    throw new RefreshTokenInvalid();
  }

  if (user.status === UserStatus.SUSPENDED) {
    for (const t of store.refreshTokens.values()) {
      if (t.familyId === token.familyId) {
        t.revokedAt = now;
      }
    }
    throw new AccountSuspended();
  }

  token.usedAt = now;

  return issueSession(user, {
    rememberMe: token.rememberMe,
    userAgent: params.userAgent,
    ipAddress: params.ipAddress,
    familyId: token.familyId,
  });
}

export async function logout(params: { rawToken?: string | null }): Promise<void> {
  if (!params.rawToken) return;
  const hash = hashToken(params.rawToken);
  const token = store.refreshTokens.get(hash);
  if (token) {
    const now = new Date();
    for (const t of store.refreshTokens.values()) {
      if (t.familyId === token.familyId) {
        t.revokedAt = now;
      }
    }
  }
}

export async function authenticateWithGoogle(params: {
  credential: string;
  expectedRole?: UserRole | null;
  rememberMe: boolean;
  userAgent: string | null;
  ipAddress: string | null;
}): Promise<GoogleSessionResult> {
  const googlePayload = await verifyGoogleIdToken(params.credential);
  const { googleSub, email, name, emailVerified } = googlePayload;

  // 1. Check if user already linked with this googleSub
  let userId = store.usersByGoogleSub.get(googleSub);
  let user = userId ? store.users.get(userId) : null;
  let isNewUser = false;

  // 2. If not found by googleSub, check if user exists with this email
  if (!user) {
    userId = store.usersByEmail.get(email);
    user = userId ? store.users.get(userId) : null;

    if (user) {
      // Link Google account to existing email account
      user.googleSub = googleSub;
      store.usersByGoogleSub.set(googleSub, user.id);
    }
  }

  // 3. If still not found, create new user (Sign Up)
  if (!user) {
    isNewUser = true;
    const targetRole = params.expectedRole || UserRole.INVESTOR;
    const now = new Date().toISOString();
    const newId = crypto.randomUUID();

    user = {
      id: newId,
      email,
      passwordHash: null, // Null for accounts created via Google
      fullName: name || null,
      role: targetRole,
      status: UserStatus.ONBOARDING,
      emailVerifiedAt: emailVerified ? now : null,
      googleSub,
      reviewedAt: null,
      reviewedById: null,
      lastLoginAt: now,
      createdAt: now,
      updatedAt: now,
    };

    store.users.set(newId, user);
    store.usersByEmail.set(email, newId);
    store.usersByGoogleSub.set(googleSub, newId);
  } else {
    // Existing user checks
    if (user.status === UserStatus.SUSPENDED) {
      throw new AccountSuspended();
    }

    if (params.expectedRole && params.expectedRole !== user.role) {
      const label = ROLE_LABELS[user.role] || user.role;
      throw new WrongRole(`This Google account is registered as an ${label} account.`);
    }

    const now = new Date().toISOString();
    if (!user.emailVerifiedAt && emailVerified) {
      user.emailVerifiedAt = now;
    }
    if (!user.fullName && name) {
      user.fullName = name;
    }
    user.lastLoginAt = now;
    user.updatedAt = now;
  }

  const session = await issueSession(user, {
    rememberMe: params.rememberMe,
    userAgent: params.userAgent,
    ipAddress: params.ipAddress,
  });

  return {
    ...session,
    isNewUser,
  };
}
