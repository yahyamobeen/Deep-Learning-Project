"use client";
import { useState } from "react";
import Link from "next/link";

const faqs = [
  { q: "What is SignBridge?",
    a: "A deep-learning powered platform that translates between sign language, text, and speech, and includes an interactive tutor for learning sign language." },
  { q: "Do I need special hardware?",
    a: "No — only a standard webcam and microphone. All processing runs from regular video frames; no sensor gloves or depth cameras required." },
  { q: "Why do I have to log in to use the tutor?",
    a: "The tutor saves your scores per lesson so you can track your progress over time. Translation features (Sign↔Text, Speech→Sign) work without an account." },
  { q: "Which sign language is supported?",
    a: "American Sign Language (ASL) is the primary supported language. Pakistan Sign Language (PSL) support is in active development as a feasibility extension." },
  { q: "Is my video stored anywhere?",
    a: "No. Webcam clips are sent directly to the inference server, processed in memory, and discarded immediately. Only your numeric lesson scores are stored." },
  { q: "Why is my prediction wrong?",
    a: "Most likely causes: poor lighting, fast motion, the sign is outside the trained vocabulary (~2,000 signs), or your hands are partially out of frame. Try again with brighter, more centered framing." },
  { q: "How accurate is it?",
    a: "On the WLASL benchmark our Sign Language Transformer reaches roughly 60–65% Top-1 accuracy and 85% Top-5 accuracy on isolated signs." },
  { q: "Can I contribute or report a bug?",
    a: "Yes! Use the Contact page to send us bug reports, feature requests, or accessibility issues." },
];

export default function HelpPage() {
  const [open, setOpen] = useState<number | null>(0);
  return (
    <div className="max-w-3xl mx-auto space-y-8">
      <header className="text-center">
        <h1 className="text-4xl font-bold">Help &amp; FAQ</h1>
        <p className="text-slate-600 mt-2">Answers to the questions we hear most often.</p>
      </header>

      <div className="space-y-3">
        {faqs.map((f, i) => (
          <div key={i} className="bg-white rounded-xl shadow-sm border border-slate-100 overflow-hidden">
            <button onClick={() => setOpen(open===i ? null : i)}
              className="w-full flex justify-between items-center px-5 py-4 text-left hover:bg-slate-50">
              <span className="font-medium">{f.q}</span>
              <span className={`transition-transform ${open===i ? "rotate-180" : ""}`}>⌄</span>
            </button>
            {open===i && <div className="px-5 pb-5 text-slate-600 text-sm leading-relaxed">{f.a}</div>}
          </div>
        ))}
      </div>

      <div className="bg-indigo-50 rounded-2xl p-6 text-center">
        <h3 className="font-semibold text-lg">Still need help?</h3>
        <p className="text-slate-600 text-sm mb-3">Reach out to us directly.</p>
        <Link href="/contact" className="inline-block px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">
          Contact us →
        </Link>
      </div>
    </div>
  );
}
