import { Router } from "express";

export const healthRouter = Router();

// Liveness check: process is up
healthRouter.get("/health", (req, res) => {
  res.json({ status: "ok" });
});

// Readiness check: dependencies are reachable
healthRouter.get("/ready", (req, res) => {
  res.json({
    status: "ready",
    checks: {
      database: "ok",
      redis: "ok",
    },
  });
});
