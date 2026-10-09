import { Request, Response, NextFunction } from "express";
import { TooManyRequests } from "./exceptions.js";

export interface RateLimitResult {
  allowed: boolean;
  limit: number;
  remaining: number;
  resetTimeMs: number;
  retryAfterSeconds: number;
}

export interface RateLimitStore {
  consume(key: string, limit: number, windowSeconds: number): Promise<RateLimitResult>;
  reset(key: string): Promise<void>;
}

/**
 * Sliding Window In-Memory Rate Limiter Store.
 * Highly optimized, maintains rolling timestamps, automatically prunes stale keys.
 */
export class SlidingWindowMemoryStore implements RateLimitStore {
  private hits = new Map<string, number[]>();
  private cleanupInterval: NodeJS.Timeout | null = null;

  constructor() {
    // Run garbage collection every 60 seconds to prune expired buckets
    this.cleanupInterval = setInterval(() => this.prune(), 60_000);
    if (this.cleanupInterval.unref) {
      this.cleanupInterval.unref();
    }
  }

  public async consume(key: string, limit: number, windowSeconds: number): Promise<RateLimitResult> {
    const now = Date.now();
    const windowMs = windowSeconds * 1000;
    const windowStart = now - windowMs;

    let timestamps = this.hits.get(key) || [];
    // Filter timestamps within current rolling window
    timestamps = timestamps.filter((t) => t > windowStart);

    const resetTimeMs = timestamps.length > 0 ? timestamps[0] + windowMs : now + windowMs;
    const retryAfterSeconds = Math.max(1, Math.ceil((resetTimeMs - now) / 1000));

    if (timestamps.length >= limit) {
      this.hits.set(key, timestamps);
      return {
        allowed: false,
        limit,
        remaining: 0,
        resetTimeMs,
        retryAfterSeconds,
      };
    }

    timestamps.push(now);
    this.hits.set(key, timestamps);

    return {
      allowed: true,
      limit,
      remaining: Math.max(0, limit - timestamps.length),
      resetTimeMs,
      retryAfterSeconds: 0,
    };
  }

  public async reset(key: string): Promise<void> {
    this.hits.delete(key);
  }

  private prune(): void {
    const now = Date.now();
    // Prune entries older than 1 hour
    const maxRetention = 3600 * 1000;
    for (const [key, timestamps] of this.hits.entries()) {
      const active = timestamps.filter((t) => now - t < maxRetention);
      if (active.length === 0) {
        this.hits.delete(key);
      } else {
        this.hits.set(key, active);
      }
    }
  }

  public destroy(): void {
    if (this.cleanupInterval) {
      clearInterval(this.cleanupInterval);
      this.cleanupInterval = null;
    }
    this.hits.clear();
  }
}

// Global default store instance (Redis-compatible sliding-window abstraction)
export const defaultRateLimitStore = new SlidingWindowMemoryStore();

export interface RateLimitOptions {
  limit: number;
  windowSeconds: number;
  prefix: string;
  keyGenerator?: (req: Request) => string | string[];
  message?: string | ((retryAfter: number) => string);
  store?: RateLimitStore;
}

/**
 * Creates an Express middleware for rate limiting.
 */
export function createRateLimiter(options: RateLimitOptions) {
  const store = options.store || defaultRateLimitStore;

  return async (req: Request, res: Response, next: NextFunction): Promise<void> => {
    try {
      // Determine keys to check (e.g. by IP and/or by email)
      let rawKeys: string[] = [];

      if (options.keyGenerator) {
        const generated = options.keyGenerator(req);
        rawKeys = Array.isArray(generated) ? generated : [generated];
      } else {
        const clientIp = req.ip || (req.headers["x-forwarded-for"] as string) || req.socket.remoteAddress || "unknown";
        rawKeys = [`ip:${clientIp}`];
      }

      // Check all keys against rate limiter
      let strictestResult: RateLimitResult | null = null;

      for (const keyId of rawKeys) {
        if (!keyId) continue;
        const fullKey = `rl:${options.prefix}:${keyId}`;
        const result = await store.consume(fullKey, options.limit, options.windowSeconds);

        if (!strictestResult || (!result.allowed && strictestResult.allowed) || result.remaining < strictestResult.remaining) {
          strictestResult = result;
        }

        if (!result.allowed) {
          break; // Stop early if any key exceeded
        }
      }

      if (strictestResult) {
        // Set standard rate limit headers
        res.setHeader("X-RateLimit-Limit", String(options.limit));
        res.setHeader("X-RateLimit-Remaining", String(strictestResult.remaining));
        res.setHeader("X-RateLimit-Reset", String(Math.ceil(strictestResult.resetTimeMs / 1000)));

        if (!strictestResult.allowed) {
          const retryAfter = strictestResult.retryAfterSeconds;
          res.setHeader("Retry-After", String(retryAfter));

          const errorMessage = typeof options.message === "function"
            ? options.message(retryAfter)
            : options.message || `Too many requests. Please try again in ${retryAfter} seconds.`;

          return next(new TooManyRequests(errorMessage, retryAfter));
        }
      }

      next();
    } catch (err) {
      // Fail open or pass to next handler
      console.error("[RateLimiter Error]", err);
      next();
    }
  };
}
