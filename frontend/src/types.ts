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
}

export interface AskResponse {
  answer: string;
  food_name: string | null;
  is_natural_food: boolean;
  benefits: string[];
  nutrients: Nutrient[];
}
