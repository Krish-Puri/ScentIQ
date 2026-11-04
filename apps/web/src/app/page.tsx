"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { fetchFragrances, requestRecommendations, FragranceSummary, RecommendationCard } from "@/lib/api";
import { formatCurrencyINR } from "@/lib/utils";
import { Search, Sparkles, ShieldCheck, ArrowRight, Layers, SlidersHorizontal } from "lucide-react";

export default function HomePage() {
  const [fragrances, setFragrances] = useState<FragranceSummary[]>([]);
  const [recommendations, setRecommendations] = useState<RecommendationCard[]>([]);
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(true);
  const [recLoading, setRecLoading] = useState(false);

  // Preference quiz state
  const [preferredFamily, setPreferredFamily] = useState<string>("Woody Citrus");
  const [maxBudget, setMaxBudget] = useState<number>(15000);
  const [avoidTerm, setAvoidTerm] = useState<string>("");

  useEffect(() => {
    fetchFragrances()
      .then((data) => setFragrances(data))
      .finally(() => setLoading(false));
  }, []);

  const handleRecommend = async () => {
    setRecLoading(true);
    try {
      const results = await requestRecommendations({
        liked_families: [preferredFamily],
        budget_max_inr: maxBudget,
        avoid_terms: avoidTerm ? [avoidTerm] : [],
        hard_budget_limit: true,
      });
      setRecommendations(results);
    } catch (e) {
      console.error(e);
    } finally {
      setRecLoading(false);
    }
  };

  const filteredFragrances = fragrances.filter((f) =>
    searchQuery
      ? f.canonical_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        f.brand_name.toLowerCase().includes(searchQuery.toLowerCase()) ||
        (f.family && f.family.toLowerCase().includes(searchQuery.toLowerCase()))
      : true
  );

  return (
    <div className="space-y-16">
      {/* Hero Section */}
      <section className="text-center max-w-3xl mx-auto space-y-4 pt-6">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-50 border border-amber-200 text-amber-900 text-xs font-medium">
          <ShieldCheck className="w-3.5 h-3.5 text-amber-700" />
          <span>Transparent Provenance • No Invented Clone Percentages</span>
        </div>

        <h1 className="text-4xl sm:text-5xl font-serif font-bold text-slate-900 tracking-tight leading-tight">
          Personalised fragrance intelligence, backed by verified evidence.
        </h1>

        <p className="text-slate-600 text-base sm:text-lg leading-relaxed">
          Discover fragrances tailored to your climate and taste, compare designer icons with honest alternatives, and decode scent notes without retail marketing hype.
        </p>

        {/* Quick Search */}
        <div className="pt-4 max-w-xl mx-auto">
          <div className="relative">
            <Search className="absolute left-3.5 top-3.5 w-4 h-4 text-slate-400" />
            <input
              type="text"
              placeholder="Search reference fragrances, houses, or notes (e.g., Aventus, Chanel, Bergamot)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full pl-10 pr-4 py-3 bg-white border border-stone-300 rounded-lg text-sm shadow-sm focus:outline-none focus:ring-2 focus:ring-slate-800 transition"
            />
          </div>
        </div>
      </section>

      {/* Trust & Methodology Principles */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-6 bg-white p-6 rounded-xl border border-stone-200 shadow-sm">
        <div className="space-y-2">
          <div className="w-8 h-8 rounded-lg bg-amber-100 flex items-center justify-center text-amber-800 font-semibold text-sm">
            1
          </div>
          <h3 className="font-semibold text-slate-900 text-base">Catalogue Before Chatbot</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Recommendations are strictly grounded in governed, verified fragrance records. No LLM hallucinations or fabricated bottles.
          </p>
        </div>

        <div className="space-y-2">
          <div className="w-8 h-8 rounded-lg bg-emerald-100 flex items-center justify-center text-emerald-800 font-semibold text-sm">
            2
          </div>
          <h3 className="font-semibold text-slate-900 text-base">Evidence-Graded Alternatives</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Directional relationships explicitly graded: <span className="font-semibold text-emerald-800">Grade A</span> (Brand claim), <span className="font-semibold text-blue-800">Grade B</span> (Supported community consensus), <span className="font-semibold text-stone-600">Grade C</span> (Provisional).
          </p>
        </div>

        <div className="space-y-2">
          <div className="w-8 h-8 rounded-lg bg-purple-100 flex items-center justify-center text-purple-800 font-semibold text-sm">
            3
          </div>
          <h3 className="font-semibold text-slate-900 text-base">Indian Buying Context</h3>
          <p className="text-xs text-slate-600 leading-relaxed">
            Dated INR price observations, size-normalised cost-per-ml, and high-heat climate suitability notes without false longevity promises.
          </p>
        </div>
      </section>

      {/* Interactive Recommendation Engine Demo (Section 12.3) */}
      <section id="advisor" className="bg-[#F4F1EA] p-6 sm:p-8 rounded-2xl border border-stone-300 space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 text-xs font-mono text-amber-800 uppercase tracking-wider">
              <Sparkles className="w-3.5 h-3.5" />
              <span>Deterministic Recommendation Engine (v1.0)</span>
            </div>
            <h2 className="text-2xl font-serif font-bold text-slate-900 mt-1">Guided Preference Shortlist</h2>
            <p className="text-xs text-slate-600">Scores candidates using multi-factor profile matching with strict exclusion guarantees.</p>
          </div>

          <button
            onClick={handleRecommend}
            disabled={recLoading}
            className="inline-flex items-center justify-center gap-2 px-5 py-2.5 bg-slate-900 text-white rounded-lg text-sm font-medium hover:bg-slate-800 transition disabled:opacity-50"
          >
            {recLoading ? "Scoring Catalogue..." : "Generate Recommendations"}
            <ArrowRight className="w-4 h-4" />
          </button>
        </div>

        {/* Constraints controls */}
        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-2">
          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Preferred Scent Family</label>
            <select
              value={preferredFamily}
              onChange={(e) => setPreferredFamily(e.target.value)}
              className="w-full text-xs p-2.5 bg-white border border-stone-300 rounded-md shadow-sm"
            >
              <option value="Woody Citrus">Woody Citrus (Fresh / Versatile)</option>
              <option value="Fruity Chypre">Fruity Chypre (Smoky / Distinctive)</option>
              <option value="Aquatic Aromatic">Aquatic Aromatic (High-Heat / Marine)</option>
              <option value="Amber Woody">Amber Woody (Warm / Evening)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Maximum Budget (INR)</label>
            <select
              value={maxBudget}
              onChange={(e) => setMaxBudget(Number(e.target.value))}
              className="w-full text-xs p-2.5 bg-white border border-stone-300 rounded-md shadow-sm"
            >
              <option value={3000}>Under ₹3,000 (Value & Alternatives)</option>
              <option value={6000}>Under ₹6,000 (Mid-Range & Middle Eastern)</option>
              <option value={15000}>Under ₹15,000 (Designer & Luxury)</option>
              <option value={40000}>Any Budget (Include Niche)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-semibold text-slate-700 mb-1">Strict Avoid Term (Hard Filter)</label>
            <input
              type="text"
              placeholder="e.g. Vanilla, Oud, Lemon..."
              value={avoidTerm}
              onChange={(e) => setAvoidTerm(e.target.value)}
              className="w-full text-xs p-2 bg-white border border-stone-300 rounded-md shadow-sm"
            />
          </div>
        </div>

        {/* Results grid */}
        {recommendations.length > 0 && (
          <div className="space-y-4 pt-4 border-t border-stone-300">
            <h3 className="text-sm font-semibold text-slate-800">Top Explainable Matches:</h3>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {recommendations.map((rec) => (
                <div key={rec.fragrance_id} className="bg-white p-5 rounded-xl border border-stone-200 shadow-sm space-y-3">
                  <div className="flex justify-between items-start">
                    <div>
                      <span className="text-[10px] uppercase font-mono tracking-wider text-slate-500">{rec.brand_name}</span>
                      <h4 className="font-serif font-bold text-slate-900 text-lg">{rec.canonical_name}</h4>
                      <span className="text-xs text-slate-500">{rec.concentration} • {rec.family}</span>
                    </div>
                    <div className="text-right">
                      <span className="inline-block px-2 py-0.5 rounded bg-emerald-50 text-emerald-800 text-xs font-mono font-semibold border border-emerald-200">
                        Score: {(rec.score * 100).toFixed(0)}%
                      </span>
                      {rec.indicative_price_inr && (
                        <p className="text-xs font-medium text-slate-700 mt-1">{formatCurrencyINR(rec.indicative_price_inr)}</p>
                      )}
                    </div>
                  </div>

                  <p className="text-xs text-slate-600 italic bg-stone-50 p-2.5 rounded border border-stone-100">
                    "{rec.fit_summary}"
                  </p>

                  <div className="flex flex-wrap gap-1.5">
                    {rec.profile_match_cues.map((cue, i) => (
                      <span key={i} className="text-[10px] bg-slate-100 text-slate-700 px-2 py-0.5 rounded">
                        ✓ {cue}
                      </span>
                    ))}
                  </div>

                  {rec.sample_first_recommended && (
                    <div className="text-[11px] text-amber-800 bg-amber-50 px-2.5 py-1.5 rounded border border-amber-200">
                      💡 <strong>Sample first advice:</strong> Higher profile uncertainty detected; sampling a 5ml decant is recommended before blind buying.
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}
      </section>

      {/* Verified Catalogue Section */}
      <section id="catalogue" className="space-y-6">
        <div className="flex justify-between items-end">
          <div>
            <h2 className="text-2xl font-serif font-bold text-slate-900">Verified Catalogue</h2>
            <p className="text-xs text-slate-500">Documented brand records and evidence-backed relationships.</p>
          </div>
          <span className="text-xs text-slate-400 font-mono">{filteredFragrances.length} records active</span>
        </div>

        {loading ? (
          <div className="py-12 text-center text-sm text-slate-400">Loading catalogue...</div>
        ) : (
          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-6">
            {filteredFragrances.map((f) => (
              <Link
                key={f.id}
                href={`/fragrances/${f.slug}`}
                className="group bg-white p-5 rounded-xl border border-stone-200 shadow-sm hover:shadow-md hover:border-slate-400 transition flex flex-col justify-between"
              >
                <div className="space-y-2">
                  <div className="flex justify-between items-center text-xs text-slate-400 font-mono">
                    <span>{f.brand_name}</span>
                    <span className="px-1.5 py-0.5 bg-stone-100 text-slate-700 rounded text-[10px]">{f.concentration}</span>
                  </div>

                  <h3 className="font-serif font-bold text-slate-900 text-lg group-hover:text-amber-900 transition">
                    {f.canonical_name}
                  </h3>

                  <p className="text-xs text-slate-500 line-clamp-2">{f.description || "Verified fragrance profile."}</p>
                </div>

                <div className="pt-4 mt-4 border-t border-stone-100 flex justify-between items-center text-xs">
                  <span className="text-slate-600 font-medium">{f.family || "Classic"}</span>
                  <span className="inline-flex items-center gap-1 text-amber-800 font-medium group-hover:translate-x-0.5 transition">
                    View & Alternatives <ArrowRight className="w-3.5 h-3.5" />
                  </span>
                </div>
              </Link>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
