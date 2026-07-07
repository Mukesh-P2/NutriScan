// Shared error banner. Interprets the backend message (which already differs for a rate-limit
// 429 vs an overload 503, thanks to the Gemini failover layer) to show friendlier, status-aware
// guidance and an optional retry — instead of an ad-hoc rose <p> on every page.
export default function ErrorNotice({ message, onRetry }: { message: string; onRetry?: () => void }) {
  const lower = message.toLowerCase();
  const rateLimited = lower.includes("rate limit");
  const busy = !rateLimited && (lower.includes("busy") || lower.includes("overload"));
  const soft = rateLimited || busy;

  const tone = soft
    ? "border-amber-200 bg-amber-50 text-amber-800"
    : "border-rose-200 bg-rose-50 text-rose-700";
  const icon = rateLimited ? "⏳" : busy ? "🔄" : "⚠️";
  const title = rateLimited ? "Rate limited" : busy ? "AI service busy" : "Something went wrong";

  return (
    <div className={`rounded-lg border p-3 text-sm ${tone}`}>
      <div className="flex items-start gap-2">
        <span aria-hidden>{icon}</span>
        <div className="min-w-0 flex-1">
          <p className="font-semibold">{title}</p>
          <p className="mt-0.5 break-words">{message}</p>
          {soft && (
            <p className="mt-1 text-xs opacity-80">
              NutriScan already retried across its fallback models. Give it a few seconds and try again.
            </p>
          )}
          {onRetry && (
            <button
              onClick={onRetry}
              className="mt-2 rounded-md bg-white/70 px-3 py-1 text-xs font-semibold ring-1 ring-inset ring-black/10 hover:bg-white"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    </div>
  );
}
