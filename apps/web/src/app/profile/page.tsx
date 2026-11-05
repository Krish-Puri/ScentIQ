"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import {
  fetchUserProfile,
  fetchUserFeedbacks,
  fetchLearnedPreferences,
  deleteUserFeedback,
  loginUser,
  registerUser,
  getStoredToken,
  clearStoredToken,
  UserProfile,
  UserFeedback,
  LearnedPreferences,
} from "@/lib/api";

export default function ProfilePage() {
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [feedbacks, setFeedbacks] = useState<UserFeedback[]>([]);
  const [learned, setLearned] = useState<LearnedPreferences | null>(null);
  const [loading, setLoading] = useState(true);

  // Auth form states
  const [authEmail, setAuthEmail] = useState("");
  const [authPassword, setAuthPassword] = useState("");
  const [authMode, setAuthMode] = useState<"login" | "register">("login");
  const [authError, setAuthError] = useState<string | null>(null);

  const loadData = async () => {
    setLoading(true);
    try {
      const token = getStoredToken();
      if (token) {
        const [prof, fbs, lrn] = await Promise.all([
          fetchUserProfile(),
          fetchUserFeedbacks(),
          fetchLearnedPreferences(),
        ]);
        setProfile(prof);
        setFeedbacks(fbs);
        setLearned(lrn);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const handleAuth = async (e: React.FormEvent) => {
    e.preventDefault();
    setAuthError(null);
    try {
      if (authMode === "login") {
        await loginUser(authEmail, authPassword);
      } else {
        await registerUser(authEmail, authPassword);
      }
      await loadData();
    } catch (err: any) {
      setAuthError(err.message || "Authentication failed");
    }
  };

  const handleLogout = () => {
    clearStoredToken();
    setProfile(null);
    setFeedbacks([]);
    setLearned(null);
  };

  const handleDeleteFeedback = async (fragranceId: string) => {
    try {
      await deleteUserFeedback(fragranceId);
      setFeedbacks((prev) => prev.filter((f) => f.fragrance_id !== fragranceId));
      const updatedLearned = await fetchLearnedPreferences();
      setLearned(updatedLearned);
    } catch (err) {
      console.error("Failed to delete feedback", err);
    }
  };

  if (!getStoredToken() && !profile) {
    return (
      <div className="max-w-md mx-auto py-12">
        <div className="bg-white border border-stone-200 rounded-lg p-6 sm:p-8 shadow-sm">
          <h2 className="font-serif text-2xl font-bold text-slate-900 mb-2">
            {authMode === "login" ? "Sign In to Your Profile" : "Create Personal Profile"}
          </h2>
          <p className="text-xs text-stone-500 mb-6">
            Access your personalized recommendations, hard exclusions, and fragrance wardrobe history.
          </p>

          {authError && (
            <div className="mb-4 p-2.5 bg-rose-50 border border-rose-200 text-rose-700 text-xs rounded">
              {authError}
            </div>
          )}

          <form onSubmit={handleAuth} className="space-y-4 text-sm">
            <div>
              <label className="block text-xs font-mono uppercase text-stone-600 mb-1">Email</label>
              <input
                type="email"
                required
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
                className="w-full px-3 py-2 border rounded border-stone-300 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
            <div>
              <label className="block text-xs font-mono uppercase text-stone-600 mb-1">Password</label>
              <input
                type="password"
                required
                value={authPassword}
                onChange={(e) => setAuthPassword(e.target.value)}
                className="w-full px-3 py-2 border rounded border-stone-300 focus:outline-none focus:ring-1 focus:ring-amber-500"
              />
            </div>
            <button
              type="submit"
              className="w-full py-2 bg-slate-900 hover:bg-slate-800 text-white rounded text-sm font-medium transition-colors"
            >
              {authMode === "login" ? "Sign In" : "Register"}
            </button>
          </form>

          <div className="mt-4 pt-4 border-t border-stone-100 flex justify-between items-center text-xs">
            <span className="text-stone-500">
              {authMode === "login" ? "Need an account?" : "Already registered?"}
            </span>
            <button
              type="button"
              onClick={() => setAuthMode(authMode === "login" ? "register" : "login")}
              className="font-medium text-amber-800 hover:underline"
            >
              {authMode === "login" ? "Create one" : "Sign In"}
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row justify-between items-start sm:items-center gap-4 bg-white border border-stone-200 p-6 rounded-lg shadow-sm">
        <div>
          <div className="flex items-center gap-2">
            <h1 className="font-serif text-3xl font-bold text-slate-900">Personal Fragrance Profile</h1>
            <span className="text-[10px] uppercase font-mono px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 font-medium">
              Active
            </span>
          </div>
          <p className="text-xs text-stone-500 mt-1">
            Deterministic preferences and transparent feedback learning. No ungrounded ML black-boxes.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Link
            href="/onboarding"
            className="text-xs px-3 py-1.5 border border-stone-300 hover:bg-stone-50 rounded font-medium text-stone-700"
          >
            Re-run Onboarding
          </Link>
          <button
            onClick={handleLogout}
            className="text-xs px-3 py-1.5 bg-stone-100 hover:bg-stone-200 rounded font-medium text-stone-600"
          >
            Sign Out
          </button>
        </div>
      </div>

      <div className="grid md:grid-cols-3 gap-6">
        {/* Left 2 Cols: Stored Profile & Preferences */}
        <div className="md:col-span-2 space-y-6">
          {/* Explicit Preferences Card */}
          <div className="bg-white border border-stone-200 rounded-lg p-6 shadow-sm">
            <h2 className="font-serif text-xl font-bold text-slate-900 mb-4 pb-2 border-b border-stone-100">
              Explicit Preference Attributes
            </h2>

            <div className="grid sm:grid-cols-2 gap-4 text-sm">
              <div>
                <span className="text-xs font-mono uppercase text-stone-400 block mb-1">Familiarity Level</span>
                <span className="font-medium text-slate-900 capitalize">{profile?.familiarity_level || "Not set"}</span>
              </div>
              <div>
                <span className="text-xs font-mono uppercase text-stone-400 block mb-1">Budget Ceiling</span>
                <span className="font-mono font-bold text-slate-900">
                  {profile?.budget_max ? `₹${profile.budget_max.toLocaleString("en-IN")}` : "No ceiling"}
                </span>
              </div>
              <div className="sm:col-span-2">
                <span className="text-xs font-mono uppercase text-stone-400 block mb-1">Preferred Scent Families</span>
                <div className="flex flex-wrap gap-1.5">
                  {profile?.preferred_families?.map((f) => (
                    <span key={f} className="px-2.5 py-0.5 rounded-full text-xs bg-slate-900 text-white">
                      {f}
                    </span>
                  )) || <span className="text-stone-400 text-xs">None specified</span>}
                </div>
              </div>
              <div className="sm:col-span-2">
                <span className="text-xs font-mono uppercase text-stone-400 block mb-1">Preferred Notes</span>
                <div className="flex flex-wrap gap-1.5">
                  {profile?.preferred_notes?.map((n) => (
                    <span key={n} className="px-2.5 py-0.5 rounded-full text-xs bg-emerald-50 text-emerald-800 border border-emerald-200">
                      {n}
                    </span>
                  )) || <span className="text-stone-400 text-xs">None specified</span>}
                </div>
              </div>
              <div className="sm:col-span-2">
                <span className="text-xs font-mono uppercase text-stone-400 block mb-1">Occasions</span>
                <div className="flex flex-wrap gap-1.5">
                  {profile?.occasions?.map((occ) => (
                    <span key={occ} className="px-2.5 py-0.5 rounded-full text-xs bg-stone-100 text-stone-700">
                      {occ}
                    </span>
                  )) || <span className="text-stone-400 text-xs">All occasions</span>}
                </div>
              </div>
            </div>
          </div>

          {/* Hard Exclusions Card */}
          <div className="bg-white border border-rose-200/80 rounded-lg p-6 shadow-sm">
            <div className="flex items-center justify-between mb-3 pb-2 border-b border-rose-100">
              <h2 className="font-serif text-lg font-bold text-rose-900">
                Hard Avoid Exclusions
              </h2>
              <span className="text-[10px] font-mono px-2 py-0.5 bg-rose-100 text-rose-800 rounded font-medium">
                Strict Filter
              </span>
            </div>
            <p className="text-xs text-stone-600 mb-4">
              Fragrances containing these notes or accords are strictly excluded from all recommendations and AI advisor queries.
            </p>
            <div className="flex flex-wrap gap-2">
              {profile?.avoid_terms && profile.avoid_terms.length > 0 ? (
                profile.avoid_terms.map((term) => (
                  <span
                    key={term}
                    className="px-3 py-1 bg-rose-50 border border-rose-200 text-rose-800 rounded-full text-xs font-medium"
                  >
                    🚫 {term}
                  </span>
                ))
              ) : (
                <span className="text-xs text-stone-400 italic">No hard exclusions configured.</span>
              )}
            </div>
          </div>

          {/* Fragrance Feedback History (EPIC-12) */}
          <div className="bg-white border border-stone-200 rounded-lg p-6 shadow-sm">
            <h2 className="font-serif text-xl font-bold text-slate-900 mb-2 pb-2 border-b border-stone-100">
              Fragrance Feedback & Wardrobe History
            </h2>
            <p className="text-xs text-stone-500 mb-4">
              Explicit ratings and wear observations that directly refine your recommendation rankings.
            </p>

            {feedbacks.length === 0 ? (
              <div className="text-center py-8 text-stone-400 text-sm">
                No feedback recorded yet. Browse the catalogue or details page to like, dislike, or mark owned fragrances!
              </div>
            ) : (
              <div className="divide-y divide-stone-100">
                {feedbacks.map((fb) => (
                  <div key={fb.id} className="py-3 flex items-start justify-between gap-4">
                    <div>
                      <div className="flex items-center gap-2">
                        <Link
                          href={`/fragrances/${fb.fragrance_slug}`}
                          className="font-medium text-slate-900 hover:text-amber-800 transition-colors text-sm"
                        >
                          {fb.fragrance_name || "Fragrance"}
                        </Link>
                        <span
                          className={`text-[10px] font-mono font-medium px-2 py-0.5 rounded ${
                            fb.feedback_type === "LIKE" || fb.feedback_type === "OWNED"
                              ? "bg-emerald-100 text-emerald-800"
                              : fb.feedback_type === "DISLIKE"
                              ? "bg-rose-100 text-rose-800"
                              : "bg-stone-100 text-stone-700"
                          }`}
                        >
                          {fb.feedback_type}
                        </span>
                        {fb.rating && (
                          <span className="text-xs font-mono font-bold text-amber-700">★ {fb.rating}</span>
                        )}
                      </div>
                      <div className="text-xs text-stone-500 mt-0.5">
                        {fb.fragrance_brand} • {new Date(fb.created_at).toLocaleDateString()}
                      </div>
                      {fb.context_json?.reason && (
                        <p className="text-xs text-stone-700 mt-1 italic">
                          "{fb.context_json.reason}"
                        </p>
                      )}
                    </div>
                    <button
                      onClick={() => handleDeleteFeedback(fb.fragrance_id)}
                      className="text-stone-400 hover:text-rose-600 text-xs p-1"
                      title="Remove feedback"
                    >
                      Remove
                    </button>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>

        {/* Right Col: Preference Learning & Transparency (EPIC-12) */}
        <div className="space-y-6">
          <div className="bg-amber-50/50 border border-amber-200/80 rounded-lg p-5 shadow-sm">
            <div className="flex items-center justify-between mb-2">
              <h3 className="font-serif text-base font-bold text-amber-950">
                Transparent Preference Learning
              </h3>
              <span className="text-[9px] uppercase font-mono px-1.5 py-0.5 bg-amber-200 text-amber-900 rounded font-medium">
                EPIC-12
              </span>
            </div>
            <p className="text-xs text-stone-600 mb-4">
              Derived automatically from your {learned?.total_feedbacks || 0} feedback items. Inferred weights never overwrite your explicit profile.
            </p>

            {/* Inferred Accord Weights */}
            <div className="space-y-3">
              <span className="text-[11px] font-mono uppercase tracking-wider text-stone-500 block">
                Learned Accord Affinity
              </span>
              {learned?.inferred_accord_weights && Object.keys(learned.inferred_accord_weights).length > 0 ? (
                Object.entries(learned.inferred_accord_weights).map(([accord, weight]) => {
                  const isPositive = weight > 0;
                  return (
                    <div key={accord} className="text-xs">
                      <div className="flex justify-between items-center mb-1">
                        <span className="capitalize font-medium text-slate-800">{accord}</span>
                        <span className={`font-mono text-[11px] ${isPositive ? "text-emerald-700" : "text-rose-700"}`}>
                          {isPositive ? `+${(weight * 100).toFixed(0)}%` : `${(weight * 100).toFixed(0)}%`}
                        </span>
                      </div>
                      <div className="w-full bg-stone-200 h-1.5 rounded-full overflow-hidden">
                        <div
                          className={`h-full ${isPositive ? "bg-emerald-600" : "bg-rose-500"}`}
                          style={{ width: `${Math.abs(weight) * 100}%` }}
                        />
                      </div>
                    </div>
                  );
                })
              ) : (
                <div className="text-xs text-stone-400 italic">
                  Feedback signals will appear here as you rate fragrances.
                </div>
              )}
            </div>

            {/* Inferred Note Weights */}
            <div className="space-y-3 mt-6 pt-4 border-t border-amber-200/60">
              <span className="text-[11px] font-mono uppercase tracking-wider text-stone-500 block">
                Learned Note Affinity
              </span>
              {learned?.inferred_note_weights && Object.keys(learned.inferred_note_weights).length > 0 ? (
                Object.entries(learned.inferred_note_weights).slice(0, 5).map(([note, weight]) => (
                  <div key={note} className="flex justify-between items-center text-xs">
                    <span className="capitalize text-slate-800">{note}</span>
                    <span className={`font-mono ${weight > 0 ? "text-emerald-700" : "text-rose-700"}`}>
                      {weight > 0 ? `+${weight.toFixed(2)}` : weight.toFixed(2)}
                    </span>
                  </div>
                ))
              ) : (
                <div className="text-xs text-stone-400 italic">No note affinities yet.</div>
              )}
            </div>
          </div>

          <div className="bg-white border border-stone-200 rounded-lg p-5 text-xs text-stone-600 space-y-2">
            <h4 className="font-semibold text-slate-900">Privacy & Data Control</h4>
            <p>
              Your personal fragrance profile is fully user-editable and can be modified at any time. SCENTIQ does not track sensitive demographics or resell personal data.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
