import crypto from "crypto";
import { Request, Response, NextFunction } from "express";
import { AppError } from "../core/exceptions.js";
import { clearRefreshCookie } from "../core/cookies.js";

declare global {
  namespace Express {
    interface Request {
      requestId?: string;
    }
  }
}

export function requestContextMiddleware(req: Request, res: Response, next: NextFunction): void {
  const requestId = (req.header("x-request-id") as string) || crypto.randomUUID();
  req.requestId = requestId;
  res.setHeader("X-Request-ID", requestId);
  next();
}

export function errorHandler(
  err: any,
  req: Request,
  res: Response,
  next: NextFunction
): void {
  const requestId = req.requestId || crypto.randomUUID();

  if (err instanceof AppError) {
    if (err.clearRefreshCookie) {
      clearRefreshCookie(res);
    }
    if (err.statusCode === 401) {
      res.setHeader("WWW-Authenticate", "Bearer");
    }
    if (err.statusCode === 429 && "retryAfterSeconds" in err) {
      res.setHeader("Retry-After", String(err.retryAfterSeconds));
    }

    res.status(err.statusCode).json({
      error: {
        code: err.code,
        message: err.message,
      },
      request_id: requestId,
    });
    return;
  }

  // Fallback for unhandled errors
  console.error("[Unhandled Error]", err);
  res.status(500).json({
    detail: "Internal server error",
    request_id: requestId,
  });
}
