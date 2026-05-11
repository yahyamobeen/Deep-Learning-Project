"use client";
import { useState } from "react";
import axios from "axios";
import { useAuth } from "../../lib/auth";

export default function ContactPage() {
  const { user } = useAuth();
  const [form, setForm] = useState({
    name: user?.name || "", email: user?.email || "",
    category: "general", message: "",
  });
  const [sent, setSent] = useState(false);
  const [err, setErr]   = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr("");
    try { await axios.post("/api/feedback", form); setSent(true); }
    catch (e: any) { setErr(e?.response?.data?.error || "Could not send. Try again."); }
    finally { setBusy(false); }
  }

  if (sent) {
    return (
      <div className="max-w-md mx-auto bg-white rounded-2xl shadow-lg p-10 text-center mt-8">
        <div className="text-5xl mb-3">✅</div>
        <h1 className="text-2xl font-bold mb-2">Thanks for the feedback!</h1>
        <p className="text-slate-600">We've received your message and will get back to you shortly.</p>
      </div>
    );
  }

  return (
    <div className="grid md:grid-cols-2 gap-10 mt-4">
      <div>
        <h1 className="text-3xl font-bold mb-3">Get in touch</h1>
        <p className="text-slate-600 mb-6">
          Found a bug, have a feature idea, or just want to share how SignBridge is working for you?
          We'd love to hear from you.
        </p>
        <ul className="space-y-3 text-sm">
          <li className="flex gap-3"><span>📧</span><span>signbridge.team@example.com</span></li>
          <li className="flex gap-3"><span>🏫</span><span>Department of Data Science, Batch 2023</span></li>
          <li className="flex gap-3"><span>👨‍🏫</span><span>Course advisor: Prof. Dr. Kamran Malik</span></li>
        </ul>
      </div>

      <form onSubmit={submit} className="bg-white p-6 rounded-2xl shadow-lg space-y-4">
        <div className="grid grid-cols-2 gap-3">
          <input placeholder="Name" value={form.name} onChange={e=>setForm({...form,name:e.target.value})}
            className="border rounded-lg px-3 py-2.5"/>
          <input type="email" placeholder="Email" value={form.email} onChange={e=>setForm({...form,email:e.target.value})}
            className="border rounded-lg px-3 py-2.5"/>
        </div>
        <select value={form.category} onChange={e=>setForm({...form,category:e.target.value})}
          className="w-full border rounded-lg px-3 py-2.5 bg-white">
          <option value="general">General feedback</option>
          <option value="bug">Bug report</option>
          <option value="feature">Feature request</option>
          <option value="accessibility">Accessibility issue</option>
        </select>
        <textarea placeholder="Your message…" rows={5} required minLength={5}
          value={form.message} onChange={e=>setForm({...form,message:e.target.value})}
          className="w-full border rounded-lg px-3 py-2.5"/>
        {err && <p className="text-rose-600 text-sm">{err}</p>}
        <button disabled={busy}
          className="w-full bg-indigo-600 text-white py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium">
          {busy ? "Sending…" : "Send message"}
        </button>
      </form>
    </div>
  );
}
