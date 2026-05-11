"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { useAuth } from "../../lib/auth";

export default function RegisterPage() {
  const { register } = useAuth();
  const router       = useRouter();
  const [name, setName]         = useState("");
  const [email, setEmail]       = useState("");
  const [password, setPassword] = useState("");
  const [err, setErr]           = useState("");
  const [busy, setBusy]         = useState(false);
  const [success, setSuccess]   = useState(false);

  async function submit(e: React.FormEvent) {
    e.preventDefault(); setBusy(true); setErr(""); setSuccess(false);
    try {
      await register(email, password, name);
      setSuccess(true);
      // Show the "account created" message for a moment before navigating.
      setTimeout(() => router.push("/learn"), 1200);
    }
    catch (e: any) { setErr(e?.response?.data?.error || "Registration failed"); }
    finally { setBusy(false); }
  }

  return (
    <div className="max-w-md mx-auto bg-white p-8 rounded-2xl shadow-lg mt-8">
      <h1 className="text-2xl font-bold mb-1">Create your account</h1>
      <p className="text-slate-500 mb-6">Start your sign-language learning journey.</p>
      <form onSubmit={submit} className="space-y-4">
        <input placeholder="Full name" value={name} onChange={e=>setName(e.target.value)}
          required className="w-full border rounded-lg px-4 py-2.5"/>
        <input type="email" placeholder="Email" value={email} onChange={e=>setEmail(e.target.value)}
          required className="w-full border rounded-lg px-4 py-2.5"/>
        <input type="password" placeholder="Password (min 6 chars)" value={password}
          onChange={e=>setPassword(e.target.value)} minLength={6} required
          className="w-full border rounded-lg px-4 py-2.5"/>
        {err && <p className="text-rose-600 text-sm">{err}</p>}
        {success && (
          <p className="text-emerald-700 bg-emerald-50 border border-emerald-200 rounded-lg px-3 py-2 text-sm font-medium">
            ✓ Account created — redirecting…
          </p>
        )}
        <button disabled={busy || success}
          className="w-full bg-indigo-600 text-white py-2.5 rounded-lg hover:bg-indigo-700 disabled:opacity-50 font-medium">
          {success ? "Account created ✓" : busy ? "Creating account…" : "Create account"}
        </button>
      </form>
      <p className="text-sm text-center mt-6 text-slate-600">
        Already have an account? <Link href="/login" className="text-indigo-600 hover:underline">Sign in</Link>
      </p>
    </div>
  );
}
