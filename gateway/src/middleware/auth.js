import jwt from "jsonwebtoken";

export function requireAuth(req, res, next) {
  const h = req.headers.authorization;
  if (!h?.startsWith("Bearer ")) return res.status(401).json({ error: "missing token" });
  try {
    const p = jwt.verify(h.slice(7), process.env.JWT_SECRET || "dev");
    req.user = { id: p.sub, email: p.email, name: p.name };
    next();
  } catch { res.status(401).json({ error: "invalid token" }); }
}
