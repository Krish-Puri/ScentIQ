"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import {
  fetchFragrances,
  submitOnboarding,
  getStoredToken,
  registerUser,
  FragranceSummary,
} from "@/lib/api";

const FAMILIARITY_OPTIONS = [
  { id: "new", title: "New to Fragrances", desc: "Just starting my journey and exploring what scent profiles I enjoy." },
  { id: "casual", title: "Casual User", desc: "Wear fragrances regularly for work, social outings, or special occasions." },
  { id: "enthusiast", title: "Fragrance Enthusiast", desc: "Deeply interested in notes, pyramids, niche houses and accords." },
  { id: "collector", title: "Dedicated Collector", desc: "Extensive wardrobe, active in fragrance communities, seeking rare profiles." },
];

const SCENT_FAMILIES = [
  "Fresh", "Citrus", "Aquatic", "Woody", "Aromatic", "Musky",
  "Amber", "Spicy", "Floral", "Gourmand", "Leather", "Oud"
];

const COMMON_NOTES = [
  "Bergamot", "Cedarwood", "Vanilla", "Sandalwood", "Lavender",
  "Vetiver", "Rose", "Cardamom", "Patchouli", "Neroli", "Tobacco", "Leather"
];

const OCCASIONS = [
  { id: "office", label: "Office & Professional" },
  { id: "casual", label: "Daily Casual" },
  { id: "date", label: "Evening & Date Night" },
  { id: "party", label: "Party & Festive" },
  { id: "summer", label: "Summer & High Heat" },
  { id: "winter", label: "Winter & Cool Weather" },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Form states
  const [familiarity, setFamiliarity] = useState<string>("casual");
  const [selectedFamilies, setSelectedFamilies] = useState<string[]>(["Fresh", "Woody"]);
  const [notePreferences, setNotePreferences] = useState<Record<string, "like" | "dislike" | "neutral">>({});
  
  // Search & known fragrances
  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<FragranceSummary[]>([]);
  const [knownFragrances, setKnownFragrances] = useState<Array<{ id: string; name: string; brand: string; pref: string }>>([]);

  // Usage preferences
  const [selectedOccasions, setSelectedOccasions] = useState<string[]>(["office", "casual"]);
  const [budgetMax, setBudgetMax] = useState<number>(4500);
  const [concentration, setConcentration] = useState<string[]>(["EDP"]);
  const [longevity, setLongevity] = useState<string>("long_lasting");
  const [avoidInput, setAvoidInput] = useState("");
  const [avoidTerms, setAvoidTerms] = useState<string[]>([]);

  // Auth state if not logged in
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");

  useEffect(() => {
    if (searchQuery.trim().length >= 2) {
      const timer = setTimeout(() => {
        fetchFragrances(searchQuery).then(setSearchResults);
      }, 300);
      return () => clearTimeout(timer);
    } else {
      setSearchResults([]);
    }
  }, [searchQuery]);

  const toggleFamily = (family: string) => {
    setSelectedFamilies((prev) =>
      prev.includes(family) ? prev.filter((f) => f !== family) : [...prev, family]
    );
  };

  const setNoteState = (note: string, state: "like" | "dislike" | "neutral") => {
    setNotePreferences((prev) => ({ ...prev, [note]: state }));
  };

  const addKnownFragrance = (frag: FragranceSummary, pref: string) => {
    setKnownFragrances((prev) => [
      ...prev.filter((item) => item.id !== frag.id),
      { id: frag.id, name: frag.canonical_name, brand: frag.brand_name, pref },
    ]);
  };

  const removeKnownFragrance = (id: string) => {
    setKnownFragrances((prev) => prev.filter((item) => item.id !== id));
  };

  const addAvoidTerm = () => {
    if (avoidInput.trim() && !avoidTerms.includes(avoidInput.trim())) {
      setAvoidTerms((prev) => [...prev, avoidInput.trim()]);
      setAvoidInput("");
    }
  };

  const removeAvoidTerm = (term: string) => {
    setAvoidTerms((prev) => prev.filter((t) => t !== term));
  };

  const handleFinish = async () => {
    setSubmitting(true);
    setError(null);
    try {
      // Ensure user has authentication token
      let token = getStoredToken();
      if (!token) {
        // Auto-register or create session
        const email = authEmail || `guest_${Date.now()}@scentiq.local`;
        const pwd = authPassword || "SecureGuestPass123";
        await registerUser(email, pwd);
      }

      const likedNotes = Object.entries(notePreferences)
        .filter(([_, v]) => v === "like")
        .map(([k]) => k);
      const dislikedNotes = Object.entries(notePreferences)
        .filter(([_, v]) => v === "dislike")
        .map(([k]) => k);

      const payload = {
        familiarity_level: familiarity,
        preferred_families: selectedFamilies,
        liked_notes: likedNotes,
        disliked_notes: dislikedNotes,
        liked_accords: selectedFamilies,
        disliked_accords: [],
        known_fragrances: knownFragrances.map((f) => ({
          fragrance_id: f.id,
          preference: f.pref.toUpperCase(),
        })),
        occasions: selectedOccasions,
        budget_min: 0,
        budget_max: budgetMax || 5000,
        preferred_concentrations: concentration,
        longevity_preference: longevity,
        projection_preference: "moderate",
        climate_context: ["subtropical", "humid"],
        avoid_terms: avoidTerms,
      };

      await submitOnboarding(payload);
      router.push("/profile");
    } catch (err: any) {
      setError(err.message || "Failed to save onboarding profile");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto py-4">
      {/* Progress header */}
      <div className="mb-8">
        <div className="flex items-center justify-between text-xs font-mono uppercase tracking-wider text-stone-500 mb-2">
          <span>Personal Fragrance Profile — Step {step} of 6</span>
          <span>{Math.round((step / 6) * 100)}% Complete</span>
        </div>
        <div className="w-full bg-stone-200 h-1.5 rounded-full overflow-hidden">
          <div
            className="bg-amber-600 h-full transition-all duration-300 ease-out"
            style={{ width: `${(step / 6) * 100}%` }}
          />
        </div>
      </div>

      {error && (
        <div className="mb-6 p-3 bg-rose-50 border border-rose-200 text-rose-700 text-sm rounded-md">
          {error}
        </div>
      )}

      {/* Step 1: Familiarity */}
      {step === 1 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">How familiar are you with fragrances?</h2>
          <p className="text-sm text-stone-600 mb-6">
            This calibrates our recommendations to your level of experience without making demographic assumptions.
          </p>
          <div className="grid sm:grid-cols-2 gap-4">
            {FAMILIARITY_OPTIONS.map((opt) => (
              <button
                key={opt.id}
                type="button"
                onClick={() => setFamiliarity(opt.id)}
                className={`text-left p-4 rounded-lg border transition-all ${
                  familiarity === opt.id
                    ? "border-amber-600 bg-amber-50/50 shadow-sm"
                    : "border-stone-200 hover:border-stone-300"
                }`}
              >
                <div className="font-semibold text-slate-900 mb-1">{opt.title}</div>
                <div className="text-xs text-stone-600">{opt.desc}</div>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Step 2: Scent Families */}
      {step === 2 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Which scent families do you gravitate toward?</h2>
          <p className="text-sm text-stone-600 mb-6">
            Select one or more olfactory families from our verified taxonomy.
          </p>
          <div className="flex flex-wrap gap-2.5">
            {SCENT_FAMILIES.map((family) => {
              const selected = selectedFamilies.includes(family);
              return (
                <button
                  key={family}
                  type="button"
                  onClick={() => toggleFamily(family)}
                  className={`px-4 py-2 rounded-full text-sm font-medium transition-all ${
                    selected
                      ? "bg-slate-900 text-white shadow-sm"
                      : "bg-stone-100 hover:bg-stone-200 text-stone-700"
                  }`}
                >
                  {family} {selected && "✓"}
                </button>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 3: Preferred Notes */}
      {step === 3 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Note Preferences</h2>
          <p className="text-sm text-stone-600 mb-6">
            Mark notes you love or prefer to avoid. Disliked notes become strict exclusion criteria.
          </p>
          <div className="grid sm:grid-cols-2 gap-3">
            {COMMON_NOTES.map((note) => {
              const current = notePreferences[note] || "neutral";
              return (
                <div
                  key={note}
                  className="flex items-center justify-between p-3 rounded-md border border-stone-100 bg-stone-50/50"
                >
                  <span className="text-sm font-medium text-slate-800">{note}</span>
                  <div className="flex items-center gap-1">
                    <button
                      type="button"
                      onClick={() => setNoteState(note, current === "like" ? "neutral" : "like")}
                      className={`px-2 py-1 text-xs rounded font-medium ${
                        current === "like"
                          ? "bg-emerald-600 text-white"
                          : "bg-white border border-stone-200 text-stone-600 hover:bg-stone-100"
                      }`}
                    >
                      Like
                    </button>
                    <button
                      type="button"
                      onClick={() => setNoteState(note, current === "dislike" ? "neutral" : "dislike")}
                      className={`px-2 py-1 text-xs rounded font-medium ${
                        current === "dislike"
                          ? "bg-rose-600 text-white"
                          : "bg-white border border-stone-200 text-stone-600 hover:bg-stone-100"
                      }`}
                    >
                      Avoid
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* Step 4: Known Fragrance Preferences */}
      {step === 4 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Known Fragrance Anchors</h2>
          <p className="text-sm text-stone-600 mb-6">
            Search our catalogue to add fragrances you already own, like or dislike to calibrate recommendations.
          </p>

          <div className="relative mb-4">
            <input
              type="text"
              placeholder="Search by perfume or brand name (e.g. Aventus, Sauvage, Luxury)..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="w-full px-4 py-2.5 rounded-lg border border-stone-300 focus:outline-none focus:ring-2 focus:ring-amber-500 text-sm"
            />
          </div>

          {searchResults.length > 0 && (
            <div className="border border-stone-200 rounded-md divide-y divide-stone-100 max-h-52 overflow-y-auto mb-6">
              {searchResults.map((frag) => (
                <div key={frag.id} className="p-3 flex items-center justify-between text-sm">
                  <div>
                    <div className="font-medium text-slate-900">{frag.canonical_name}</div>
                    <div className="text-xs text-stone-500">{frag.brand_name} • {frag.concentration}</div>
                  </div>
                  <div className="flex gap-1.5">
                    <button
                      type="button"
                      onClick={() => addKnownFragrance(frag, "LIKE")}
                      className="px-2 py-1 text-xs bg-emerald-50 text-emerald-700 border border-emerald-200 rounded hover:bg-emerald-100"
                    >
                      Like
                    </button>
                    <button
                      type="button"
                      onClick={() => addKnownFragrance(frag, "OWNED")}
                      className="px-2 py-1 text-xs bg-amber-50 text-amber-800 border border-amber-200 rounded hover:bg-amber-100"
                    >
                      Own
                    </button>
                    <button
                      type="button"
                      onClick={() => addKnownFragrance(frag, "DISLIKE")}
                      className="px-2 py-1 text-xs bg-rose-50 text-rose-700 border border-rose-200 rounded hover:bg-rose-100"
                    >
                      Dislike
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}

          {knownFragrances.length > 0 && (
            <div>
              <div className="text-xs font-mono uppercase tracking-wider text-stone-500 mb-2">Selected Anchors</div>
              <div className="flex flex-wrap gap-2">
                {knownFragrances.map((kf) => (
                  <span
                    key={kf.id}
                    className="inline-flex items-center gap-1.5 px-3 py-1 bg-stone-100 border border-stone-200 rounded-full text-xs text-slate-800"
                  >
                    <span>{kf.name}</span>
                    <span className="font-mono text-[10px] text-amber-800">[{kf.pref}]</span>
                    <button
                      type="button"
                      onClick={() => removeKnownFragrance(kf.id)}
                      className="text-stone-400 hover:text-stone-700"
                    >
                      ×
                    </button>
                  </span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Step 5: Usage & Budget */}
      {step === 5 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Occasions, Budget & Exclusions</h2>
          <p className="text-sm text-stone-600 mb-6">
            Configure hard budget ceilings and contexts for personalized recommendations.
          </p>

          <div className="space-y-6">
            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-stone-600 mb-2">
                Primary Occasions
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-2">
                {OCCASIONS.map((occ) => {
                  const active = selectedOccasions.includes(occ.id);
                  return (
                    <button
                      key={occ.id}
                      type="button"
                      onClick={() =>
                        setSelectedOccasions((prev) =>
                          prev.includes(occ.id) ? prev.filter((o) => o !== occ.id) : [...prev, occ.id]
                        )
                      }
                      className={`p-2.5 rounded-lg border text-xs font-medium transition-all ${
                        active
                          ? "border-amber-600 bg-amber-50/50 text-slate-900"
                          : "border-stone-200 hover:border-stone-300 text-stone-700"
                      }`}
                    >
                      {occ.label}
                    </button>
                  );
                })}
              </div>
            </div>

            <div>
              <div className="flex justify-between items-center mb-1">
                <label className="text-xs font-mono uppercase tracking-wider text-stone-600">
                  Maximum Budget Ceiling
                </label>
                <span className="font-mono font-bold text-slate-900">₹{budgetMax.toLocaleString("en-IN")}</span>
              </div>
              <input
                type="range"
                min="1000"
                max="25000"
                step="500"
                value={budgetMax}
                onChange={(e) => setBudgetMax(Number(e.target.value))}
                className="w-full accent-amber-600"
              />
              <div className="flex justify-between text-[11px] text-stone-400 font-mono mt-1">
                <span>₹1,000</span>
                <span>₹10,000</span>
                <span>₹25,000+</span>
              </div>
            </div>

            <div>
              <label className="block text-xs font-mono uppercase tracking-wider text-stone-600 mb-2">
                Explicit Avoid Terms (Hard Exclusions)
              </label>
              <div className="flex gap-2 mb-2">
                <input
                  type="text"
                  placeholder="e.g. tobacco, animalic, overly sweet"
                  value={avoidInput}
                  onChange={(e) => setAvoidInput(e.target.value)}
                  onKeyDown={(e) => e.key === "Enter" && (e.preventDefault(), addAvoidTerm())}
                  className="flex-1 px-3 py-2 rounded border border-stone-300 text-sm focus:outline-none focus:ring-1 focus:ring-amber-500"
                />
                <button
                  type="button"
                  onClick={addAvoidTerm}
                  className="px-4 py-2 bg-stone-900 text-white rounded text-xs font-medium hover:bg-stone-800"
                >
                  Add
                </button>
              </div>
              {avoidTerms.length > 0 && (
                <div className="flex flex-wrap gap-1.5">
                  {avoidTerms.map((term) => (
                    <span
                      key={term}
                      className="px-2.5 py-0.5 bg-rose-50 text-rose-700 border border-rose-200 rounded-full text-xs flex items-center gap-1"
                    >
                      <span>{term}</span>
                      <button type="button" onClick={() => removeAvoidTerm(term)} className="hover:text-rose-900">×</button>
                    </span>
                  ))}
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Step 6: Review & Finalize */}
      {step === 6 && (
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">Review Your Fragrance Profile</h2>
          <p className="text-sm text-stone-600 mb-6">
            Your structured preferences will power our deterministic recommendation engine.
          </p>

          <div className="space-y-4 text-sm divide-y divide-stone-100 mb-6">
            <div className="py-2 flex justify-between">
              <span className="text-stone-500">Familiarity Level:</span>
              <span className="font-medium text-slate-800 capitalize">{familiarity}</span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-stone-500">Scent Families:</span>
              <span className="font-medium text-slate-800">{selectedFamilies.join(", ") || "None"}</span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-stone-500">Budget Ceiling:</span>
              <span className="font-medium text-slate-800">₹{budgetMax.toLocaleString("en-IN")}</span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-stone-500">Hard Exclusions:</span>
              <span className="font-medium text-rose-700">{avoidTerms.join(", ") || "None specified"}</span>
            </div>
            <div className="py-2 flex justify-between">
              <span className="text-stone-500">Known Fragrances:</span>
              <span className="font-medium text-slate-800">{knownFragrances.length} selected</span>
            </div>
          </div>

          {!getStoredToken() && (
            <div className="bg-stone-50 border border-stone-200 p-4 rounded-lg mb-6">
              <div className="font-semibold text-slate-900 text-sm mb-1">Create Account / Save Profile</div>
              <p className="text-xs text-stone-500 mb-3">
                Save your fragrance profile to persist recommendations and preferences across devices.
              </p>
              <div className="grid sm:grid-cols-2 gap-3">
                <input
                  type="email"
                  placeholder="Your Email"
                  value={authEmail}
                  onChange={(e) => setAuthEmail(e.target.value)}
                  className="px-3 py-2 border rounded text-xs"
                />
                <input
                  type="password"
                  placeholder="Create Password"
                  value={authPassword}
                  onChange={(e) => setAuthPassword(e.target.value)}
                  className="px-3 py-2 border rounded text-xs"
                />
              </div>
            </div>
          )}
        </div>
      )}

      {/* Navigation buttons */}
      <div className="flex items-center justify-between mt-6">
        {step > 1 ? (
          <button
            type="button"
            onClick={() => setStep((s) => s - 1)}
            className="px-4 py-2 border border-stone-300 rounded-md text-sm font-medium text-stone-700 hover:bg-stone-100"
          >
            ← Previous
          </button>
        ) : (
          <div />
        )}

        <div className="flex items-center gap-3">
          {step < 6 && (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="text-xs text-stone-500 hover:text-stone-800 underline font-mono"
            >
              Skip for now
            </button>
          )}

          {step < 6 ? (
            <button
              type="button"
              onClick={() => setStep((s) => s + 1)}
              className="px-5 py-2 bg-slate-900 hover:bg-slate-800 text-white rounded-md text-sm font-medium transition-colors"
            >
              Next Step →
            </button>
          ) : (
            <button
              type="button"
              disabled={submitting}
              onClick={handleFinish}
              className="px-6 py-2.5 bg-amber-600 hover:bg-amber-700 text-white rounded-md text-sm font-medium shadow-sm transition-colors disabled:opacity-50"
            >
              {submitting ? "Saving Profile..." : "Complete Profile ✓"}
            </button>
          )}
        </div>
      </div>
    </div>
  );
}

