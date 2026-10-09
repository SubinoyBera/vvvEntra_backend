import express from "express";
import cors from "cors";
import cookieParser from "cookie-parser";
import { config } from "./config.js";
import { requestContextMiddleware, errorHandler } from "./middleware/requestContext.js";
import { healthRouter } from "./routes/health.js";
import { authRouter } from "./routes/auth.js";
import { usersRouter } from "./routes/users.js";
import { profileRouter } from "./routes/profile.js";
import { openApiSpec } from "./docs/openapi.js";

export const app = express();

// Middlewares
app.use(cors({
  origin: (origin, callback) => {
    // Allow requests with no origin (like mobile apps, curl, or server-to-server)
    if (!origin) return callback(null, true);
    return callback(null, true); // Allow all origins for dev/API testing
  },
  credentials: true,
  methods: ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
  allowedHeaders: ["Authorization", "Content-Type", "X-Request-ID"],
  exposedHeaders: ["X-Request-ID"],
}));

app.use(cookieParser());
app.use(express.json());
app.use(requestContextMiddleware);

// Unversioned infra health checks
app.use("/", healthRouter);

// API v1 routes
const v1Router = express.Router();
v1Router.use("/auth", authRouter);
v1Router.use("/users", usersRouter);
v1Router.use("/profile", profileRouter);

app.use(config.apiV1Prefix, v1Router);

// OpenAPI specification endpoint
app.get("/openapi.json", (req, res) => {
  res.json(openApiSpec);
});

// Swagger UI Documentation & Test Interface
const swaggerHtml = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>vvvEntra API Server Documentation</title>
  <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.18.2/swagger-ui.css" />
  <style>
    body {
      margin: 0;
      padding: 0;
      font-family: system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
      background: #f8fafc;
    }
    .topbar { display: none !important; }
    .banner {
      background: #0f172a;
      color: #fff;
      padding: 16px 24px;
      display: flex;
      align-items: center;
      justify-content: space-between;
      border-bottom: 2px solid #38bdf8;
    }
    .banner h1 {
      margin: 0;
      font-size: 1.25rem;
      font-weight: 600;
      display: flex;
      align-items: center;
      gap: 10px;
    }
    .banner .badge {
      background: #0284c7;
      font-size: 0.75rem;
      padding: 2px 8px;
      border-radius: 9999px;
      text-transform: uppercase;
      font-weight: 700;
    }
    .banner a {
      color: #94a3b8;
      text-decoration: none;
      font-size: 0.875rem;
    }
    .banner a:hover {
      color: #38bdf8;
    }
    #swagger-ui {
      max-width: 1200px;
      margin: 0 auto;
      padding: 20px;
    }
  </style>
</head>
<body>
  <div class="banner">
    <h1>vvvEntra backend API <span class="badge">v0.1.0</span></h1>
    <a href="/openapi.json" target="_blank">View Raw openapi.json</a>
  </div>
  <div id="swagger-ui">
    <div style="padding: 2rem; text-align: center; color: #64748b;">
      Loading API Documentation...
    </div>
  </div>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.18.2/swagger-ui-bundle.js"></script>
  <script src="https://cdn.jsdelivr.net/npm/swagger-ui-dist@5.18.2/swagger-ui-standalone-preset.js"></script>
  <script>
    window.onload = function() {
      SwaggerUIBundle({
        url: "/openapi.json",
        dom_id: "#swagger-ui",
        deepLinking: true,
        presets: [
          SwaggerUIBundle.presets.apis,
          SwaggerUIStandalonePreset
        ],
        layout: "BaseLayout"
      });
    };
  </script>
</body>
</html>`;

app.get(["/", "/docs"], (req, res) => {
  res.type("html").send(swaggerHtml);
});

// Global error handler
app.use(errorHandler);

// Start server
const port = config.port;
const host = config.host;

if (process.env.NODE_ENV !== "test") {
  app.listen(port, host, () => {
    console.log(`[vvvEntra API] Server listening on http://${host}:${port}`);
    console.log(`[vvvEntra API] Swagger UI available at http://${host}:${port}/docs`);
  });
}
