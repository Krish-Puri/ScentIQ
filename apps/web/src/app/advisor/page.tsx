"use client";

import { useState } from "react";
import Link from "next/link";
import {
  recommendWithAdvisor,
  AdvisorRecommendResponse,
  RecommendationCard,
} from "@/lib/api";

const PROMPT_SUGGESTIONS = [
  "I want a fresh, slightly woody perfume for office use. My budget is ₹2,500. I don't like overly sweet fragrances.",
  "Looking for a rich amber vanilla scent for date night under ₹6,000. Avoid powdery accords.",
  "Crisp citrus and aquatic fragrance for hot Indian summer under ₹3,500.",
  "Sophisticated cedarwood and cardamom EDP for formal evening events.",
];

export default function AIAdvisorPage() {
  const [query, setQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<AdvisorRecommendResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [includeProfile, setIncludeProfile] = useState(true);

  const handleSubmit = async (userQuery?: string) => {
    const q = userQuery || query;
    if (!q.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const res = await recommendWithAdvisor(q, includeProfile);
      setResponse(res);
    } catch (err: any) {
      setError(err.message || "Failed to process query with advisor");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 py-2">
      {/* Editorial Header */}
      <div className="text-center max-w-2xl mx-auto space-y-3">
        <div className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-amber-100 text-amber-900 text-xs font-mono font-medium">
          <span>Bounded AI Advisor • EPIC-11</span>
        </div>
        <h1 className="font-serif text-3xl sm:text-4xl font-bold text-slate-900 tracking-tight">
          Natural Language Fragrance Advisor
        </h1>
        <p className="text-sm text-stone-600">
          Describe what you are looking for in plain language. Our advisor translates your message into validated constraints, merges them with your profile, and ranks catalogue fragrances using our deterministic engine.
        </p>
      </div>

      {/* Input box */}
      <div className="bg-white border border-stone-200 rounded-xl p-5 sm:p-6 shadow-sm">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSubmit();
          }}
          className="space-y-4"
        >
          <div className="relative">
            <textarea
              rows={3}
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="e.g. I want a fresh, slightly woody perfume for office use. My budget is ₹2,500. I don't like overly sweet fragrances..."
              className="w-full p-4 text-sm border border-stone-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-amber-500 placeholder:text-stone-400"
            />
          </div>

          <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-3">
            <label className="flex items-center gap-2 text-xs text-stone-600 cursor-pointer">
              <input
                type="checkbox"
                checked={includeProfile}
                onChange={(e) => setIncludeProfile(e.target.checked)}
                className="rounded text-amber-600 focus:ring-amber-500"
              />
              <span>Merge with my stored personal profile (hard exclusions & budget limits)</span>
            </label>

            <button
              type="submit"
              disabled={loading || !query.trim()}
              className="px-6 py-2.5 bg-slate-900 hover:bg-slate-800 text-white rounded-lg text-sm font-medium transition-colors disabled:opacity-50"
            >
              {loading ? "Analyzing Constraints..." : "Ask Advisor →"}
            </button>
          </div>
        </form>

        {/* Suggestion Chips */}
        <div className="mt-4 pt-4 border-t border-stone-100">
          <span className="text-xs font-mono uppercase tracking-wider text-stone-400 block mb-2">
            Example Queries
          </span>
          <div className="flex flex-wrap gap-2">
            {PROMPT_SUGGESTIONS.map((suggestion, idx) => (
              <button
                key={idx}
                type="button"
                onClick={() => {
                  setQuery(suggestion);
                  handleSubmit(suggestion);
                }}
                className="text-left text-xs bg-stone-50 hover:bg-stone-100 border border-stone-200 text-stone-700 px-3 py-1.5 rounded-full transition-colors"
              >
                "{suggestion.slice(0, 45)}..."
              </button>
            ))}
          </div>
        </div>
      </div>

      {error && (
        <div className="p-4 bg-rose-50 border border-rose-200 text-rose-800 text-sm rounded-lg">
          {error}
        </div>
      )}

      {/* Results View */}
      {response && (
        <div className="space-y-6">
          {/* Parsed Intent Visualizer */}
          <div className="bg-amber-50/60 border border-amber-200/80 rounded-lg p-5">
            <div className="flex items-center justify-between mb-3">
              <span className="text-xs font-mono uppercase tracking-wider text-amber-900 font-bold">
                Extracted Structured Constraints (Validation Pipeline)
              </span>
              <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-200 text-amber-900">
                via {response.parsed_intent.parsed_via}
              </span>
            </div>

            <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
              <div className="bg-white/80 p-2.5 rounded border border-amber-200/60">
                <span className="text-stone-400 block mb-0.5">Budget Ceiling</span>
                <span className="font-mono font-bold text-slate-900">
                  {response.parsed_intent.budget_max
                    ? `₹${response.parsed_intent.budget_max.toLocaleString("en-IN")}`
                    : "No Limit"}
                </span>
              </div>
              <div className="bg-white/80 p-2.5 rounded border border-amber-200/60">
                <span className="text-stone-400 block mb-0.5">Accords / Families</span>
                <span className="font-medium text-slate-800">
                  {[...response.parsed_intent.preferred_families, ...response.parsed_intent.preferred_accords].join(", ") || "None"}
                </span>
              </div>
              <div className="bg-white/80 p-2.5 rounded border border-amber-200/60">
                <span className="text-stone-400 block mb-0.5">Strict Exclusions</span>
                <span className="font-medium text-rose-700">
                  {response.applied_avoid_terms.join(", ") || "None"}
                </span>
              </div>
              <div className="bg-white/80 p-2.5 rounded border border-amber-200/60">
                <span className="text-stone-400 block mb-0.5">Occasion</span>
                <span className="font-medium text-slate-800">
                  {response.parsed_intent.occasions.join(", ") || "Any"}
                </span>
              </div>
            </div>
          </div>

          {/* Grounded Narrative Explanation */}
          <div className="bg-white border-l-4 border-amber-500 border border-stone-200 p-5 rounded-r-lg shadow-sm">
            <div className="text-xs font-mono uppercase tracking-wider text-amber-800 font-bold mb-1">
              Grounded Advisor Rationale
            </div>
            <p className="text-sm text-stone-700 leading-relaxed">
              {response.explanation}
            </p>
          </div>

          {/* Ranked Fragrance Cards */}
          <div>
            <h2 className="font-serif text-2xl font-bold text-slate-900 mb-4">
              Ranked Catalogue Matches ({response.recommendations.length})
            </h2>

            {response.recommendations.length === 0 ? (
              <div className="bg-white border border-stone-200 p-8 rounded-lg text-center text-stone-500 text-sm">
                No published fragrances meet these strict constraints and budget limits. Try broadening your budget or relaxing note exclusions.
              </div>
            ) : (
              <div className="grid md:grid-cols-2 gap-4">
                {response.recommendations.map((card, idx) => (
                  <div
                    key={card.fragrance_id}
                    className="bg-white border border-stone-200 rounded-lg p-5 shadow-sm hover:border-amber-400 transition-all flex flex-col justify-between"
                  >
                    <div>
                      <div className="flex items-start justify-between gap-2 mb-2">
                        <div>
                          <div className="text-xs font-mono uppercase text-stone-400">{card.brand_name}</div>
                          <Link
                            href={`/fragrances/${card.canonical_name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                            className="font-serif text-lg font-bold text-slate-900 hover:text-amber-800 transition-colors"
                          >
                            {card.canonical_name}
                          </Link>
                          <div className="text-xs text-stone-500">{card.concentration} • {card.family || "Fragrance"}</div>
                        </div>

                        <div className="text-right">
                          <div className="text-xs font-mono text-stone-400">Match Fit</div>
                          <div className="font-mono text-lg font-bold text-amber-700">
                            {(card.score * 100).toFixed(0)}%
                          </div>
                        </div>
                      </div>

                      <p className="text-xs text-stone-600 mb-3">{card.fit_summary}</p>

                      <div className="space-y-1 mb-4">
                        {card.profile_match_cues.map((cue, i) => (
                          <div key={i} className="text-[11px] text-emerald-800 flex items-center gap-1.5">
                            <span className="text-emerald-500">✓</span>
                            <span>{cue}</span>
                          </div>
                        ))}
                        {card.tradeoffs_or_caveats.map((cav, i) => (
                          <div key={i} className="text-[11px] text-amber-800 flex items-center gap-1.5">
                            <span className="text-amber-500">⚠</span>
                            <span>{cav}</span>
                          </div>
                        ))}
                      </div>
                    </div>

                    <div className="pt-3 border-t border-stone-100 flex items-center justify-between text-xs">
                      <div>
                        {card.indicative_price_inr ? (
                          <span className="font-mono font-bold text-slate-900">
                            ₹{card.indicative_price_inr.toLocaleString("en-IN")}
                          </span>
                        ) : (
                          <span className="text-stone-400">Price unavailable</span>
                        )}
                        {card.sample_first_recommended && (
                          <span className="ml-2 text-[10px] bg-amber-100 text-amber-800 px-1.5 py-0.5 rounded font-mono">
                            Sample First
                          </span>
                        )}
                      </div>

                      <Link
                        href={`/fragrances/${card.canonical_name.toLowerCase().replace(/[^a-z0-9]+/g, "-")}`}
                        className="text-stone-900 font-medium hover:underline text-xs"
                      >
                        Inspect Details →
                      </Link>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
