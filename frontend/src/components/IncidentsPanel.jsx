import { formatServerDateTime } from "../utils/datetime";

export default function IncidentsPanel({ incidents }) {
  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/70 p-5 shadow-glow backdrop-blur-sm">
      <h2 className="mb-4 text-lg font-semibold text-slate-100">Active Incidents</h2>
      {incidents.length === 0 ? (
        <p className="text-sm text-slate-400">No active incidents right now.</p>
      ) : (
        <div className="space-y-3">
          {incidents.slice(0, 8).map((incident) => (
            <div key={incident.id} className="rounded-xl border border-slate-700 bg-slate-950/70 p-3">
              <p className="text-sm font-medium text-slate-100">
                Probe #{incident.probe_id} - {incident.issue_type}
              </p>
              <p className="mt-1 text-xs text-slate-400">
                Source: {incident.source} | Started:{" "}
                {formatServerDateTime(incident.started_at)}
              </p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
