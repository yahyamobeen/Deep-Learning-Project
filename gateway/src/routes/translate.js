import { Router } from "express";
import multer from "multer";
import axios from "axios";
import FormData from "form-data";

const router = Router();
const upload = multer({ storage: multer.memoryStorage(), limits: { fileSize: 25 * 1024 * 1024 } });
const ML = process.env.ML_SERVICE_URL || "http://localhost:8000";

router.post("/text-to-sign", async (req, res) => {
  try {
    const { data } = await axios.post(`${ML}/translate/text-to-sign`, req.body);
    res.json(data);
  } catch (e) { res.status(502).json({ error: "ml service unreachable" }); }
});

router.post("/sign-to-text", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "file required" });
  const fd = new FormData();
  fd.append("file", req.file.buffer, { filename: req.file.originalname || "clip.webm" });
  try {
    const { data } = await axios.post(`${ML}/translate/sign-to-text`, fd, { headers: fd.getHeaders() });
    res.json(data);
  } catch (e) { res.status(502).json({ error: "ml service unreachable" }); }
});

router.post("/speech-to-sign", upload.single("file"), async (req, res) => {
  if (!req.file) return res.status(400).json({ error: "audio file required" });
  const fd = new FormData();
  fd.append("file", req.file.buffer, { filename: req.file.originalname || "audio.webm" });
  try {
    const { data } = await axios.post(`${ML}/translate/speech-to-sign`, fd, { headers: fd.getHeaders() });
    res.json(data);
  } catch (e) { res.status(502).json({ error: "ml service unreachable" }); }
});

export default router;
