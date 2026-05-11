"use client";
import { useEffect, useRef, useState } from "react";

type Props = { onAudioReady: (blob: Blob) => void };

export default function AudioCapture({ onAudioReady }: Props) {
  const recRef    = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const [recording, setRecording] = useState(false);

  function stopMic() {
    if (recRef.current?.state === "recording") recRef.current.stop();
    recRef.current = null;
    streamRef.current?.getTracks().forEach(t => t.stop());
    streamRef.current = null;
    setRecording(false);
  }

  useEffect(() => () => stopMic(), []);   // release mic on unmount

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    streamRef.current = stream;
    const chunks: Blob[] = [];
    const rec = new MediaRecorder(stream, { mimeType: "audio/webm" });
    rec.ondataavailable = e => e.data.size && chunks.push(e.data);
    rec.onstop = () => {
      onAudioReady(new Blob(chunks, { type: "audio/webm" }));
      stream.getTracks().forEach(t => t.stop());
      streamRef.current = null;
    };
    recRef.current = rec; rec.start();
    setRecording(true);
  }
  function stop() { recRef.current?.stop(); setRecording(false); }

  return (
    <div className="flex items-center gap-3">
      {!recording ? (
        <button onClick={start} className="px-4 py-2 bg-rose-600 text-white rounded-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-white"/> Start recording
        </button>
      ) : (
        <button onClick={stop} className="px-4 py-2 bg-slate-700 text-white rounded-lg flex items-center gap-2">
          <span className="w-2 h-2 rounded-full bg-rose-400 animate-pulse"/> Stop
        </button>
      )}
      <span className="text-sm text-slate-500">{recording ? "Speak now…" : "Click to record audio"}</span>
    </div>
  );
}
