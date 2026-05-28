import {
  CartesianGrid,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

function parseAsUtc(dateString) {
  if (!dateString) {
    return null;
  }
  const hasTimezone = /[zZ]$|[+-]\d{2}:\d{2}$/.test(dateString);
  return new Date(hasTimezone ? dateString : `${dateString}Z`);
}

function formatTick(timestamp, selectedDuration) {
  const date = new Date(timestamp);
  if (selectedDuration === "1w" || selectedDuration === "1m") {
    return `${date.toLocaleDateString()} ${date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })}`;
  }
  return date.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit", second: "2-digit" });
}

export default function LatencyTrendChart({
  selectedProbeName,
  durationOptions,
  selectedDuration,
  onSelectDuration,
  results,
  isLoading,
  error,
}) {
  const points = results
    .slice()
    .sort((left, right) => {
      const leftDate = parseAsUtc(left.checked_at);
      const rightDate = parseAsUtc(right.checked_at);
      return (leftDate?.getTime() ?? 0) - (rightDate?.getTime() ?? 0);
    })
    .map((item) => ({
      checkedAtTs: parseAsUtc(item.checked_at)?.getTime() ?? 0,
      latency: item.latency_avg ?? 0,
      packetLoss: item.packet_loss,
    }));

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/70 p-5 shadow-glow backdrop-blur-sm">
      <div className="mb-4 flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
        <div>
          <h2 className="text-lg font-semibold text-slate-100">Latency Trend</h2>
          <p className="text-xs text-slate-400">
            {selectedProbeName
              ? `Probe: ${selectedProbeName}`
              : "Click a probe in table to view history"}
          </p>
        </div>
        <div className="flex flex-wrap gap-2">
          {durationOptions.map((option) => (
            <button
              key={option.value}
              type="button"
              onClick={() => onSelectDuration(option.value)}
              className={`rounded-md border px-2.5 py-1 text-xs ${
                selectedDuration === option.value
                  ? "border-cyan-400/50 bg-cyan-500/20 text-cyan-200"
                  : "border-slate-700 bg-slate-950 text-slate-300 hover:border-slate-500"
              }`}
            >
              {option.label}
            </button>
          ))}
        </div>
      </div>

      {error ? (
        <div className="mb-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
          {error}
        </div>
      ) : null}

      {!selectedProbeName ? (
        <div className="flex h-[280px] items-center justify-center text-sm text-slate-400">
          Select a probe from the table to load chart data.
        </div>
      ) : points.length === 0 ? (
        <div className="flex h-[280px] items-center justify-center text-sm text-slate-400">
          No data found for {selectedDuration}. Try a longer duration.
        </div>
      ) : (
        <div className="h-[280px]">
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={points}>
              <CartesianGrid strokeDasharray="4 4" stroke="#1e293b" />
              <XAxis
                dataKey="checkedAtTs"
                type="number"
                domain={["dataMin", "dataMax"]}
                tickFormatter={(value) => formatTick(value, selectedDuration)}
                stroke="#94a3b8"
                tick={{ fontSize: 11 }}
              />
              <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
              <Tooltip
                labelFormatter={(value) => new Date(value).toLocaleString()}
                contentStyle={{
                  backgroundColor: "#020617",
                  borderColor: "#334155",
                  color: "#e2e8f0",
                }}
              />
              <Line type="monotone" dataKey="latency" stroke="#22d3ee" dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {isLoading ? <p className="mt-2 text-xs text-slate-500">Loading probe history...</p> : null}
      {!isLoading && points.length > 0 ? (
        <p className="mt-2 text-xs text-slate-500">
          Showing {points.length} samples for {selectedDuration}.
        </p>
      ) : null}
    </div>
  );
}
