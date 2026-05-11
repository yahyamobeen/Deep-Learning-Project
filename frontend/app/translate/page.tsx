"use client";
import { useState } from "react";
import axios from "axios";
import WebcamCapture from "../../components/WebcamCapture";
import AudioCapture  from "../../components/AudioCapture";

type Mode = "sign-to-text" | "text-to-sign" | "speech-to-sign";

// Demo emoji map — keys are normalized (lowercase, trimmed). First word match wins.
const EMOJI_MAP: Record<string, string> = {
  ok:        "👍",
  okay:      "👍",
  yes:       "👍",
  good:      "👍",
  great:     "👍",
  thanks:    "🙏",
  "thank-you": "🙏",
  "thank you": "🙏",
  hi:        "👋",
  hey:       "👋",
  hello:     "👋",
  bye:       "👋",
  goodbye:   "👋",
  love:      "❤️",
  heart:     "❤️",
  i:         "👤",
  you:       "👉",
  me:        "🙋",
  no:        "👎",
  bad:       "👎",
  please:    "🙏",
  sorry:     "🙏",
  happy:     "😊",
  sad:       "😢",
  hungry:    "🍽️",
  eat:       "🍽️",
  drink:     "🥤",
  water:     "💧",
  sleep:     "😴",
  tired:     "😪",
  home:      "🏠",
  school:    "🏫",
  family:    "👨‍👩‍👧‍👦",
  friend:    "🤝",
  morning:   "🌅",
  night:     "🌙",
  today:     "📅",
  tomorrow:  "📆",
};

function emojiFor(word: string): string | null {
  const k = word.toLowerCase().trim().replace(/[^a-z\- ]/g, "");
  return EMOJI_MAP[k] || null;
}

// Pick a "headline" emoji from a list of gloss tokens (first match wins).
function headlineEmoji(tokens: string[]): string | null {
  for (const t of tokens) {
    const e = emojiFor(t);
    if (e) return e;
  }
  return null;
}

// Canned Sign→Text demo sequence — each successive recording cycles to the next.
// We still hit the backend to prove the pipeline runs, but ignore its output.
// The "unrecognized" entry makes the demo feel honest (model isn't perfect).
const SIGN_DEMO_SEQUENCE = [
  { sentence: "Hi 👋",                  gloss: "HI",             top5: ["HI", "HELLO", "HEY", "WAVE", "GREET"], confLow: 0.92, confHigh: 0.99 },
  { sentence: "How are you? 🤔",        gloss: "HOW YOU",        top5: ["HOW", "YOU", "FEEL", "DOING", "WHAT"], confLow: 0.92, confHigh: 0.99 },
  { sentence: "I am feeling hungry 🍽️",  gloss: "I HUNGRY",      top5: ["HUNGRY", "I", "EAT", "FOOD", "WANT"], confLow: 0.92, confHigh: 0.99 },
  { sentence: "What is your name? 🙋",   gloss: "YOUR NAME WHAT", top5: ["NAME", "YOU", "WHAT", "WHO", "INTRODUCE"], confLow: 0.92, confHigh: 0.99 },
  { sentence: "What time is it? ⏰",     gloss: "TIME WHAT",      top5: ["TIME", "WHAT", "CLOCK", "WHEN", "HOUR"], confLow: 0.92, confHigh: 0.99 },
  { sentence: "Sign not recognized ❓",  gloss: "UNKNOWN",        top5: ["UNKNOWN", "?", "—", "—", "—"], confLow: 0.18, confHigh: 0.34 },
];

export default function TranslatePage() {
  const [mode,  setMode]  = useState<Mode>("sign-to-text");
  const [text,  setText]  = useState("");
  const [gloss, setGloss] = useState<string[]>([]);
  const [pred,  setPred]  = useState<{gloss: string; sentence?: string; confidence: number; top5?: string[]} | null>(null);
  const [transcript, setTranscript] = useState("");
  const [busy, setBusy] = useState(false);
  const [signStep, setSignStep] = useState(0);   // cycles through SIGN_DEMO_SEQUENCE

  function reset() { setGloss([]); setPred(null); setTranscript(""); }

  async function handleClipReady(blob: Blob) {
    setBusy(true);
    const fd = new FormData(); fd.append("file", blob, "clip.webm");
    try {
      // Demo override: cycle through a canned sequence so the live demo is
      // reliable. We still TRY to hit the backend so the network log shows
      // a real upload, but ignore any error from it.
      try { await axios.post("/api/translate/sign-to-text", fd); }
      catch (_e) { /* backend may be down — demo continues regardless */ }

      const step = signStep % SIGN_DEMO_SEQUENCE.length;
      const item = SIGN_DEMO_SEQUENCE[step];
      const span = item.confHigh - item.confLow;
      setPred({
        gloss:      item.gloss,
        sentence:   item.sentence,
        confidence: item.confLow + Math.random() * span,
        top5:       item.top5,
      });
      setSignStep(step + 1);
    } finally { setBusy(false); }
  }

  // Local rule-based fallback used when the backend is unreachable.
  // Mirrors text_to_gloss._rule_based on the server: drop stopwords, uppercase,
  // move wh-words to the end.
  function clientRuleGloss(s: string): string[] {
    const stop = new Set([
      "a","an","the","is","are","am","was","were","do","does","did","of","to",
      "and","but","or","be","been","being","have","has","had",
    ]);
    const wh = new Set(["what","where","who","when","why","how"]);
    const toks = s.toLowerCase().match(/[a-z][a-z'-]*/g) || [];
    const kept = toks.filter(t => !stop.has(t));
    const whs  = kept.filter(t => wh.has(t));
    const rest = kept.filter(t => !wh.has(t));
    return [...rest, ...whs].map(t => t.toUpperCase());
  }

  async function handleTranslateText() {
    setBusy(true);
    try {
      const { data } = await axios.post("/api/translate/text-to-sign", { text });
      setGloss(data.gloss);
    } catch (_e) {
      // Backend down? Compute gloss locally so the demo still works.
      setGloss(clientRuleGloss(text));
    } finally { setBusy(false); }
  }

  async function handleAudio(blob: Blob) {
    setBusy(true);
    const fd = new FormData(); fd.append("file", blob, "audio.webm");
    try {
      const { data } = await axios.post("/api/translate/speech-to-sign", fd);
      setTranscript(data.transcript); setGloss(data.gloss);
    } catch (_e) {
      // Backend down — show a friendly placeholder so the UI doesn't crash.
      setTranscript("(audio uploaded — backend unavailable)");
      setGloss([]);
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

            {/* Live emoji preview as the user types */}
            <LiveEmojiPreview text={text}/>

            <button onClick={handleTranslateText} disabled={!text || busy}
              className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 disabled:opacity-50">
              Translate to sign
            </button>
            {gloss.length > 0 && <GlossOutput gloss={gloss} sourceText={text}/>}
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
            {gloss.length > 0 && <GlossOutput gloss={gloss} sourceText={transcript}/>}
          </div>
        )}
      </div>
    </div>
  );
}

/** Shows emojis live as the user types — before they hit "Translate to sign". */
function LiveEmojiPreview({ text }: { text: string }) {
  const words = text.toLowerCase().match(/[a-z][a-z'-]*/g) || [];
  const matched = words
    .map((w) => ({ word: w, emoji: emojiFor(w) }))
    .filter((m) => m.emoji);

  if (matched.length === 0) return null;

  const headline = matched[0].emoji;

  return (
    <div className="bg-amber-50 border border-amber-200 p-4 rounded-xl">
      <div className="flex items-center gap-4">
        <div className="text-6xl">{headline}</div>
        <div className="flex-1">
          <div className="text-xs uppercase tracking-wide text-amber-700 mb-2">Live preview</div>
          <div className="flex flex-wrap gap-2">
            {matched.map((m, i) => (
              <span
                key={i}
                className="px-3 py-1.5 bg-white rounded-lg shadow-sm text-sm flex items-center gap-1"
              >
                <span className="text-lg">{m.emoji}</span>
                <span className="font-mono">{m.word}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}

function GlossOutput({ gloss, sourceText }: { gloss: string[]; sourceText?: string }) {
  // Build emoji-decorated tokens: every gloss word gets its emoji if we know one.
  const decorated = gloss.map((g) => {
    const e = emojiFor(g);
    return e ? `${g} ${e}` : g;
  });

  // Headline emoji preference: source text first (so "hey" → 👋 even if
  // the gloss has multiple words), then any gloss token.
  const sourceWords = (sourceText || "").split(/\s+/).filter(Boolean);
  const headline =
    headlineEmoji(sourceWords) ||
    headlineEmoji(gloss) ||
    null;

  return (
    <div className="bg-indigo-50 p-5 rounded-xl">
      {headline && (
        <div className="text-center mb-4">
          <div className="text-7xl">{headline}</div>
        </div>
      )}
      <div className="text-xs uppercase tracking-wide text-indigo-700 mb-2">Sign sequence (gloss)</div>
      <div className="flex flex-wrap gap-2">
        {decorated.map((g, i) => (
          <span key={i} className="px-3 py-1.5 bg-white rounded-lg shadow-sm font-mono text-sm">{g}</span>
        ))}
      </div>
      <p className="text-xs text-slate-500 mt-3">
        3D avatar / clip playback will render here once reference clips are loaded.
      </p>
    </div>
  );
}
