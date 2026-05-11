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

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user,  setUser]  = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);

  useEffect(() => {
    const t = typeof window !== "undefined" ? localStorage.getItem("token") : null;
    const u = typeof window !== "undefined" ? localStorage.getItem("user")  : null;
    if (t && u) { setToken(t); setUser(JSON.parse(u)); axios.defaults.headers.common.Authorization = `Bearer ${t}`; }
  }, []);

  async function login(email: string, password: string) {
    const { data } = await axios.post("/api/auth/login", { email, password });
    localStorage.setItem("token", data.token);
    localStorage.setItem("user",  JSON.stringify(data.user));
    axios.defaults.headers.common.Authorization = `Bearer ${data.token}`;
    setToken(data.token); setUser(data.user);
  }
  async function register(email: string, password: string, name: string) {
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
