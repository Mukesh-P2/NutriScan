import type { Nutrient, NutrientStatus } from "../types";

const statusColor: Record<NutrientStatus, string> = {
  good: "bg-emerald-500",
  low: "bg-sky-500",
  high: "bg-rose-500",
  neutral: "bg-slate-400",
};

export default function NutrientList({ nutrients }: { nutrients: Nutrient[] }) {
  if (!nutrients.length) return null;
  return (
    <div className="space-y-3">
      {nutrients.map((n) => (
        <div key={n.name}>
          <div className="flex justify-between text-sm">
            <span className="font-medium">{n.name}</span>
            <span className="text-slate-500">
              {n.amount_per_serving} · {n.percent_of_daily}% of {n.daily_reference}/day
            </span>
          </div>
          <div className="mt-1 h-2 w-full rounded-full bg-slate-200">
            <div
              className={`h-2 rounded-full ${statusColor[n.status]}`}
              style={{ width: `${Math.min(n.percent_of_daily, 100)}%` }}
            />
          </div>
        </div>
      ))}
    </div>
  );
}
