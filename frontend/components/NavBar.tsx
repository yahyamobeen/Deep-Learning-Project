"use client";
import Link from "next/link";
import { useAuth } from "../lib/auth";
import { usePathname } from "next/navigation";

export default function NavBar() {
  const { user, logout } = useAuth();
  const path = usePathname();
  const link = (href: string, label: string) => (
    <Link href={href}
      className={`px-3 py-1.5 rounded-md transition ${path===href ? "bg-white/20" : "hover:bg-white/10"}`}>
      {label}
    </Link>
  );

  return (
    <nav className="bg-gradient-to-r from-indigo-700 to-purple-700 text-white shadow-md sticky top-0 z-50">
      <div className="max-w-6xl mx-auto px-6 py-3 flex items-center gap-2">
        <Link href="/" className="font-bold text-lg mr-4 flex items-center gap-2">
          <span className="text-2xl">🤟</span> SignBridge
        </Link>
        {link("/translate", "Translate")}
        {link("/learn",     "Learn")}
        {link("/contact",   "Contact")}
        <div className="ml-auto flex items-center gap-2">
          {user ? (
            <>
              <span className="text-sm opacity-90 hidden sm:inline">Hi, {user.name}</span>
              <button onClick={logout}
                className="px-3 py-1.5 bg-white/15 hover:bg-white/25 rounded-md text-sm">
                Sign out
              </button>
            </>
          ) : (
            <>
              {link("/login", "Sign in")}
              <Link href="/register"
                className="px-3 py-1.5 bg-white text-indigo-700 rounded-md font-medium hover:bg-indigo-50">
                Get started
              </Link>
            </>
          )}
        </div>
      </div>
    </nav>
  );
}
