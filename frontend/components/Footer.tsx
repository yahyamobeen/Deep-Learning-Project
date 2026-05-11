import Link from "next/link";

export default function Footer() {
  return (
    <footer className="bg-slate-900 text-slate-300 mt-16">
      <div className="max-w-6xl mx-auto px-6 py-10 grid sm:grid-cols-4 gap-8">
        <div className="sm:col-span-2">
          <h3 className="text-white font-bold text-lg mb-2">🤟 SignBridge</h3>
          <p className="text-sm text-slate-400 max-w-sm">
            A deep-learning powered translator and tutor for sign language —
            built to bridge the communication gap.
          </p>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wide">Product</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/translate" className="hover:text-white">Translate</Link></li>
            <li><Link href="/learn"     className="hover:text-white">Learn</Link></li>
          </ul>
        </div>
        <div>
          <h4 className="text-white font-semibold mb-3 text-sm uppercase tracking-wide">Support</h4>
          <ul className="space-y-2 text-sm">
            <li><Link href="/help"    className="hover:text-white">Help &amp; FAQ</Link></li>
            <li><Link href="/contact" className="hover:text-white">Contact us</Link></li>
          </ul>
        </div>
      </div>
      <div className="border-t border-slate-800 text-center text-xs text-slate-500 py-4">
        © {new Date().getFullYear()} SignBridge — DL Course Project · Prof. Dr. Kamran Malik
      </div>
    </footer>
  );
}
