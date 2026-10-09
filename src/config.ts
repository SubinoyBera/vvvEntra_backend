import dotenv from "dotenv";

dotenv.config();

export const config = {
  appName: "vventra-api",
  environment: (process.env.NODE_ENV || "local") as "local" | "staging" | "production",
  port: parseInt(process.env.PORT || "3000", 10),
  host: "0.0.0.0",
  apiV1Prefix: "/api/v1",

  // Auth config
  jwtSecret: process.env.JWT_SECRET || "default-secret-jwt-key-minimum-32-chars-long",
  jwtAlgorithm: "HS256" as const,
  googleClientId: process.env.GOOGLE_CLIENT_ID || "",
  accessTokenMinutes: 15,
  refreshTokenDays: 7,
  refreshTokenRememberDays: 30,

  // Cookie config
  cookieSameSite: (process.env.COOKIE_SAMESITE || "lax") as "lax" | "strict" | "none",
  cookieDomain: process.env.COOKIE_DOMAIN || undefined,
  cookieSecure: process.env.NODE_ENV === "production",
  corsOrigins: process.env.CORS_ORIGINS ? process.env.CORS_ORIGINS.split(",") : ["http://localhost:3000"],
};
