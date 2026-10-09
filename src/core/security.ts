import crypto from "crypto";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { config } from "../config.js";

export async function hashPassword(password: string): Promise<string> {
  return bcrypt.hash(password, 10);
}

export async function verifyPassword(password: string, hash: string): Promise<boolean> {
  try {
    return await bcrypt.compare(password, hash);
  } catch {
    return false;
  }
}

export function createAccessToken(userId: string, role: string): { accessToken: string; expiresIn: number } {
  const expiresInSeconds = config.accessTokenMinutes * 60;
  const payload = {
    sub: userId,
    role,
    typ: "access",
  };

  const accessToken = jwt.sign(payload, config.jwtSecret, {
    algorithm: config.jwtAlgorithm,
    expiresIn: expiresInSeconds,
  });

  return {
    accessToken,
    expiresIn: expiresInSeconds,
  };
}

export function decodeAccessToken(token: string): { sub: string; role: string; typ: string } {
  const payload = jwt.verify(token, config.jwtSecret, {
    algorithms: [config.jwtAlgorithm],
  }) as { sub: string; role: string; typ: string };

  if (payload.typ !== "access") {
    throw new Error("not an access token");
  }

  return payload;
}

export function hashToken(rawToken: string): string {
  return crypto.createHash("sha256").update(rawToken).digest("hex");
}

export function generateRefreshToken(): { raw: string; hash: string } {
  const raw = crypto.randomBytes(36).toString("base64url");
  return {
    raw,
    hash: hashToken(raw),
  };
}
