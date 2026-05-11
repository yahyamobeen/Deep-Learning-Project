"use client";
import { createContext, useContext, useEffect, useState } from "react";
import axios from "axios";

type User = { email: string; name: string };
type Ctx  = {
  user: User | null;
  token: string | null;
  login:    (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, name: string) => Promise<void>;
  logout: () => void;
};

const AuthCtx = createContext<Ctx>(null as any);
export const useAuth = () => useContext(AuthCtx);

// Demo mode: bypass the gateway and accept any login / registration locally.
// Set NEXT_PUBLIC_DEMO_AUTH=false in Vercel env to re-enable the real backend flow.
const DEMO_AUTH =
  (process.env.NEXT_PUBLIC_DEMO_AUTH ?? "true").toLowerCase() !== "false";

function fakeToken(email: string) {
  // Not a real JWT — a recognizable opaque string that lasts for the session.
  if (typeof window === "undefined") return "demo.ssr";
  return "demo." + btoa(email + "." + Date.now()).replace(/=+$/, "");
}

function delay(ms: number) {
  return new Promise<void>((r) => setTimeout(r, ms));
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,  setUser]  = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const u = typeof window !== "undefined" ? localStorage.getItem("user")  : null;
    if (t && u) { setToken(t); setUser(JSON.parse(u)); axios.defaults.headers.common.Authorization = `Bearer ${t}`; }
  }, []);

  function persist(t: string, u: User) {
    localStorage.setItem("token", t);
    localStorage.setItem("user",  JSON.stringify(u));
    axios.defaults.headers.common.Authorization = `Bearer ${t}`;
    setToken(t); setUser(u);
  }

  async function login(email: string, password: string) {
    if (DEMO_AUTH) {
      await delay(400);             // small spinner so it feels real
      const u: User = { email, name: email.split("@")[0] || "User" };
      persist(fakeToken(email), u);
      return;
    }
    const { data } = await axios.post("/api/auth/login", { email, password });
    persist(data.token, data.user);
  }

  async function register(email: string, password: string, name: string) {
    if (DEMO_AUTH) {
      await delay(500);
      const u: User = { email, name: name || email.split("@")[0] || "User" };
      persist(fakeToken(email), u);
      return;
    }
    await axios.post("/api/auth/register", { email, password, name });
    await login(email, password);
  }

  function logout() {
    localStorage.removeItem("token"); localStorage.removeItem("user");
    delete axios.defaults.headers.common.Authorization;
    setToken(null); setUser(null);
  }

  return <AuthCtx.Provider value={{ user, token, login, register, logout }}>{children}</AuthCtx.Provider>;
}
