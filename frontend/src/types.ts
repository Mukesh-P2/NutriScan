// Mirrors backend/app/schemas.py

export type Verdict = "healthy" | "moderate" | "unhealthy";
export type NutrientStatus = "good" | "high" | "low" | "neutral";
export type FoodType = "veg" | "non_veg" | "unknown";

export interface DietTag {
  name: string;
  compatible: boolean;
}

export interface Nutrient {
  name: string;
  amount_per_serving: string;
  daily_reference: string;
  percent_of_daily: number;
  status: NutrientStatus;
}

export interface ServingNutrition {
  calories: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  saturated_fat_g: number;
  sugar_g: number;
  fiber_g: number;
  sodium_mg: number;
}

export interface AnalysisResult {
  product_name: string;
  barcode: string | null;
  verdict: Verdict;
  score: number;
  summary: string;
  pros: string[];
  cons: string[];
  tips: string[];
  key_nutrients: Nutrient[];
  serving_nutrition: ServingNutrition;
  food_type: FoodType;
  allergens: string[];
  diet_tags: DietTag[];
  recommended_serving: string;
  max_per_day: string;
  daily_context_note: string;
  total_weight: string | null;
  servings_in_pack: number | null;
  whole_pack_context: string | null;
  has_ingredients: boolean;
  missing_info: string[];
  // Present on /api/analyze responses (ScanResponse): a best-effort Open Food Facts
  // cross-check of the scanned barcode. The scanned label always wins; this is a hint.
  barcode_lookup?: ProductLookup | null;
}

export interface AskResponse {
  answer: string;
  food_name: string | null;
  is_natural_food: boolean;
  benefits: string[];
  nutrients: Nutrient[];
}

// --- Auth & profile (mirrors backend/app/auth_schemas.py) ---

export type Sex = "male" | "female";
export type ActivityLevel = "sedentary" | "light" | "moderate" | "active" | "very_active";
export type Goal = "lose" | "maintain" | "gain";

export interface User {
  id: number;
  email: string;
  name: string | null;
}

export interface Profile {
  age: number | null;
  sex: Sex | null;
  height_cm: number | null;
  weight_kg: number | null;
  activity_level: ActivityLevel | null;
  goal: Goal | null;
}

export interface NutrientTarget {
  name: string;
  amount: number;
  unit: string;
}

export interface NutritionTargets {
  calories: number;
  complete: boolean;
  basis: string;
  targets: NutrientTarget[];
}

// AI guidance grounded in the computed targets (numbers stay deterministic; AI only advises).
export interface TargetGuidance {
  summary: string;
  focus_points: string[];
  food_suggestions: string[];
  cautions: string[];
  needs_professional_advice: boolean;
  disclaimer: string;
}

// --- Food-database lookup (Open Food Facts) ---

export interface ProductNutriment {
  name: string;
  amount: string;
  per: string;
}

export interface ProductSummary {
  barcode: string;
  product_name: string | null;
  brands: string | null;
  countries: string[];
  image_url: string | null;
}

export interface ProductSearchResults {
  query: string;
  country_filter: string | null;
  count: number;
  results: ProductSummary[];
  caveats: string[];
}

export interface ProductLookup {
  found: boolean;
  barcode: string | null;
  product_name: string | null;
  brands: string | null;
  ingredients_text: string | null;
  allergens: string[];
  nutriments: ProductNutriment[];
  countries: string[];
  image_url: string | null;
  last_modified: string | null;
  source: string;
  source_url: string | null;
  caveats: string[];
}

// --- Consumption tracking ---

export interface ConsumeInput {
  product_name: string;
  servings: number;
  nutrition: ServingNutrition;
  product_verdict?: Verdict | null;
  product_score?: number | null;
}

export interface NutrientEffect {
  name: string;
  kind: "beneficial" | "budget" | "limit";
  unit: string;
  target: number;
  consumed_before: number;
  adds: number;
  remaining_after: number;
  status: string;
  message: string;
}

export interface ConsumptionRecommendation {
  product_name: string;
  servings: number;
  targets_complete: boolean;
  daily_fit: "good" | "ok" | "avoid";
  fit_headline: string;
  general: string;
  general_message: string;
  effects: NutrientEffect[];
  current_achievement_pct: number;
  projected_achievement_pct: number;
}

export interface NutrientProgress {
  name: string;
  kind: "beneficial" | "budget" | "limit";
  unit: string;
  consumed: number;
  target: number;
  remaining: number;
  percent: number;
  over: boolean;
}

export interface ConsumptionEntry {
  id: number;
  product_name: string;
  servings: number;
  calories: number;
  consumed_at: string;
}

export interface DailyProgress {
  date: string;
  targets_complete: boolean;
  achievement_pct: number;
  calories_consumed: number;
  calories_target: number;
  nutrients: NutrientProgress[];
  entries: ConsumptionEntry[];
}

export interface DaySummary {
  date: string;
  achievement_pct: number;
  calories_consumed: number;
  calories_target: number;
  entries: number;
}

export interface WeeklyAverages {
  days: number;
  days_logged: number;
  targets_complete: boolean;
  avg_achievement_pct: number;
  avg_calories: number;
  calories_target: number;
  nutrients: NutrientProgress[];
}

// --- Food suggestions (fills today's remaining gaps; numbers stay deterministic) ---

export interface FoodSuggestion {
  food: string;
  fills: string[];
  serving_idea: string;
  why: string;
  is_veg: boolean;
}

export interface FoodSuggestions {
  summary: string;
  focus_nutrients: string[];
  suggestions: FoodSuggestion[];
  cautions: string[];
  disclaimer: string;
}

// --- Service health (drives the header model badge) ---

export interface Health {
  status: string;
  gemini_configured: boolean;
  model_chain: string[];
}
