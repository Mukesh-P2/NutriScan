import { useEffect, useState } from "react";
import { useAuth } from "../AuthContext";
import Login from "./Login";
import { fetchGuidance, fetchProfile, fetchTargets, saveProfile } from "../auth";
import type { NutritionTargets, Profile as ProfileData, TargetGuidance } from "../types";

const EMPTY: ProfileData = {
  age: null,
  sex: null,
  height_cm: null,
  weight_kg: null,
  activity_level: null,
  goal: "maintain",
};

const ACTIVITY_OPTIONS: { value: string; label: string }[] = [
  { value: "sedentary", label: "Sedentary (little exercise)" },
  { value: "light", label: "Light (1–3 days/week)" },
  { value: "moderate", label: "Moderate (3–5 days/week)" },
  { value: "active", label: "Active (6–7 days/week)" },
  { value: "very_active", label: "Very active (hard daily / physical job)" },
];

// Fields required to compute personalized targets (goal has a sensible default).
// Must match _REQUIRED_FIELDS in backend/app/services/nutrition.py.
const REQUIRED: (keyof ProfileData)[] = ["age", "sex", "height_cm", "weight_kg", "activity_level"];

// Small red asterisk marking a mandatory field.
const Req = () => <span className="text-rose-500"> *</span>;

export default function Profile() {
  const { user, logout } = useAuth();
  const [profile, setProfile] = useState<ProfileData>(EMPTY);
  const [targets, setTargets] = useState<NutritionTargets | null>(null);
  const [guidance, setGuidance] = useState<TargetGuidance | null>(null);
  const [guidanceLoading, setGuidanceLoading] = useState(false);
  const [guidanceError, setGuidanceError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    if (!user) return;
    setLoading(true);
    Promise.all([fetchProfile(), fetchTargets()])
      .then(([p, t]) => {
        setProfile({ ...EMPTY, ...p });
        setTargets(t);
      })
      .catch((err) => setError(err instanceof Error ? err.message : "Failed to load profile."))
      .finally(() => setLoading(false));
  }, [user]);

  if (!user) return <Login />;

  const missing = REQUIRED.filter((k) => profile[k] === null || profile[k] === undefined);
  const complete = missing.length === 0;

  function set<K extends keyof ProfileData>(key: K, value: ProfileData[K]) {
    setProfile((p) => ({ ...p, [key]: value }));
    setSaved(false);
  }

  function num(v: string): number | null {
    return v === "" ? null : Number(v);
  }

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (!complete) {
      setError("Please fill in all required fields (marked *) before saving.");
      return;
    }
    setSaving(true);
    setError(null);
    try {
      const updated = await saveProfile(profile);
      setProfile({ ...EMPTY, ...updated });
      setTargets(await fetchTargets());
      setGuidance(null); // targets changed — old AI guidance no longer matches
      setGuidanceError(null);
      setSaved(true);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to save.");
    } finally {
      setSaving(false);
    }
  }

  async function getGuidance() {
    setGuidanceLoading(true);
    setGuidanceError(null);
    try {
      setGuidance(await fetchGuidance());
    } catch (err) {
      setGuidanceError(err instanceof Error ? err.message : "Couldn't get suggestions.");
    } finally {
      setGuidanceLoading(false);
    }
  }

  const inputClass =
    "w-full rounded-lg border border-slate-300 p-2.5 focus:border-emerald-500 focus:outline-none focus:ring-1 focus:ring-emerald-500";

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-lg font-bold">{user.name || user.email}</h2>
          <p className="text-sm text-slate-500">{user.email}</p>
        </div>
        <button onClick={logout} className="text-sm font-semibold text-slate-500 hover:text-rose-600">
          Log out
        </button>
      </div>

      {loading ? (
        <p className="text-slate-500">Loading…</p>
      ) : (
        <>
          <form onSubmit={submit} className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
            <h3 className="font-semibold text-slate-700">Your details</h3>
            <p className="text-sm text-slate-500">
              Fields marked <span className="text-rose-500">*</span> are required for personalized targets.
              Until they're all set, we use generic adult defaults.
            </p>

            <div className="grid grid-cols-2 gap-4">
              <label className="text-sm">
                <span className="text-slate-600">Age<Req /></span>
                <input type="number" required min={1} max={120} value={profile.age ?? ""} onChange={(e) => set("age", num(e.target.value))} className={inputClass} />
              </label>
              <label className="text-sm">
                <span className="text-slate-600">Sex<Req /></span>
                <select required value={profile.sex ?? ""} onChange={(e) => set("sex", (e.target.value || null) as ProfileData["sex"])} className={inputClass}>
                  <option value="">—</option>
                  <option value="male">Male</option>
                  <option value="female">Female</option>
                </select>
              </label>
              <label className="text-sm">
                <span className="text-slate-600">Height (cm)<Req /></span>
                <input type="number" required min={50} max={260} value={profile.height_cm ?? ""} onChange={(e) => set("height_cm", num(e.target.value))} className={inputClass} />
              </label>
              <label className="text-sm">
                <span className="text-slate-600">Weight (kg)<Req /></span>
                <input type="number" required min={2} max={500} step="0.1" value={profile.weight_kg ?? ""} onChange={(e) => set("weight_kg", num(e.target.value))} className={inputClass} />
              </label>
            </div>

            <label className="block text-sm">
              <span className="text-slate-600">Activity level<Req /></span>
              <select required value={profile.activity_level ?? ""} onChange={(e) => set("activity_level", (e.target.value || null) as ProfileData["activity_level"])} className={inputClass}>
                <option value="">—</option>
                {ACTIVITY_OPTIONS.map((o) => (
                  <option key={o.value} value={o.value}>{o.label}</option>
                ))}
              </select>
            </label>

            <label className="block text-sm">
              <span className="text-slate-600">Goal</span>
              <select value={profile.goal ?? "maintain"} onChange={(e) => set("goal", e.target.value as ProfileData["goal"])} className={inputClass}>
                <option value="lose">Lose weight</option>
                <option value="maintain">Maintain</option>
                <option value="gain">Gain weight</option>
              </select>
            </label>

            {error && <p className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{error}</p>}
            <div className="flex items-center gap-3">
              <button type="submit" disabled={saving || !complete} className="rounded-lg bg-emerald-600 px-5 py-2 font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50">
                {saving ? "Saving…" : "Save profile"}
              </button>
              {!complete && <span className="text-sm text-slate-400">Fill required fields to save</span>}
              {complete && saved && <span className="text-sm text-emerald-600">✓ Saved</span>}
            </div>
          </form>

          {targets && (
            <div className="space-y-3 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <div className="flex items-baseline justify-between">
                <h3 className="font-semibold text-slate-700">Daily targets</h3>
                <span className="text-2xl font-bold text-emerald-700">{targets.calories} kcal</span>
              </div>
              {!targets.complete && (
                <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-700">
                  These are generic defaults. Fill in every field above for targets tailored to you.
                </p>
              )}
              <p className="text-xs text-slate-500">{targets.basis}</p>
              <ul className="divide-y divide-slate-100">
                {targets.targets.map((t) => (
                  <li key={t.name} className="flex justify-between py-2 text-sm">
                    <span className="text-slate-600">{t.name}</span>
                    <span className="font-medium text-slate-800">{t.amount} {t.unit}</span>
                  </li>
                ))}
              </ul>

              <div className="border-t border-slate-100 pt-4">
                <button
                  onClick={getGuidance}
                  disabled={guidanceLoading}
                  className="rounded-lg bg-emerald-50 px-4 py-2 text-sm font-semibold text-emerald-700 hover:bg-emerald-100 disabled:opacity-50"
                >
                  {guidanceLoading ? "Getting suggestions…" : guidance ? "↻ Refresh AI suggestions" : "✨ Get AI suggestions"}
                </button>
                <p className="mt-1 text-xs text-slate-400">
                  AI advises on how to meet the targets above. The numbers themselves come from the formula, not the AI.
                </p>
                {guidanceError && (
                  <p className="mt-3 rounded-lg bg-rose-50 p-3 text-sm text-rose-700">{guidanceError}</p>
                )}
              </div>
            </div>
          )}

          {guidance && (
            <div className="space-y-4 rounded-2xl bg-white p-6 shadow-sm ring-1 ring-slate-200">
              <h3 className="font-semibold text-slate-700">✨ Personalized suggestions</h3>

              {guidance.needs_professional_advice && (
                <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-800">
                  ⚠️ Your details suggest you should confirm these targets with a doctor or registered dietitian
                  before acting on them.
                </p>
              )}

              <p className="text-slate-700">{guidance.summary}</p>

              {guidance.focus_points.length > 0 && (
                <Section title="How to hit your targets" icon="🎯" items={guidance.focus_points} />
              )}
              {guidance.food_suggestions.length > 0 && (
                <Section title="Foods that help" icon="🥗" items={guidance.food_suggestions} />
              )}
              {guidance.cautions.length > 0 && (
                <Section title="Watch out for" icon="⚠️" items={guidance.cautions} />
              )}

              <p className="border-t border-slate-100 pt-3 text-xs italic text-slate-400">{guidance.disclaimer}</p>
            </div>
          )}
        </>
      )}
    </div>
  );
}

function Section({ title, icon, items }: { title: string; icon: string; items: string[] }) {
  return (
    <div>
      <h4 className="font-semibold text-slate-700">{title}</h4>
      <ul className="mt-1 space-y-1 text-sm">
        {items.map((it, i) => (
          <li key={i} className="flex gap-2">
            <span>{icon}</span>
            <span className="text-slate-700">{it}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}
