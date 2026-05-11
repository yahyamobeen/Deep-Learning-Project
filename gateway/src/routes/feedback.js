import { Router } from "express";
import jwt from "jsonwebtoken";
import { q } from "../db.js";

const router = Router();

router.post("/", async (req, res) => {
  const { name, email, category, message } = req.body || {};
  if (!message || message.trim().length < 5)
    return res.status(400).json({ error: "message must be at least 5 characters" });

  // Optional auth — if a token is present, link the feedback to that user
  let userId = null;
  const h = req.headers.authorization;
  if (h?.startsWith("Bearer ")) {
    try { userId = jwt.verify(h.slice(7), process.env.JWT_SECRET || "dev").sub; } catch {}
  }

  const { rows } = await q(
    `INSERT INTO feedback (user_id, name, email, category, message)
     VALUES ($1,$2,$3,$4,$5) RETURNING id`,
    [userId, name || "anonymous", email || null, category || "general", message.trim()],
  );
  res.json({ ok: true, id: rows[0].id });
});

export default router;
