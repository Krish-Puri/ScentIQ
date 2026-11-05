"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import {
  fetchFragranceDetail,
  fetchAlternatives,
  FragranceDetail,
  AlternativeItem,
} from "@/lib/api";
import { formatCurrencyINR } from "@/lib/utils";
import {
  ArrowLeft,
  ShieldCheck,
  CheckCircle2,
  AlertCircle,
  Tag,
  Layers,
  ArrowRight,
  ExternalLink,
} from "lucide-react";

export default function FragranceDetailPage() {
  const params = useParams();
  const slug = params?.slug as string;

  const [fragrance, setFragrance] = useState<FragranceDetail | null>(null);
  const [alternatives, setAlternatives] = useState<AlternativeItem[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!slug) return;
    fetchFragranceDetail(slug)
      .then((detail) => {
        setFragrance(detail);
        if (detail) {
          return fetchAlternatives(detail.id).then((alts) => setAlternatives(alts));
        }
      })
      .finally(() => setLoading(false));
  }, [slug]);

  if (loading) {
    return <div className="py-20 text-center text-sm text-slate-400">Loading fragrance dossier...</div>;
  }

  if (!fragrance) {
    return (
      <div className="py-20 text-center space-y-4">
        <h2 className="text-xl font-bold text-slate-800">Fragrance Not Found</h2>
        <p className="text-sm text-slate-500">The requested record is either unpublished or does not exist.</p>
        <Link href="/" className="inline-block px-4 py-2 bg-slate-900 text-white rounded text-xs font-medium">
          Return to Catalogue
        </Link>
      </div>
    );
  }

  return (
    <div className="space-y-10">
      {/* Back link */}
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Catalogue</span>
        </Link>
      </div>

      {/* Header Dossier */}
      <section className="bg-white p-6 sm:p-8 rounded-2xl border border-stone-200 shadow-sm space-y-6">
        <div className="flex flex-col sm:flex-row sm:items-start justify-between gap-4 border-b border-stone-100 pb-6">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="text-xs uppercase font-mono tracking-wider text-slate-500">{fragrance.brand_name}</span>
              <span className="text-[10px] px-2 py-0.5 rounded bg-stone-100 text-stone-700 font-mono font-medium">
                {fragrance.concentration}
              </span>
              {fragrance.release_year && (
                <span className="text-[10px] text-slate-400 font-mono">{fragrance.release_year}</span>
              )}
            </div>

            <h1 className="text-3xl sm:text-4xl font-serif font-bold text-slate-900">{fragrance.canonical_name}</h1>
            <p className="text-sm text-slate-600 max-w-2xl">{fragrance.description || "Official catalogue formulation."}</p>
          </div>

          <div className="flex flex-col sm:items-end gap-2 text-xs">
            <div className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200 font-medium">
              <ShieldCheck className="w-4 h-4 text-emerald-600" />
              <span>{fragrance.evidence_count} Verified Claims Attached</span>
            </div>
            {fragrance.perfumer_text && (
              <span className="text-slate-500 text-[11px]">Nose: {fragrance.perfumer_text}</span>
            )}
          </div>
        </div>

        {/* Note Pyramid & Accords */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {/* Note Pyramid */}
          <div className="space-y-4">
            <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider font-mono">
              Note Structure
            </h3>

            <div className="space-y-3 text-xs">
              <div className="p-3 bg-stone-50 rounded-lg border border-stone-100">
                <span className="font-semibold text-slate-700 block mb-1">Top Notes (Opening)</span>
                <p className="text-slate-600">{fragrance.top_notes.join(", ") || "Not officially disclosed"}</p>
              </div>

              <div className="p-3 bg-stone-50 rounded-lg border border-stone-100">
                <span className="font-semibold text-slate-700 block mb-1">Heart Notes (Mid)</span>
                <p className="text-slate-600">{fragrance.heart_notes.join(", ") || "Not officially disclosed"}</p>
              </div>

              <div className="p-3 bg-stone-50 rounded-lg border border-stone-100">
                <span className="font-semibold text-slate-700 block mb-1">Base Notes (Drydown)</span>
                <p className="text-slate-600">{fragrance.base_notes.join(", ") || "Not officially disclosed"}</p>
              </div>
            </div>
          </div>

          {/* Accords & Observed Prices */}
          <div className="space-y-6">
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider font-mono">
                Main Accords
              </h3>
              <div className="flex flex-wrap gap-2">
                {fragrance.accords.map((a, i) => (
                  <span key={i} className="px-3 py-1 bg-amber-50 text-amber-900 border border-amber-200 rounded-md text-xs font-medium">
                    {a}
                  </span>
                ))}
              </div>
            </div>

            {/* Price Listings */}
            <div className="space-y-3">
              <h3 className="text-sm font-semibold text-slate-900 uppercase tracking-wider font-mono">
                Observed Indian Retail Prices (INR)
              </h3>
              {fragrance.prices.length === 0 ? (
                <p className="text-xs text-slate-400 italic">No active retailer observations logged currently.</p>
              ) : (
                <div className="space-y-2">
                  {fragrance.prices.map((p) => (
                    <div key={p.id} className="flex justify-between items-center p-3 bg-white border border-stone-200 rounded-lg text-xs shadow-2xs">
                      <div>
                        <p className="font-medium text-slate-800">{p.seller}</p>
                        <p className="text-[11px] text-slate-500">{p.size_ml} ml {p.price_per_ml && `(₹${p.price_per_ml}/ml)`}</p>
                      </div>
                      <span className="font-bold text-slate-900 text-sm">{formatCurrencyINR(p.price_inr)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      </section>

      {/* Alternative & Clone Intelligence (Section 7, FR-007) */}
      <section className="space-y-6">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-amber-800 uppercase tracking-wider">
            <Tag className="w-3.5 h-3.5" />
            <span>Alternative Intelligence Graph</span>
          </div>
          <h2 className="text-2xl font-serif font-bold text-slate-900 mt-1">
            Credible Alternatives to {fragrance.canonical_name}
          </h2>
          <p className="text-xs text-slate-600">
            Documented market alternatives with strict evidence grades and recorded scent profile differences.
          </p>
        </div>

        {alternatives.length === 0 ? (
          <div className="bg-white p-8 rounded-xl border border-stone-200 text-center space-y-2">
            <AlertCircle className="w-8 h-8 text-stone-400 mx-auto" />
            <h4 className="text-sm font-semibold text-slate-700">No Verified Alternatives Published Yet</h4>
            <p className="text-xs text-slate-500 max-w-md mx-auto">
              SCENTIQ does not publish unverified clone claims. All alternative relationships require dual curator approval and documented scent comparisons.
            </p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
            {alternatives.map((alt) => (
              <div key={alt.id} className="bg-white p-6 rounded-xl border border-stone-200 shadow-sm space-y-4">
                <div className="flex justify-between items-start">
                  <div>
                    <span className="text-[10px] uppercase font-mono text-slate-500">{alt.candidate_brand}</span>
                    <h3 className="font-serif font-bold text-slate-900 text-lg">{alt.candidate_name}</h3>
                    <span className="text-xs text-slate-500">{alt.candidate_concentration}</span>
                  </div>

                  <div className="text-right space-y-1">
                    <span className={`inline-block px-2 py-0.5 rounded text-[10px] font-mono font-semibold border ${
                      alt.evidence_grade === "A_STRONG"
                        ? "bg-emerald-50 text-emerald-800 border-emerald-200"
                        : alt.evidence_grade === "B_SUPPORTED"
                        ? "bg-blue-50 text-blue-800 border-blue-200"
                        : "bg-stone-100 text-stone-700 border-stone-200"
                    }`}>
                      {alt.evidence_grade.replace("_", " ")}
                    </span>
                    {alt.candidate_indicative_price_inr && (
                      <p className="text-xs font-bold text-slate-800">{formatCurrencyINR(alt.candidate_indicative_price_inr)}</p>
                    )}
                  </div>
                </div>

                <div className="text-xs space-y-2">
                  <div className="p-2.5 bg-stone-50 rounded border border-stone-100">
                    <span className="font-semibold text-slate-700 block mb-0.5">Relationship Type:</span>
                    <span className="text-slate-600 font-mono text-[11px]">{alt.relationship_type.replace(/_/g, " ")}</span>
                  </div>

                  {alt.rationale && (
                    <div className="p-2.5 bg-stone-50 rounded border border-stone-100">
                      <span className="font-semibold text-slate-700 block mb-0.5">Editorial Consensus:</span>
                      <p className="text-slate-600 leading-relaxed">{alt.rationale}</p>
                    </div>
                  )}

                  {alt.known_differences && (
                    <div className="p-2.5 bg-amber-50/60 rounded border border-amber-100">
                      <span className="font-semibold text-amber-900 block mb-0.5">Known Profile Differences:</span>
                      <p className="text-amber-800 leading-relaxed">{alt.known_differences}</p>
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

