import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";
import { config } from "../config.js";
import { decodeAccessToken } from "../core/security.js";
import { store } from "../db/store.js";
import {
  AccountPendingReview,
  AccountSuspended,
  ForbiddenOrigin,
  NotAuthenticated,
  OnboardingIncomplete,
  TokenExpired,
  TokenInvalid,
} from "../core/exceptions.js";
import { User, UserStatus } from "../types/index.js";

declare global {
  namespace Express {
    interface Request {
      user?: User;
    }
  }
}

export async function requireCurrentUser(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const authHeader = req.headers.authorization;
  if (!authHeader || !authHeader.startsWith("Bearer ")) {
    return next(new NotAuthenticated());
  }

  const token = authHeader.slice(7).trim();
  let payload: { sub: string; role: string; typ: string };

  try {
    payload = decodeAccessToken(token);
  } catch (err: any) {
    if (err instanceof jwt.TokenExpiredError) {
      return next(new TokenExpired());
    }
    return next(new TokenInvalid());
  }

  const user = store.users.get(payload.sub);
  if (!user) {
    return next(new TokenInvalid());
  }

  if (user.status === UserStatus.SUSPENDED) {
    return next(new AccountSuspended());
  }

  req.user = user;
  next();
}

export async function requireActiveUser(
  req: Request,
  res: Response,
  next: NextFunction
): Promise<void> {
  const user = req.user;
  if (!user) {
    return next(new NotAuthenticated());
  }

  if (user.status === UserStatus.ONBOARDING) {
    return next(new OnboardingIncomplete());
  }

  if (user.status === UserStatus.PENDING_REVIEW) {
    return next(new AccountPendingReview());
  }

  next();
}

export function verifyOrigin(req: Request, res: Response, next: NextFunction): void {
  const origin = req.headers["origin"] as string | undefined;
  if (!origin) {
    return next();
  }

  const host = req.headers["host"] || "";
  const ownOriginHttp = `http://${host}`;
  const ownOriginHttps = `https://${host}`;

  if (origin !== ownOriginHttp && origin !== ownOriginHttps && !config.corsOrigins.includes(origin)) {
    return next(new ForbiddenOrigin());
  }

  next();
}
