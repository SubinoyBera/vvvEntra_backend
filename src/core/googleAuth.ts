import { config } from "../config.js";
import { AppError } from "./exceptions.js";

export interface GooglePayload {
  googleSub: string;
  email: string;
  name: string | null;
  picture: string | null;
  emailVerified: boolean;
}

/**
 * Verifies a Google ID Token securely using Google's free public verification endpoint.
 * Validates cryptographic signature, expiration, issuer, and client ID.
 */
export async function verifyGoogleIdToken(idToken: string): Promise<GooglePayload> {
  if (!idToken || typeof idToken !== "string" || idToken.trim().length === 0) {
    throw new AppError("Google credential token is required.");
  }

  const token = idToken.trim();

  // Test / development fallback helper: allows mock-token-{email} in non-production
  if (config.environment !== "production" && token.startsWith("mock-google-token:")) {
    const parts = token.split(":");
    const mockEmail = (parts[1] || "test@gmail.com").toLowerCase();
    const mockSub = parts[2] || "mock-google-sub-12345";
    const mockName = parts[3] || "Google Test User";
    return {
      googleSub: mockSub,
      email: mockEmail,
      name: mockName,
      picture: "https://lh3.googleusercontent.com/a/default-user",
      emailVerified: true,
    };
  }

  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000); // 6s timeout

    const url = `https://oauth2.googleapis.com/tokeninfo?id_token=${encodeURIComponent(token)}`;
    const response = await fetch(url, {
      method: "GET",
      signal: controller.signal,
      headers: {
        Accept: "application/json",
      },
    });

    clearTimeout(timeoutId);

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new AppError(
        errorData.error_description || errorData.error || "Invalid or expired Google ID token."
      );
    }

    const payload = (await response.json()) as Record<string, any>;

    // 1. Verify Issuer
    const validIssuers = ["accounts.google.com", "https://accounts.google.com"];
    if (!validIssuers.includes(payload.iss)) {
      throw new AppError("Invalid Google token issuer.");
    }

    // 2. Verify Audience (if GOOGLE_CLIENT_ID is configured)
    if (config.googleClientId && payload.aud !== config.googleClientId) {
      throw new AppError("Google token audience does not match this application.");
    }

    // 3. Verify Sub and Email exist
    if (!payload.sub || !payload.email) {
      throw new AppError("Google token is missing essential profile claims.");
    }

    const emailVerified = payload.email_verified === "true" || payload.email_verified === true;
    if (!emailVerified) {
      throw new AppError("Google account email must be verified.");
    }

    return {
      googleSub: String(payload.sub),
      email: String(payload.email).trim().toLowerCase(),
      name: payload.name ? String(payload.name).trim() : null,
      picture: payload.picture ? String(payload.picture) : null,
      emailVerified: true,
    };
  } catch (err: any) {
    if (err instanceof AppError) {
      throw err;
    }
    if (err.name === "AbortError") {
      throw new AppError("Google authentication verification timed out. Please try again.");
    }
    throw new AppError(`Google authentication failed: ${err.message || "Unknown error"}`);
  }
}
