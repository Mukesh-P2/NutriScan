// Convert an Open Food Facts product's per-100g nutriments into a ServingNutrition so a lookup
// result can be logged with the same ConsumePanel used for scans. OFF gives strings like "5.2 g";
// here "1 serving" means 100 g (the panel lets the user scale servings to their real portion).
import type { ProductLookup, ServingNutrition } from "./types";

function num(s: string | undefined): number {
  if (!s) return 0;
  const m = s.match(/-?\d+(\.\d+)?/);
  return m ? parseFloat(m[0]) : 0;
}

export function servingFromLookup(product: ProductLookup): ServingNutrition | null {
  const by: Record<string, string> = {};
  for (const n of product.nutriments) by[n.name.toLowerCase()] = n.amount;

  // OFF reports Sodium and/or Salt in grams; convert to mg (salt→sodium ≈ ×400).
  const sodiumG = num(by["sodium"]);
  const saltG = num(by["salt"]);
  const sodium_mg = sodiumG > 0 ? sodiumG * 1000 : saltG > 0 ? saltG * 400 : 0;

  const nutrition: ServingNutrition = {
    calories: num(by["energy"]),
    protein_g: num(by["protein"]),
    carbs_g: num(by["carbohydrate"]),
    fat_g: num(by["fat"]),
    saturated_fat_g: num(by["saturated fat"]),
    sugar_g: num(by["sugars"]),
    fiber_g: num(by["fiber"]),
    sodium_mg,
  };

  return Object.values(nutrition).some((v) => v > 0) ? nutrition : null;
}
