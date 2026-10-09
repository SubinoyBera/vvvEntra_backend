export class AppError extends Error {
  public statusCode: number = 400;
  public code: string = "BAD_REQUEST";
  public clearRefreshCookie: boolean = false;

  constructor(message: string = "Bad request.") {
    super(message);
    this.name = this.constructor.name;
  }
}

export class EmailAlreadyRegistered extends AppError {
  public override statusCode = 409;
  public override code = "EMAIL_ALREADY_REGISTERED";
  constructor(message: string = "An account with this email already exists.") {
    super(message);
  }
}

export class InvalidCredentials extends AppError {
  public override statusCode = 401;
  public override code = "INVALID_CREDENTIALS";
  constructor(message: string = "Invalid email or password.") {
    super(message);
  }
}

export class NotAuthenticated extends AppError {
  public override statusCode = 401;
  public override code = "NOT_AUTHENTICATED";
  constructor(message: string = "Authentication required.") {
    super(message);
  }
}

export class TokenInvalid extends NotAuthenticated {
  public override code = "TOKEN_INVALID";
  constructor(message: string = "Invalid access token.") {
    super(message);
  }
}

export class TokenExpired extends NotAuthenticated {
  public override code = "TOKEN_EXPIRED";
  constructor(message: string = "Access token expired.") {
    super(message);
  }
}

export class RefreshTokenInvalid extends NotAuthenticated {
  public override code = "REFRESH_TOKEN_INVALID";
  public override clearRefreshCookie = true;
  constructor(message: string = "Your session has ended. Please sign in again.") {
    super(message);
  }
}

export class RefreshConflict extends AppError {
  public override statusCode = 409;
  public override code = "REFRESH_CONFLICT";
  constructor(message: string = "This session was just refreshed by another request. Retry once.") {
    super(message);
  }
}

export class AccountSuspended extends AppError {
  public override statusCode = 403;
  public override code = "ACCOUNT_SUSPENDED";
  constructor(message: string = "This account has been suspended.") {
    super(message);
  }
}

export class AccountPendingReview extends AppError {
  public override statusCode = 403;
  public override code = "ACCOUNT_PENDING_REVIEW";
  constructor(message: string = "Your account is being reviewed. You will get access once it is approved.") {
    super(message);
  }
}

export class OnboardingIncomplete extends AppError {
  public override statusCode = 403;
  public override code = "ONBOARDING_INCOMPLETE";
  constructor(message: string = "Please finish setting up your profile first.") {
    super(message);
  }
}

export class WrongRole extends AppError {
  public override statusCode = 403;
  public override code = "WRONG_ROLE";
  constructor(message: string = "This action is not available for your account type.") {
    super(message);
  }
}

export class ProfileLocked extends AppError {
  public override statusCode = 409;
  public override code = "PROFILE_LOCKED";
  constructor(message: string = "The profile can no longer be edited here.") {
    super(message);
  }
}

export class ForbiddenOrigin extends AppError {
  public override statusCode = 403;
  public override code = "FORBIDDEN_ORIGIN";
  constructor(message: string = "Request origin is not allowed.") {
    super(message);
  }
}

export class TooManyRequests extends AppError {
  public override statusCode = 429;
  public override code = "TOO_MANY_REQUESTS";
  public retryAfterSeconds: number;

  constructor(message?: string, retryAfterSeconds: number = 60) {
    super(message || `Too many requests. Please try again in ${retryAfterSeconds} seconds.`);
    this.retryAfterSeconds = retryAfterSeconds;
  }
}
