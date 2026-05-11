import express from "express";
import cors from "cors";
import morgan from "morgan";
import dotenv from "dotenv";

import authRouter from "./routes/auth.js";
import translateRouter from "./routes/translate.js";
import lessonsRouter from "./routes/lessons.js";
import feedbackRouter from "./routes/feedback.js";

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json({ limit: "10mb" }));
app.use(morgan("dev"));

app.get("/health", (_req, res) => res.json({ status: "ok" }));

app.use("/api/auth", authRouter);
app.use("/api/translate", translateRouter);
app.use("/api/lessons", lessonsRouter);
app.use("/api/feedback", feedbackRouter);

const PORT = process.env.PORT || 4000;
app.listen(PORT, () => console.log(`gateway running on :${PORT}`));
