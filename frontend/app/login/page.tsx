"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../lib/auth";

export default function LoginPage() {
  const { login } = useAuth();
  const router    = useRouter();
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr]           = useState("");
  const [busy, setBusy]         = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr("");
    try { await login(email, password); router.push("/learn"); }
    catch (e: any) { setErr(e?.response?.data?.error || "Login failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-lg mt-8">
      <h1 className="text-2xl font-bold mb-1">Welcome back</h1>
      <p className="text-slate-500 mb-6">Sign in to track your sign-language progress.</p>
      <form onSubmit={submit} className="space-y-4">
        <input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}
          required className="w-full border rounded-lg px-4 py-2.5"/>
        <input type="password" placeholder="Password" value={password} onChange={e=>setPassword(e.target.value)}
          required className="w-full border rounded-lg px-4 py-2.5"/>
        {err && <p className="text-rose-600 text-sm">{err}</p>}
        <button disabled={busy}
          className="w-full bg-indigo-600 text-white py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium">
          {busy ? "Signing in…" : "Sign in"}
        </button>
      </form>
      <p className="text-sm text-center mt-6 text-slate-600">
        New here? <Link href="/register" className="text-indigo-600 hover:underline">Create an account</Link>
      </p>
    </div>
  );
}
