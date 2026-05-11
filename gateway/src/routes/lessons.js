import { Router } from "express";
import multer from "multer";
import axios from "axios";
import FormData from "form-data";
import { requireAuth } from "../middleware/auth.js";
import { q } from "../db.js";

const router = Router();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
const ML = process.env.ML_SERVICE_URL || "http://localhost:8000";

router.get("/", async (_req, res) => {
  try {
    const { data } = await axios.get(`${ML}/tutor/lessons`);
    res.json(data);
  } catch { res.status(502).json({ error: "ml service unreachable" }); }
});

router.post("/:lessonId/score", requireAuth, upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "file required" });
  const fd = new FormData();
  fd.append("file",      req.file.buffer, { filename: "attempt.webm" });
  fd.append("lesson_id", req.params.lessonId);
  try {
    const { data } = await axios.post(`${ML}/tutor/score`, fd, { headers: fd.getHeaders() });
    const { rows } = await q(
      `INSERT INTO lesson_progress (user_id, lesson_id, best_score, last_score, attempts)
       VALUES ($1, $2, $3, $3, 1)
       ON CONFLICT (user_id, lesson_id) DO UPDATE SET
         best_score = GREATEST(lesson_progress.best_score, EXCLUDED.last_score),
         last_score = EXCLUDED.last_score,
         attempts   = lesson_progress.attempts + 1,
         updated_at = now()
       RETURNING best_score`,
      [req.user.id, req.params.lessonId, data.score],
    );
    res.json({ ...data, best: Number(rows[0].best_score) });
  } catch (e) { console.error(e); res.status(502).json({ error: "ml service unreachable" }); }
});

router.get("/me/progress", requireAuth, async (req, res) => {
  const { rows } = await q(
    `SELECT lesson_id, best_score, attempts FROM lesson_progress WHERE user_id = $1`,
    [req.user.id],
  );
  const out = {};
  for (const r of rows) out[r.lesson_id] = Number(r.best_score);
  res.json(out);
});

export default router;
