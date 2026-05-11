"use client";
import { useEffect, useRef, useState } from "react";

type Props = { onClipReady: (blob: Blob) => void; durationMs?: number };

export default function WebcamCapture({ onClipReady, durationMs = 3000 }: Props) {
  const videoRef  = useRef<HTMLVideoElement>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const recRef    = useRef<MediaRecorder | null>(null);
  const [recording, setRecording] = useState(false);

  function stopCamera() {
    recRef.current?.state === "recording" && recRef.current.stop();
    recRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    if (videoRef.current) videoRef.current.srcObject = null;
  }

  useEffect(() => {
    let cancelled = false;
    navigator.mediaDevices.getUserMedia({ video: true, audio: false }).then(s => {
      if (cancelled) {                    // unmounted before camera resolved
        s.getTracks().forEach(t => t.stop());
        return;
      }
      streamRef.current = s;
      if (videoRef.current) videoRef.current.srcObject = s;
    }).catch(() => { /* user denied — ignore */ });

    return () => { cancelled = true; stopCamera(); };
  }, []);

  // Stop camera when tab/window is hidden (extra safety)
  useEffect(() => {
    const onHide = () => document.visibilityState === "hidden" && stopCamera();
    document.addEventListener("visibilitychange", onHide);
    return () => document.removeEventListener("visibilitychange", onHide);
  }, []);

  async function start() {
    const stream = streamRef.current;
    if (!stream) return;
    const chunks: Blob[] = [];
    const rec = new MediaRecorder(stream, { mimeType: "video/webm;codecs=vp9" });
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    rec.onstop = () => onClipReady(new Blob(chunks, { type: "video/webm" }));
    recRef.current = rec;
    rec.start();
    setRecording(true);
    setTimeout(() => { rec.state === "recording" && rec.stop(); setRecording(false); }, durationMs);
  }

  return (
    <div className="space-y-2">
      <video ref={videoRef} autoPlay muted playsInline
        className="w-full max-w-md rounded shadow bg-black"/>
      <button onClick={start} disabled={recording}
        className="px-4 py-2 bg-rose-600 text-white rounded disabled:opacity-50">
        {recording ? "Recording…" : `Record ${durationMs/1000}s clip`}
      </button>
    </div>
  );
}
