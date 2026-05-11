"use client";
import { useEffect, useState } from "react";
import axios from "axios";
import Link from "next/link";
import WebcamCapture from "../../components/WebcamCapture";
import { useAuth } from "../../lib/auth";

type Lesson = { id: string; label: string; video: string; level: number };

export default function LearnPage() {
  const { user, token } = useAuth();
  const [lessons, setLessons]   = useState<Lesson[]>([]);
  const [active,  setActive]    = useState<Lesson | null>(null);
  const [result,  setResult]    = useState<{score:number; hint:string; passed:boolean; best?:number} | null>(null);
  const [progress, setProgress] = useState<Record<string, number>>({});

  useEffect(() => { axios.get("/api/lessons").then(r => setLessons(r.data)).catch(()=>{}); }, []);
  useEffect(() => {
    if (!token) return;
    axios.get("/api/lessons/me/progress").then(r => setProgress(r.data)).catch(()=>{});
  }, [token]);

  // Auth gate
  if (!user) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg p-10 text-center mt-8 space-y-4">
        <div className="text-5xl">🔒</div>
        <h1 className="text-2xl font-bold">Sign in to start learning</h1>
        <p className="text-slate-600">
          The interactive tutor saves your progress per lesson. Create a free account
          (or sign in) to begin.
        </p>
        <div className="flex gap-3 justify-center pt-2">
          <Link href="/login"    className="px-5 py-2.5 bg-indigo-600 text-white rounded-lg hover:bg-indigo-700">Sign in</Link>
          <Link href="/register" className="px-5 py-2.5 bg-white border rounded-lg hover:bg-slate-50">Create account</Link>
        </div>
      </div>
    );
  }

  async function handleAttempt(blob: Blob) {
    if (!active) return;
    const fd = new FormData();
    fd.append("file", blob, "attempt.webm");
    const { data } = await axios.post(`/api/lessons/${active.id}/score`, fd);
    setResult(data);
    if (data.best !== undefined) setProgress(p => ({ ...p, [active.id]: data.best }));
  }

  const overall = lessons.length
    ? Math.round(lessons.reduce((s,l) => s + (progress[l.id] || 0), 0) / lessons.length)
    : 0;

  return (
    <div className="space-y-6">
      {/* Progress header */}
      <div className="bg-gradient-to-r from-indigo-600 to-purple-700 text-white p-6 rounded-2xl shadow flex items-center gap-6">
        <div className="w-16 h-16 rounded-full bg-white/20 grid place-items-center text-2xl font-bold">
          {user.name[0]?.toUpperCase()}
        </div>
        <div className="flex-1">
          <div className="text-sm opacity-80">Welcome back,</div>
          <div className="text-xl font-semibold">{user.name}</div>
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold">{overall}<span className="text-lg opacity-70">/100</span></div>
          <div className="text-sm opacity-80">Overall score</div>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        <aside className="space-y-2">
          <h2 className="font-semibold text-slate-700">Lessons</h2>
          {lessons.map(l => {
            const score = progress[l.id] || 0;
            return (
              <button key={l.id} onClick={() => { setActive(l); setResult(null); }}
                className={`block w-full text-left px-3 py-2.5 rounded-lg transition ${active?.id===l.id ? "bg-indigo-600 text-white shadow":"bg-white hover:bg-slate-50"}`}>
                <div className="flex justify-between items-center">
                  <div>
                    <div className="font-medium">{l.label}</div>
                    <div className="text-xs opacity-75">Level {l.level}</div>
                  </div>
                  {score > 0 && (
                    <div className={`text-xs px-2 py-0.5 rounded-full ${score>=70 ? "bg-green-100 text-green-700":"bg-amber-100 text-amber-700"}`}>
                      {score}
                    </div>
                  )}
                </div>
              </button>
            );
          })}
        </aside>

        <section className="md:col-span-2 space-y-4">
          {!active && <p className="text-slate-500 italic">Pick a lesson on the left to begin.</p>}
          {active && (
            <>
              <div className="flex justify-between items-baseline">
                <h2 className="text-2xl font-bold">{active.label}</h2>
                {progress[active.id] && <span className="text-sm text-slate-500">Best: {progress[active.id]}/100</span>}
              </div>
              <video src={active.video} controls className="w-full max-w-md rounded-lg shadow"/>
              <h3 className="font-semibold pt-2">Now try it yourself</h3>
              <WebcamCapture onClipReady={handleAttempt} />
              {result && (
                <div className={`p-5 rounded-xl shadow ${result.passed ? "bg-green-50 border border-green-200":"bg-amber-50 border border-amber-200"}`}>
                  <div className="text-4xl font-bold">{result.score} <span className="text-lg text-slate-500">/ 100</span></div>
                  <p className="mt-1 text-slate-700">{result.hint}</p>
                </div>
              )}
            </>
          )}
        </section>
      </div>
    </div>
  );
}
