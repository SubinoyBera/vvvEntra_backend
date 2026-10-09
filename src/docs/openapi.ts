export const openApiSpec = {
  openapi: "3.0.3",
  info: {
    title: "vvvEntra backend API server",
    description: "Backend API for vvvEntra: authentication, session rotation, user management, and investor profile onboarding.",
    version: "0.1.0",
  },
  servers: [
    {
      url: "/",
      description: "Default server",
    },
  ],
  components: {
    securitySchemes: {
      OAuth2PasswordBearer: {
        type: "http",
        scheme: "bearer",
        bearerFormat: "JWT",
      },
    },
    schemas: {
      UserRole: {
        type: "string",
        enum: ["investor", "architect", "admin"],
      },
      UserStatus: {
        type: "string",
        enum: ["onboarding", "pending_review", "active", "suspended"],
      },
      UserOut: {
        type: "object",
        required: ["id", "email", "role", "status"],
        properties: {
          id: { type: "string", format: "uuid" },
          email: { type: "string", format: "email" },
          full_name: { type: "string", nullable: true },
          role: { $ref: "#/components/schemas/UserRole" },
          status: { $ref: "#/components/schemas/UserStatus" },
        },
      },
      ErrorResponse: {
        type: "object",
        required: ["error", "request_id"],
        properties: {
          error: {
            type: "object",
            required: ["code", "message"],
            properties: {
              code: { type: "string", example: "TOO_MANY_REQUESTS" },
              message: { type: "string", example: "Too many requests. Please try again in 45 seconds." },
            },
          },
          request_id: { type: "string", format: "uuid" },
        },
      },
      RegisterRequest: {
        type: "object",
        required: ["email", "password", "role"],
        properties: {
          email: { type: "string", format: "email" },
          password: { type: "string", minLength: 8, maxLength: 128 },
          role: { type: "string", enum: ["investor", "architect"] },
          remember_me: { type: "boolean", default: false },
        },
      },
      LoginRequest: {
        type: "object",
        required: ["email", "password"],
        properties: {
          email: { type: "string", format: "email" },
          password: { type: "string", minLength: 1, maxLength: 128 },
          role: { type: "string", enum: ["investor", "architect"], nullable: true },
          remember_me: { type: "boolean", default: false },
        },
      },
      AuthResponse: {
        type: "object",
        required: ["access_token", "token_type", "expires_in", "user"],
        properties: {
          access_token: { type: "string" },
          token_type: { type: "string", example: "bearer" },
          expires_in: { type: "integer", example: 900 },
          user: { $ref: "#/components/schemas/UserOut" },
        },
      },
      GoogleAuthRequest: {
        type: "object",
        required: ["credential"],
        properties: {
          credential: {
            type: "string",
            description: "Google ID Token (credential) returned by Google Identity Services",
          },
          role: {
            type: "string",
            enum: ["investor", "architect"],
            description: "Account role if creating a new user (defaults to investor)",
            nullable: true,
          },
          remember_me: {
            type: "boolean",
            description: "Whether to maintain a 30-day persistent session",
            default: false,
          },
        },
      },
      GoogleAuthResponse: {
        type: "object",
        required: ["access_token", "token_type", "expires_in", "user", "is_new_user"],
        properties: {
          access_token: { type: "string" },
          token_type: { type: "string", example: "bearer" },
          expires_in: { type: "integer", example: 900 },
          user: { $ref: "#/components/schemas/UserOut" },
          is_new_user: {
            type: "boolean",
            description: "True if account was newly created, false if existing user logged in",
          },
        },
      },
      InvestorProfileIn: {
        type: "object",
        required: [
          "full_name",
          "focus",
          "location",
          "sectors",
          "looking_for",
          "capital_range",
          "deployment_timeline",
        ],
        properties: {
          full_name: { type: "string", minLength: 2, maxLength: 200 },
          focus: { type: "string", minLength: 1, maxLength: 120 },
          location: { type: "string", minLength: 1, maxLength: 120 },
          sectors: {
            type: "array",
            items: {
              type: "string",
              enum: [
                "b2b_saas",
                "ai_automation",
                "marketplaces",
                "fintech",
                "climate_industry",
                "d2c_consumer",
                "operations",
                "healthtech",
              ],
            },
          },
          additional_notes: { type: "string", maxLength: 1000, nullable: true },
          looking_for: { type: "string", minLength: 1, maxLength: 2000 },
          capital_range: {
            type: "string",
            enum: ["under_10k", "10k_50k", "50k_250k", "250k_1m", "over_1m", "exploring"],
          },
          deployment_timeline: {
            type: "string",
            enum: ["now", "within_3_months", "within_12_months", "exploring"],
          },
        },
      },
      ArchitectDocDepth: {
        type: "string",
        enum: ["90_120_pages", "120_150_pages", "150_plus_pages", "still_planning"],
        description: "Expected documentation depth for the opportunity",
      },
      ArchitectSubmissionTimeline: {
        type: "string",
        enum: ["within_30_days", "within_3_months", "later_this_year", "exploring"],
        description: "When the architect expects to submit the opportunity",
      },
      ArchitectProfileIn: {
        type: "object",
        required: [
          "full_name",
          "headline",
          "location",
          "sectors",
          "opportunity_description",
          "doc_depth",
          "submission_timeline",
        ],
        properties: {
          full_name: { type: "string", minLength: 2, maxLength: 200, example: "Elena Rostova" },
          headline: { type: "string", minLength: 1, maxLength: 120, example: "Former COO, B2B operator" },
          location: { type: "string", minLength: 1, maxLength: 120, example: "San Francisco, USA" },
          sectors: {
            type: "array",
            items: {
              type: "string",
              enum: [
                "b2b_saas",
                "ai_automation",
                "marketplaces",
                "fintech",
                "climate_industry",
                "d2c_consumer",
                "operations",
                "healthtech",
              ],
            },
            example: ["b2b_saas", "ai_automation"],
          },
          additional_notes: {
            type: "string",
            maxLength: 1000,
            nullable: true,
            example: "Enterprise GTM, compliance, marketplace operations",
          },
          opportunity_description: {
            type: "string",
            minLength: 1,
            maxLength: 2000,
            example: "Autonomous compliance verification system for regulated B2B Fintech SaaS.",
          },
          doc_depth: { $ref: "#/components/schemas/ArchitectDocDepth" },
          submission_timeline: { $ref: "#/components/schemas/ArchitectSubmissionTimeline" },
        },
      },
    },
  },
  paths: {
    "/health": {
      get: {
        summary: "Liveness check",
        responses: {
          "200": {
            description: "Process is up",
            content: { "application/json": { schema: { type: "object", properties: { status: { type: "string" } } } } },
          },
        },
      },
    },
    "/ready": {
      get: {
        summary: "Readiness check",
        responses: {
          "200": {
            description: "Dependencies reachable",
            content: { "application/json": { schema: { type: "object" } } },
          },
        },
      },
    },
    "/api/v1/auth/register": {
      post: {
        summary: "Register new user account (Rate limited: 5 req/15min per IP, 3 req/15min per email)",
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/RegisterRequest" } } },
        },
        responses: {
          "201": {
            description: "Account created and logged in",
            content: { "application/json": { schema: { $ref: "#/components/schemas/AuthResponse" } } },
          },
          "429": {
            description: "Rate limit exceeded",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
        },
      },
    },
    "/api/v1/auth/login": {
      post: {
        summary: "Login with email and password (Rate limited: 10 req/5min per IP, 5 req/5min per email)",
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/LoginRequest" } } },
        },
        responses: {
          "200": {
            description: "Login successful",
            content: { "application/json": { schema: { $ref: "#/components/schemas/AuthResponse" } } },
          },
          "429": {
            description: "Rate limit exceeded (credential stuffing / brute force defense)",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
        },
      },
    },
    "/api/v1/auth/google": {
      post: {
        summary: "Continue with Google (Unified Login & Sign-Up)",
        description: "Accepts Google ID token from frontend Google Identity Services. If user exists, signs them in. If new user, creates their account with role (investor or architect).",
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/GoogleAuthRequest" } } },
        },
        responses: {
          "200": {
            description: "Existing user logged in",
            content: { "application/json": { schema: { $ref: "#/components/schemas/GoogleAuthResponse" } } },
          },
          "201": {
            description: "New user registered and logged in",
            content: { "application/json": { schema: { $ref: "#/components/schemas/GoogleAuthResponse" } } },
          },
          "400": {
            description: "Invalid or expired Google credential",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
          "403": {
            description: "Account suspended or role mismatch",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
          "429": {
            description: "Rate limit exceeded",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
        },
      },
    },
    "/api/v1/auth/refresh": {
      post: {
        summary: "Rotate refresh token from HTTP-only cookie (Rate limited: 30 req/min per IP)",
        responses: {
          "200": {
            description: "Refreshed access token",
            content: { "application/json": { schema: { $ref: "#/components/schemas/AuthResponse" } } },
          },
          "429": {
            description: "Rate limit exceeded",
            content: { "application/json": { schema: { $ref: "#/components/schemas/ErrorResponse" } } },
          },
        },
      },
    },
    "/api/v1/auth/logout": {
      post: {
        summary: "Log out current session",
        responses: {
          "204": {
            description: "Logged out",
          },
        },
      },
    },
    "/api/v1/users/me": {
      get: {
        summary: "Get current authenticated user info",
        security: [{ OAuth2PasswordBearer: [] }],
        responses: {
          "200": {
            description: "Current user details",
            content: { "application/json": { schema: { $ref: "#/components/schemas/UserOut" } } },
          },
        },
      },
    },
    "/api/v1/profile/investor": {
      get: {
        summary: "Get current investor profile",
        security: [{ OAuth2PasswordBearer: [] }],
        responses: {
          "200": {
            description: "Current investor profile",
            content: { "application/json": { schema: { type: "object" } } },
          },
          "404": { description: "Profile not found" },
        },
      },
      put: {
        summary: "Submit investor onboarding profile",
        description: "Completes the 3-step investor onboarding wizard and transitions user status to pending_review.",
        security: [{ OAuth2PasswordBearer: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/InvestorProfileIn" } } },
        },
        responses: {
          "200": {
            description: "Profile submitted, moved to pending_review",
            content: { "application/json": { schema: { type: "object" } } },
          },
        },
      },
    },
    "/api/v1/profile/architect": {
      get: {
        summary: "Get current architect profile",
        security: [{ OAuth2PasswordBearer: [] }],
        responses: {
          "200": {
            description: "Current architect profile",
            content: { "application/json": { schema: { type: "object" } } },
          },
          "404": { description: "Profile not found" },
        },
      },
      put: {
        summary: "Submit architect onboarding profile",
        description: "Completes the 3-step architect wizard (About you, Your strengths, Your opportunity) and transitions user status to pending_review.",
        security: [{ OAuth2PasswordBearer: [] }],
        requestBody: {
          required: true,
          content: { "application/json": { schema: { $ref: "#/components/schemas/ArchitectProfileIn" } } },
        },
        responses: {
          "200": {
            description: "Profile submitted, moved to pending_review",
            content: { "application/json": { schema: { type: "object" } } },
          },
        },
      },
    },
  },
};
