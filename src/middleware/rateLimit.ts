import { Request, Response, NextFunction } from "express";
import { createRateLimiter } from "../core/rateLimiter.js";
import { REFRESH_COOKIE_NAME } from "../core/cookies.js";
import { hashToken } from "../core/security.js";

function getClientIp(req: Request): string {
  const forwarded = req.headers["x-forwarded-for"];
  if (typeof forwarded === "string") {
    return forwarded.split(",")[0].trim();
  }
  return req.ip || req.socket.remoteAddress || "127.0.0.1";
}

function normalizeEmail(email: any): string | null {
  if (typeof email === "string" && email.includes("@")) {
    return email.trim().toLowerCase();
  }
  return null;
}

/**
 * Rate Limiter for /api/v1/auth/register
 * Protection:
 * - 5 registrations per 15 minutes per IP address
 * - 3 registration attempts per 15 minutes per target email
 */
const ipRegisterLimiter = createRateLimiter({
  prefix: "register_ip",
  limit: 5,
  windowSeconds: 900, // 15 minutes
  keyGenerator: (req) => `ip:${getClientIp(req)}`,
  message: (retryAfter) => `Too many registration attempts from this IP. Please try again in ${retryAfter} seconds.`,
});

const emailRegisterLimiter = createRateLimiter({
  prefix: "register_email",
  limit: 3,
  windowSeconds: 900, // 15 minutes
  keyGenerator: (req) => {
    const email = normalizeEmail(req.body?.email);
    return email ? `email:${email}` : `ip:${getClientIp(req)}`;
  },
  message: (retryAfter) => `Too many registration attempts for this email address. Please try again in ${retryAfter} seconds.`,
});

export async function registerRateLimiter(req: Request, res: Response, next: NextFunction): Promise<void> {
  ipRegisterLimiter(req, res, (err) => {
    if (err) return next(err);
    emailRegisterLimiter(req, res, next);
  });
}

/**
 * Rate Limiter for /api/v1/auth/login
 * Protection:
 * - 10 login attempts per 5 minutes per IP address
 * - 5 login attempts per 5 minutes per target account email (brute-force defense)
 */
const ipLoginLimiter = createRateLimiter({
  prefix: "login_ip",
  limit: 10,
  windowSeconds: 300, // 5 minutes
  keyGenerator: (req) => `ip:${getClientIp(req)}`,
  message: (retryAfter) => `Too many login attempts from this network. Please try again in ${retryAfter} seconds.`,
});

const emailLoginLimiter = createRateLimiter({
  prefix: "login_email",
  limit: 5,
  windowSeconds: 300, // 5 minutes
  keyGenerator: (req) => {
    const email = normalizeEmail(req.body?.email);
    return email ? `email:${email}` : `ip:${getClientIp(req)}`;
  },
  message: (retryAfter) => `Too many failed login attempts for this account. Please wait ${retryAfter} seconds before trying again.`,
});

export async function loginRateLimiter(req: Request, res: Response, next: NextFunction): Promise<void> {
  ipLoginLimiter(req, res, (err) => {
    if (err) return next(err);
    emailLoginLimiter(req, res, next);
  });
}

/**
 * Rate Limiter for /api/v1/auth/refresh
 * Protection:
 * - 30 token rotations per 60 seconds per IP
 * - 15 token rotations per 60 seconds per active session token
 */
const ipRefreshLimiter = createRateLimiter({
  prefix: "refresh_ip",
  limit: 30,
  windowSeconds: 60, // 1 minute
  keyGenerator: (req) => `ip:${getClientIp(req)}`,
  message: (retryAfter) => `Too many token refresh requests. Please wait ${retryAfter} seconds.`,
});

const tokenRefreshLimiter = createRateLimiter({
  prefix: "refresh_token",
  limit: 15,
  windowSeconds: 60, // 1 minute
  keyGenerator: (req) => {
    const rawToken = req.cookies?.[REFRESH_COOKIE_NAME];
    return rawToken ? `token:${hashToken(rawToken)}` : `ip:${getClientIp(req)}`;
  },
  message: (retryAfter) => `Session refresh rate limit exceeded. Please wait ${retryAfter} seconds.`,
});

export async function refreshRateLimiter(req: Request, res: Response, next: NextFunction): Promise<void> {
  ipRefreshLimiter(req, res, (err) => {
    if (err) return next(err);
    tokenRefreshLimiter(req, res, next);
  });
}

/**
 * Rate Limiter for /api/v1/auth/google
 * Protection:
 * - 20 Google auth requests per 5 minutes per IP
 */
export const googleRateLimiter = createRateLimiter({
  prefix: "google_auth_ip",
  limit: 20,
  windowSeconds: 300, // 5 minutes
  keyGenerator: (req) => `ip:${getClientIp(req)}`,
  message: (retryAfter) => `Too many Google sign-in attempts from this network. Please wait ${retryAfter} seconds.`,
});

