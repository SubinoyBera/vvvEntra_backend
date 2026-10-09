import { Router } from "express";
import { requireCurrentUser } from "../middleware/auth.js";

export const usersRouter = Router();

// GET /api/v1/users/me
usersRouter.get("/me", requireCurrentUser, (req, res) => {
  const user = req.user!;
  res.json({
    id: user.id,
    email: user.email,
    full_name: user.fullName,
    role: user.role,
    status: user.status,
  });
});
