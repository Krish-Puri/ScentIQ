"use client";

import { useEffect, useState } from "react";
import { fetchFragrances, FragranceSummary } from "@/lib/api";
import { formatCurrencyINR } from "@/lib/utils";
import { Layers, ShieldCheck, AlertCircle, ArrowLeft } from "lucide-react";
import Link from "next/link";

interface ComparisonItem {
  id: string;
  canonical_name: string;
  brand_name: string;
  concentration: string;
  family?: string;
  top_notes: string[];
  heart_notes: string[];
  base_notes: string[];
  accords: string[];
  indicative_price_inr?: number;
  size_ml?: number;
  price_per_ml?: number;
  has_full_pyramid_data: boolean;
  evidence_count: number;
}

export default function ComparePage() {
  const [catalog, setCatalog] = useState<FragranceSummary[]>([]);
  const [selectedIds, setSelectedIds] = useState<string[]>([]);
  const [comparisonData, setComparisonData] = useState<{
    items: ComparisonItem[];
    shared_notes: string[];
    shared_accords: string[];
    distinguishing_notes: string[];
    missing_data_disclosures: string[];
  } | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    fetchFragrances().then((items) => {
      setCatalog(items);
      // Auto-select first two if available
      if (items.length >= 2) {
        setSelectedIds([items[0].id, items[1].id]);
      }
    });
  }, []);

  useEffect(() => {
    if (selectedIds.length < 2) {
      setComparisonData(null);
      return;
    }

    setLoading(true);
    fetch("http://localhost:8000/api/v1/comparisons", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ fragrance_ids: selectedIds }),
    })
      .then((res) => res.json())
      .then((json) => {
        if (json.data) setComparisonData(json.data);
      })
      .catch((e) => console.error(e))
      .finally(() => setLoading(false));
  }, [selectedIds]);

  const toggleSelect = (id: string) => {
    if (selectedIds.includes(id)) {
      if (selectedIds.length > 2) {
        setSelectedIds(selectedIds.filter((i) => i !== id));
      }
    } else {
      if (selectedIds.length < 3) {
        setSelectedIds([...selectedIds, id]);
      } else {
        setSelectedIds([selectedIds[0], selectedIds[1], id]);
      }
    }
  };

  return (
    <div className="space-y-8">
      <div>
        <Link href="/" className="inline-flex items-center gap-1.5 text-xs text-slate-500 hover:text-slate-800 transition">
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to Catalogue</span>
        </Link>
      </div>

      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-xs font-mono text-amber-800 uppercase tracking-wider">
            <Layers className="w-3.5 h-3.5" />
            <span>Side-by-Side Scent Analysis (FR-008)</span>
          </div>
          <h1 className="text-3xl font-serif font-bold text-slate-900 mt-1">Fragrance Comparison</h1>
          <p className="text-xs text-slate-600">Select 2 to 3 fragrances to inspect overlapping notes, structural differences, and price per ml.</p>
        </div>
      </div>

      {/* Fragrance Selector Chips */}
      <div className="bg-white p-4 rounded-xl border border-stone-200 space-y-2">
        <label className="text-xs font-semibold text-slate-700 block">Select Fragrances to Compare (2–3):</label>
        <div className="flex flex-wrap gap-2">
          {catalog.map((f) => {
            const isSelected = selectedIds.includes(f.id);
            return (
              <button
                key={f.id}
                onClick={() => toggleSelect(f.id)}
                className={`text-xs px-3 py-1.5 rounded-lg border transition font-medium ${
                  isSelected
                    ? "bg-slate-900 text-white border-slate-900 shadow-sm"
                    : "bg-stone-50 text-slate-700 border-stone-200 hover:bg-stone-100"
                }`}
              >
                {isSelected ? "✓ " : "+ "} {f.canonical_name} ({f.brand_name})
              </button>
            );
          })}
        </div>
      </div>

      {/* Comparison Grid */}
      {loading ? (
        <div className="py-20 text-center text-sm text-slate-400">Computing notes and accord overlap...</div>
      ) : !comparisonData ? (
        <div className="py-12 text-center text-sm text-slate-400">Select at least 2 fragrances to compare.</div>
      ) : (
        <div className="space-y-6">
          {/* Overlap Summary Box */}
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 bg-amber-50/70 p-5 rounded-xl border border-amber-200 text-xs">
            <div>
              <span className="font-semibold text-amber-900 block mb-1">Shared Notes Overlap:</span>
              <p className="text-amber-800 font-mono">
                {comparisonData.shared_notes.length > 0 ? comparisonData.shared_notes.join(", ") : "No direct shared notes"}
              </p>
            </div>

            <div>
              <span className="font-semibold text-amber-900 block mb-1">Shared Accords:</span>
              <p className="text-amber-800 font-mono">
                {comparisonData.shared_accords.length > 0 ? comparisonData.shared_accords.join(", ") : "No identical accords"}
              </p>
            </div>

            <div>
              <span className="font-semibold text-amber-900 block mb-1">Key Distinguishing Notes:</span>
              <p className="text-amber-800 font-mono">
                {comparisonData.distinguishing_notes.slice(0, 5).join(", ")}
              </p>
            </div>
          </div>

          {/* Side by side columns */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {comparisonData.items.map((item) => (
              <div key={item.id} className="bg-white p-6 rounded-xl border border-stone-200 shadow-sm space-y-5">
                <div className="border-b border-stone-100 pb-4">
                  <span className="text-[10px] uppercase font-mono text-slate-400">{item.brand_name}</span>
                  <h3 className="font-serif font-bold text-slate-900 text-xl">{item.canonical_name}</h3>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs px-2 py-0.5 rounded bg-stone-100 text-slate-700 font-mono">
                      {item.concentration}
                    </span>
                    <span className="text-xs text-slate-500">{item.family}</span>
                  </div>
                </div>

                {/* Price & Value */}
                <div className="p-3 bg-stone-50 rounded-lg border border-stone-100 text-xs space-y-1">
                  <span className="text-slate-500 font-semibold block">Indian Price & Value:</span>
                  {item.indicative_price_inr ? (
                    <div className="flex justify-between items-baseline">
                      <span className="font-bold text-slate-900 text-base">{formatCurrencyINR(item.indicative_price_inr)}</span>
                      {item.price_per_ml && (
                        <span className="text-slate-500 font-mono text-[11px]">₹{item.price_per_ml}/ml ({item.size_ml}ml)</span>
                      )}
                    </div>
                  ) : (
                    <span className="text-slate-400 italic">No price listing recorded</span>
                  )}
                </div>

                {/* Notes breakdown */}
                <div className="space-y-3 text-xs">
                  <div>
                    <span className="font-semibold text-slate-700 block mb-0.5">Top Notes:</span>
                    <p className="text-slate-600 font-mono text-[11px]">{item.top_notes.join(", ") || "—"}</p>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-700 block mb-0.5">Heart Notes:</span>
                    <p className="text-slate-600 font-mono text-[11px]">{item.heart_notes.join(", ") || "—"}</p>
                  </div>

                  <div>
                    <span className="font-semibold text-slate-700 block mb-0.5">Base Notes:</span>
                    <p className="text-slate-600 font-mono text-[11px]">{item.base_notes.join(", ") || "—"}</p>
                  </div>
                </div>

                {/* Accords */}
                <div className="pt-2">
                  <span className="text-xs font-semibold text-slate-700 block mb-1.5">Dominant Accords:</span>
                  <div className="flex flex-wrap gap-1.5">
                    {item.accords.map((a, i) => (
                      <span key={i} className="text-[10px] px-2 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-200">
                        {a}
                      </span>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* Missing data disclosures & trust notice */}
          {comparisonData.missing_data_disclosures.length > 0 && (
            <div className="p-4 bg-stone-100 rounded-lg text-xs text-stone-600 space-y-1">
              <span className="font-semibold text-stone-800 block">Data Disclosures:</span>
              <ul className="list-disc list-inside space-y-0.5">
                {comparisonData.missing_data_disclosures.map((d, i) => (
                  <li key={i}>{d}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

