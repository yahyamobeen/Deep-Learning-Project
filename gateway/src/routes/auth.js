import { Router } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { q } from "../db.js";

const router = Router();

router.post("/register", async (req, res) => {
  const { email, password, name } = req.body;
  if (!email || !password) return res.status(400).json({ error: "email + password required" });
  try {
    const hash = await bcrypt.hash(password, 10);
    const { rows } = await q(
      `INSERT INTO users (email, name, password_hash) VALUES ($1,$2,$3) RETURNING id, email, name`,
      [email.toLowerCase(), name || email, hash],
    );
    res.json({ ok: true, user: rows[0] });
  } catch (e) {
    if (e.code === "23505") return res.status(409).json({ error: "user already exists" });
    console.error(e); res.status(500).json({ error: "registration failed" });
  }
});

router.post("/login", async (req, res) => {
  const { email, password } = req.body;
  const { rows } = await q(
    `SELECT id, email, name, password_hash FROM users WHERE lower(email) = lower($1)`,
    [email],
  );
  const u = rows[0];
  if (!u || !(await bcrypt.compare(password, u.password_hash)))
    return res.status(401).json({ error: "invalid credentials" });
  const token = jwt.sign(
    { sub: u.id, email: u.email, name: u.name },
    process.env.JWT_SECRET || "dev",
    { expiresIn: process.env.JWT_EXPIRES_IN || "7d" },
  );
  res.json({ token, user: { id: u.id, email: u.email, name: u.name } });
});

export default router;
