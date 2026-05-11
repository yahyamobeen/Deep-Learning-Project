"use client";
import Link from "next/link";
import { useEffect, useState } from "react";

const features = [
  { icon: "👋", title: "Sign → Text",   desc: "Real-time webcam translation of sign language to readable text." },
  { icon: "💬", title: "Text → Sign",   desc: "Type any sentence and watch it rendered as a sign sequence." },
  { icon: "🎙️", title: "Speech → Sign", desc: "Speak naturally — Whisper transcribes and signs back to you." },
  { icon: "🎓", title: "Interactive Tutor", desc: "Learn with feedback — your sign attempts are scored automatically." },
];

const stats = [
  { num: "2,000+", label: "Sign vocabulary" },
  { num: "<400ms", label: "Per-sign latency" },
  { num: "4",      label: "Translation modes" },
  { num: "30+",    label: "Built-in lessons" },
];

const examples = [
  { en: "Hello, how are you?",      gloss: "HELLO HOW YOU" },
  { en: "Thank you very much.",      gloss: "THANK-YOU VERY MUCH" },
  { en: "I love learning sign language.", gloss: "I LOVE LEARN SIGN-LANGUAGE" },
  { en: "Where is the bathroom?",    gloss: "BATHROOM WHERE" },
];

export default function Home() {
  const [idx, setIdx] = useState(0);
  useEffect(() => { const t = setInterval(() => setIdx(i => (i+1) % examples.length), 2800); return () => clearInterval(t); }, []);

  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="grid md:grid-cols-2 gap-10 items-center pt-8">
        <div className="space-y-6">
          <span className="inline-block px-3 py-1 text-xs font-semibold bg-indigo-100 text-indigo-700 rounded-full">
            Powered by Deep Learning
          </span>
          <h1 className="text-5xl font-bold leading-tight tracking-tight">
            Bridging communication, <span className="text-indigo-600">one sign at a time.</span>
          </h1>
          <p className="text-lg text-slate-600">
            SignBridge translates between sign language, text and speech in real time —
            and helps anyone learn to sign through interactive, scored lessons.
          </p>
          <div className="flex gap-3">
            <Link href="/translate"
              className="px-6 py-3 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700 font-medium shadow-lg shadow-indigo-200">
              Try it now →
            </Link>
            <Link href="/learn"
              className="px-6 py-3 bg-white border border-slate-300 rounded-lg hover:bg-slate-50 font-medium">
              Start learning
            </Link>
          </div>
        </div>

        {/* Animated example card */}
        <div className="bg-gradient-to-br from-indigo-600 to-purple-700 p-8 rounded-3xl shadow-2xl text-white">
          <div className="text-xs uppercase tracking-widest opacity-75 mb-3">Live example</div>
          <div className="text-2xl font-light min-h-[3rem] transition-all">{examples[idx].en}</div>
          <div className="my-4 text-2xl opacity-60">↓</div>
          <div className="flex flex-wrap gap-2">
            {examples[idx].gloss.split(" ").map((g,i) => (
              <span key={i} className="px-3 py-1.5 bg-white/20 rounded-md backdrop-blur font-mono text-sm">{g}</span>
            ))}
          </div>
          <div className="flex gap-1 mt-6">
            {examples.map((_,i) => (
              <button key={i} onClick={()=>setIdx(i)}
                className={`h-1.5 rounded-full transition-all ${i===idx ? "w-8 bg-white":"w-2 bg-white/40"}`}/>
            ))}
          </div>
        </div>
      </section>

      {/* Stats */}
      <section className="grid grid-cols-2 md:grid-cols-4 gap-6">
        {stats.map(s => (
          <div key={s.label} className="text-center bg-white rounded-2xl p-6 shadow-sm border border-slate-100">
            <div className="text-3xl font-bold text-indigo-600">{s.num}</div>
            <div className="text-sm text-slate-600 mt-1">{s.label}</div>
          </div>
        ))}
      </section>

      {/* Features */}
      <section>
        <div className="text-center mb-10">
          <h2 className="text-3xl font-bold">Everything you need to communicate</h2>
          <p className="text-slate-600 mt-2">Four modes, one accessible platform.</p>
        </div>
        <div className="grid md:grid-cols-2 lg:grid-cols-4 gap-4">
          {features.map(f => (
            <div key={f.title}
              className="group bg-white p-6 rounded-2xl shadow-sm border border-slate-100 hover:shadow-lg hover:-translate-y-1 transition">
              <div className="text-4xl mb-3 group-hover:scale-110 transition-transform">{f.icon}</div>
              <h3 className="font-semibold text-lg mb-1">{f.title}</h3>
              <p className="text-sm text-slate-600">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="bg-gradient-to-r from-indigo-600 to-purple-700 rounded-3xl p-10 md:p-14 text-white text-center">
        <h2 className="text-3xl md:text-4xl font-bold mb-3">Ready to start signing?</h2>
        <p className="text-indigo-100 mb-6 max-w-xl mx-auto">
          Create a free account to track your learning progress and unlock the interactive tutor.
        </p>
        <Link href="/register"
          className="inline-block bg-white text-indigo-700 px-8 py-3 rounded-lg font-semibold hover:bg-indigo-50 shadow-lg">
          Create free account
        </Link>
      </section>
    </div>
  );
}
