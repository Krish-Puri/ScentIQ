import type { Metadata } from "next";
import Link from "next/link";
import "./globals.css";

export const metadata: Metadata = {
  title: "SCENTIQ — Evidence-Led Fragrance Intelligence",
  description: "Personal fragrance discovery, side-by-side comparisons, and transparent clone intelligence.",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body className="min-h-screen flex flex-col bg-[#FAF9F5] text-slate-900 selection:bg-amber-100 selection:text-amber-900">
        <header className="sticky top-0 z-50 bg-[#FAF9F5]/90 backdrop-blur-md border-b border-stone-200">
          <div className="max-w-6xl mx-auto px-4 h-16 flex items-center justify-between">
            <Link href="/" className="flex items-center gap-2">
              <span className="font-serif tracking-widest text-xl font-bold text-slate-900">SCENTIQ</span>
              <span className="text-[10px] uppercase tracking-wider px-1.5 py-0.5 rounded bg-amber-100 text-amber-800 font-mono font-medium">Evidence-Led</span>
            </Link>

            <nav className="hidden md:flex items-center gap-6 text-sm font-medium text-slate-700">
              <Link href="/" className="hover:text-slate-900 transition-colors">Discover</Link>
              <Link href="/#catalogue" className="hover:text-slate-900 transition-colors">Catalogue</Link>
              <Link href="/compare" className="hover:text-slate-900 transition-colors">Compare</Link>
              <Link href="/#advisor" className="hover:text-slate-900 transition-colors">Recommendation Engine</Link>
            </nav>

            <div className="flex items-center gap-3">
              <div className="flex items-center gap-1.5 text-xs text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-full border border-emerald-200 font-mono">
                <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse"></span>
                <span>API Ready</span>
              </div>
            </div>
          </div>
        </header>

        <main className="flex-1 max-w-6xl w-full mx-auto px-4 py-8">
          {children}
        </main>

        <footer className="border-t border-stone-200 bg-stone-100/50 py-8 text-xs text-stone-500">
          <div className="max-w-6xl mx-auto px-4 flex flex-col sm:flex-row justify-between items-center gap-4">
            <div>
              <p className="font-semibold text-stone-700">SCENTIQ Decision-Support Platform</p>
              <p>Catalogue before Chatbot • Evidence before Confidence • No Unsupported Clone Guarantees</p>
            </div>
            <p>© 2026 SCENTIQ. Data governance adheres to CC BY 4.0 & DPDP 2023 guidelines.</p>
          </div>
        </footer>
      </body>
    </html>
  );
}
