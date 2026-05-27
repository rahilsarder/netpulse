export default function KpiCard({ title, value, accent = "cyan" }) {
  const accentColor =
    accent === "red"
      ? "border-red-400/40 text-red-300"
      : accent === "yellow"
        ? "border-amber-400/40 text-amber-300"
        : "border-cyan-400/40 text-cyan-300";

  return (
    <div
      className={`rounded-2xl border ${accentColor} bg-slate-900/70 p-4 shadow-glow backdrop-blur-sm`}
    >
      <p className="text-xs uppercase tracking-wide text-slate-400">{title}</p>
      <p className="mt-3 text-2xl font-semibold text-slate-100">{value}</p>
    </div>
  );
}
