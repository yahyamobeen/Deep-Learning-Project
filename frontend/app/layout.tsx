import "./globals.css";
import { AuthProvider } from "../lib/auth";
import NavBar from "../components/NavBar";
import Footer from "../components/Footer";

export const metadata = {
  title: "SignBridge — Sign Language Translator & Tutor",
  description: "Real-time sign language translation and interactive lessons, powered by deep learning.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col">
        <AuthProvider>
          <NavBar />
          <main className="flex-1 max-w-6xl mx-auto w-full p-6">{children}</main>
          <Footer />
        </AuthProvider>
      </body>
    </html>
  );
}
