import { formatServerTime } from "../utils/datetime";

const STATUS_COLOR_CLASS = {
  UP: "bg-emerald-500/20 text-emerald-300 border-emerald-400/40",
  DEGRADED: "bg-amber-500/20 text-amber-300 border-amber-400/40",
  DOWN: "bg-red-500/20 text-red-300 border-red-400/40",
};

function getStatusClass(status) {
  return STATUS_COLOR_CLASS[status] ?? "bg-slate-700/30 text-slate-300 border-slate-400/30";
}

export default function ProbeStatusTable({
  probes,
  latestResults,
  selectedProbeId,
  onSelectProbe,
  onEditProbe,
  onDeleteProbe,
}) {
  const canManageProbes = Boolean(onEditProbe && onDeleteProbe);
  const canSelectProbe = typeof onSelectProbe === "function";
  const resultByProbe = latestResults.reduce((accumulator, result) => {
    const key = `${result.probe_id}:${result.source}`;
    if (!accumulator.has(key)) {
      accumulator.set(key, result);
    }
    return accumulator;
  }, new Map());

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/70 shadow-glow backdrop-blur-sm">
      <div className="border-b border-slate-800 px-5 py-4">
        <h2 className="text-lg font-semibold text-slate-100">Real-time Probe Table</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm text-slate-300">
          <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
            <tr>
              <th className="px-4 py-3">Target</th>
              <th className="px-4 py-3">Host</th>
              <th className="px-4 py-3">Group</th>
              <th className="px-4 py-3">Source</th>
              <th className="px-4 py-3">Status</th>
              <th className="px-4 py-3">Latency (avg)</th>
              <th className="px-4 py-3">Jitter</th>
              <th className="px-4 py-3">Packet loss</th>
              <th className="px-4 py-3">Last checked</th>
              {canManageProbes ? <th className="px-4 py-3">Actions</th> : null}
            </tr>
          </thead>
          <tbody>
            {probes.map((probe) => {
              const result = resultByProbe.get(`${probe.id}:default`);
              const isSelected = selectedProbeId === probe.id;
              return (
                <tr
                  key={probe.id}
                  className={`border-t border-slate-800 ${
                    canSelectProbe ? "cursor-pointer hover:bg-slate-800/40" : ""
                  } ${isSelected ? "bg-cyan-500/10" : ""}`}
                  onClick={() => {
                    if (canSelectProbe) {
                      onSelectProbe(probe.id);
                    }
                  }}
                >
                  <td className="px-4 py-3 font-medium text-slate-100">{probe.name}</td>
                  <td className="px-4 py-3">{probe.host}</td>
                  <td className="px-4 py-3">{probe.group}</td>
                  <td className="px-4 py-3">{result?.source ?? "default"}</td>
                  <td className="px-4 py-3">
                    <span
                      className={`rounded-full border px-2.5 py-1 text-xs font-medium ${getStatusClass(
                        result?.status
                      )}`}
                    >
                      {result?.status ?? "N/A"}
                    </span>
                  </td>
                  <td className="px-4 py-3">{result?.latency_avg ?? "-"}</td>
                  <td className="px-4 py-3">{result?.jitter ?? "-"}</td>
                  <td className="px-4 py-3">{result ? `${result.packet_loss}%` : "-"}</td>
                  <td className="px-4 py-3">
                    {result?.checked_at
                      ? formatServerTime(result.checked_at, {
                          hour: "2-digit",
                          minute: "2-digit",
                          second: "2-digit",
                        })
                      : "No data"}
                  </td>
                  {canManageProbes ? (
                    <td className="px-4 py-3">
                      <div className="flex gap-2">
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onEditProbe(probe);
                          }}
                          className="rounded-md border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-300 hover:bg-cyan-500/20"
                        >
                          Edit
                        </button>
                        <button
                          type="button"
                          onClick={(event) => {
                            event.stopPropagation();
                            onDeleteProbe(probe);
                          }}
                          className="rounded-md border border-red-400/40 bg-red-500/10 px-2 py-1 text-xs text-red-300 hover:bg-red-500/20"
                        >
                          Delete
                        </button>
                      </div>
                    </td>
                  ) : null}
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
}
