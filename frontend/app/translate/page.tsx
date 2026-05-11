"use client";
import { useState } from "react";
import axios from "axios";
import WebcamCapture from "../../components/WebcamCapture";
import AudioCapture  from "../../components/AudioCapture";

type Mode = "sign-to-text" | "text-to-sign" | "speech-to-sign";

export default function TranslatePage() {
  const [mode,  setMode]  = useState<Mode>("sign-to-text");
  const [text,  setText]  = useState("");
  const [gloss, setGloss] = useState<string[]>([]);
  const [pred,  setPred]  = useState<{gloss: string; sentence?: string; confidence: number; top5?: string[]} | null>(null);
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);

  function reset() { setGloss([]); setPred(null); setTranscript(""); }

  async function handleClipReady(blob: Blob) {
    setBusy(true);
    const fd = new FormData(); fd.append("file", blob, "clip.webm");
    try { setPred((await axios.post("/api/translate/sign-to-text", fd)).data); }
    finally { setBusy(false); }
  }
  async function handleTranslateText() {
    setBusy(true);
    try { setGloss((await axios.post("/api/translate/text-to-sign", { text })).data.gloss); }
    finally { setBusy(false); }
  }
  async function handleAudio(blob: Blob) {
    setBusy(true);
    const fd = new FormData(); fd.append("file", blob, "audio.webm");
    try {
      const { data } = await axios.post("/api/translate/speech-to-sign", fd);
      setTranscript(data.transcript); setGloss(data.gloss);
    } finally { setBusy(false); }
  }

  const Tab = ({ k, label, icon }: { k: Mode; label: string; icon: string }) => (
    <button onClick={() => { setMode(k); reset(); }}
      className={`flex-1 px-4 py-3 rounded-xl font-medium transition flex items-center justify-center gap-2 ${
        mode===k ? "bg-indigo-600 text-white shadow-lg shadow-indigo-200" : "bg-white hover:bg-slate-50 border"
      }`}>
      <span>{icon}</span><span>{label}</span>
    </button>
  );

  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-bold">Translator</h1>
        <p className="text-slate-600">Choose a translation mode and start.</p>
      </header>

      <div className="flex gap-2">
        <Tab k="sign-to-text"  label="Sign → Text"  icon="👋"/>
        <Tab k="text-to-sign"  label="Text → Sign"  icon="💬"/>
        <Tab k="speech-to-sign" label="Speech → Sign" icon="🎙️"/>
      </div>

      <div className="bg-white p-6 rounded-2xl shadow-sm border border-slate-100">
        {mode === "sign-to-text" && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">Record a 3-second clip of yourself signing.</p>
            <WebcamCapture onClipReady={handleClipReady}/>
            {busy && <p className="text-slate-500">Translating…</p>}
            {pred && (
              <div className="bg-indigo-50 p-5 rounded-xl">
                {pred.sentence && (
                  <>
                    <div className="text-xs uppercase tracking-wide text-indigo-700">English</div>
                    <div className="text-2xl font-semibold mt-1">{pred.sentence}</div>
                  </>
                )}
                <div className="text-xs uppercase tracking-wide text-indigo-700 mt-3">Gloss</div>
                <div className="text-3xl font-bold mt-1">{pred.gloss}</div>
                <div className="text-sm text-slate-500 mt-1">confidence: {(pred.confidence*100).toFixed(1)}%</div>
                {pred.top5 && pred.top5.length > 0 && (
                  <div className="text-xs text-slate-500 mt-2">top-5: {pred.top5.join(", ")}</div>
                )}
              </div>
            )}
          </div>
        )}

        {mode === "text-to-sign" && (
          <div className="space-y-4">
            <textarea value={text} onChange={e=>setText(e.target.value)}
              placeholder="Type a sentence in English…"
              className="w-full border rounded-lg p-3" rows={3}/>
            <button onClick={handleTranslateText} disabled={!text || busy}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              Translate to sign
            </button>
            {gloss.length > 0 && <GlossOutput gloss={gloss}/>}
          </div>
        )}

        {mode === "speech-to-sign" && (
          <div className="space-y-4">
            <p className="text-sm text-slate-600">
              Speak naturally — Whisper will transcribe your audio, then translate it to a sign sequence.
            </p>
            <AudioCapture onAudioReady={handleAudio}/>
            {busy && <p className="text-slate-500">Transcribing &amp; translating…</p>}
            {transcript && (
              <div className="bg-slate-50 p-4 rounded-lg">
                <div className="text-xs uppercase tracking-wide text-slate-500">Transcript</div>
                <div className="text-lg italic">"{transcript}"</div>
              </div>
            )}
            {gloss.length > 0 && <GlossOutput gloss={gloss}/>}
          </div>
        )}
      </div>
    </div>
  );
}

function GlossOutput({ gloss }: { gloss: string[] }) {
  return (
    <div className="bg-indigo-50 p-5 rounded-xl">
      <div className="text-xs uppercase tracking-wide text-indigo-700 mb-2">Sign sequence (gloss)</div>
      <div className="flex flex-wrap gap-2">
        {gloss.map((g,i) => (
          <span key={i} className="px-3 py-1.5 bg-white rounded-lg shadow-sm font-mono text-sm">{g}</span>
        ))}
      </div>
      <p className="text-xs text-slate-500 mt-3">
        3D avatar / clip playback will render here once reference clips are loaded.
      </p>
    </div>
  );
}
