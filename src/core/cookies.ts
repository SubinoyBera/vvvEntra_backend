import { Response } from "express";
import { config } from "../config.js";

export const REFRESH_COOKIE_NAME = "refresh_token";
export const REFRESH_COOKIE_PATH = `${config.apiV1Prefix}/auth`;

export function setRefreshCookie(res: Response, rawToken: string, maxAgeSeconds?: number | null): void {
  res.cookie(REFRESH_COOKIE_NAME, rawToken, {
    maxAge: maxAgeSeconds ? maxAgeSeconds * 1000 : undefined,
    path: REFRESH_COOKIE_PATH,
    domain: config.cookieDomain,
    secure: config.cookieSecure,
    httpOnly: true,
    sameSite: config.cookieSameSite,
  });
}

export function clearRefreshCookie(res: Response): void {
  res.clearCookie(REFRESH_COOKIE_NAME, {
    path: REFRESH_COOKIE_PATH,
    domain: config.cookieDomain,
    secure: config.cookieSecure,
    httpOnly: true,
    sameSite: config.cookieSameSite,
  });
}
