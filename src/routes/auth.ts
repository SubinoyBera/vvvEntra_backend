import { Router } from "express";
import { AppError } from "../core/exceptions.js";
import {
  clearRefreshCookie,
  REFRESH_COOKIE_NAME,
  setRefreshCookie,
} from "../core/cookies.js";
import {
  authenticateWithGoogle,
  loginUser,
  logout,
  refreshSession,
  registerUser,
  SessionResult,
} from "../services/authService.js";
import { UserRole } from "../types/index.js";
import { verifyOrigin } from "../middleware/auth.js";
import {
  googleRateLimiter,
  loginRateLimiter,
  refreshRateLimiter,
  registerRateLimiter,
} from "../middleware/rateLimit.js";

export const authRouter = Router();

function sendSessionResponse(res: any, result: SessionResult, statusCode: number = 200) {
  setRefreshCookie(res, result.refreshToken, result.refreshMaxAgeSeconds);
  return res.status(statusCode).json({
    access_token: result.accessToken,
    token_type: "bearer",
    expires_in: result.expiresIn,
    user: {
      id: result.user.id,
      email: result.user.email,
      full_name: result.user.fullName,
      role: result.user.role,
      status: result.user.status,
    },
  });
}

function getClientInfo(req: any) {
  return {
    userAgent: (req.headers["user-agent"] as string) || null,
    ipAddress: (req.ip as string) || null,
  };
}

// POST /register
authRouter.post("/register", registerRateLimiter, async (req, res, next) => {
  try {
    const { email, password, role, remember_me } = req.body || {};

    if (!email || typeof email !== "string" || !email.includes("@")) {
      throw new AppError("Invalid email address.");
    }
    if (!password || typeof password !== "string" || password.length < 8 || password.length > 128) {
      throw new AppError("Password must be between 8 and 128 characters.");
    }
    if (role !== UserRole.INVESTOR && role !== UserRole.ARCHITECT) {
      throw new AppError("Role must be 'investor' or 'architect'.");
    }

    const { userAgent, ipAddress } = getClientInfo(req);
    const result = await registerUser({
      email,
      password,
      role,
      rememberMe: Boolean(remember_me),
      userAgent,
      ipAddress,
    });

    sendSessionResponse(res, result, 201);
  } catch (err) {
    next(err);
  }
});

// POST /login
authRouter.post("/login", loginRateLimiter, async (req, res, next) => {
  try {
    const { email, password, role, remember_me } = req.body || {};

    if (!email || typeof email !== "string") {
      throw new AppError("Email is required.");
    }
    if (!password || typeof password !== "string" || password.length < 1) {
      throw new AppError("Password is required.");
    }
    if (role && role !== UserRole.INVESTOR && role !== UserRole.ARCHITECT) {
      throw new AppError("Role must be 'investor' or 'architect'.");
    }

    const { userAgent, ipAddress } = getClientInfo(req);
    const result = await loginUser({
      email,
      password,
      expectedRole: role || null,
      rememberMe: Boolean(remember_me),
      userAgent,
      ipAddress,
    });

    sendSessionResponse(res, result, 200);
  } catch (err) {
    next(err);
  }
});

// POST /google (Unified Sign-In & Sign-Up via Google)
authRouter.post("/google", googleRateLimiter, async (req, res, next) => {
  try {
    const { credential, role, remember_me } = req.body || {};

    if (!credential || typeof credential !== "string") {
      throw new AppError("Google credential is required.");
    }

    if (role && role !== UserRole.INVESTOR && role !== UserRole.ARCHITECT) {
      throw new AppError("Role must be 'investor' or 'architect'.");
    }

    const { userAgent, ipAddress } = getClientInfo(req);
    const result = await authenticateWithGoogle({
      credential,
      expectedRole: role || null,
      rememberMe: Boolean(remember_me),
      userAgent,
      ipAddress,
    });

    setRefreshCookie(res, result.refreshToken, result.refreshMaxAgeSeconds);
    const statusCode = result.isNewUser ? 201 : 200;

    return res.status(statusCode).json({
      access_token: result.accessToken,
      token_type: "bearer",
      expires_in: result.expiresIn,
      user: {
        id: result.user.id,
        email: result.user.email,
        full_name: result.user.fullName,
        role: result.user.role,
        status: result.user.status,
      },
      is_new_user: result.isNewUser,
    });
  } catch (err) {
    next(err);
  }
});

// POST /refresh
authRouter.post("/refresh", refreshRateLimiter, verifyOrigin, async (req, res, next) => {
  try {
    const rawToken = req.cookies?.[REFRESH_COOKIE_NAME];
    const { userAgent, ipAddress } = getClientInfo(req);
    const result = await refreshSession({
      rawToken,
      userAgent,
      ipAddress,
    });

    sendSessionResponse(res, result, 200);
  } catch (err) {
    next(err);
  }
});

// POST /logout
authRouter.post("/logout", verifyOrigin, async (req, res, next) => {
  try {
    const rawToken = req.cookies?.[REFRESH_COOKIE_NAME];
    await logout({ rawToken });
    clearRefreshCookie(res);
    res.status(204).send();
  } catch (err) {
    next(err);
  }
});
