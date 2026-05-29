import ProbeFormCard from "./ProbeFormCard";

export default function ProbeManagementModal({
  isOpen,
  probes,
  activeProbe,
  onClose,
  onSubmitProbe,
  onCancelEdit,
  onEditProbe,
  onDeleteProbe,
  isSubmitting,
  mutationError,
  alertPersistSeconds,
  onChangeAlertPersistSeconds,
  incidentReminderMinutes,
  onChangeIncidentReminderMinutes,
  onSaveAlertSettings,
  isSavingAlertSettings,
  alertSettingsError,
}) {
  if (!isOpen) {
    return null;
  }

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/80 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      aria-label="Probe management"
    >
      <div className="max-h-[90vh] w-full max-w-6xl overflow-y-auto rounded-2xl border border-slate-700 bg-slate-900 p-5 shadow-glow">
        <div className="mb-4 flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-slate-100">Probe Management</h2>
            <p className="text-xs text-slate-400">
              Add, edit, and delete probes without leaving the dashboard.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500"
          >
            Close
          </button>
        </div>

        <div className="grid gap-4">
          <div className="rounded-2xl border border-slate-700 bg-slate-900/70 p-4">
            <h3 className="text-sm font-semibold text-slate-100">Alert Timing</h3>
            <p className="mt-1 text-xs text-slate-400">
              Degraded alerts (high latency/packet loss) trigger only when issue persists for this
              many seconds.
            </p>
            <p className="mt-1 text-xs text-slate-400">
              Incident reminder sends repeat notifications every N minutes while an incident stays
              active (set 0 to disable reminders).
            </p>

            {alertSettingsError ? (
              <div className="mt-3 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
                {alertSettingsError}
              </div>
            ) : null}

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <input
                type="number"
                min={10}
                max={86400}
                value={alertPersistSeconds}
                onChange={(event) => onChangeAlertPersistSeconds(Number(event.target.value))}
                className="w-40 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
              />
              <span className="text-xs text-slate-400">seconds</span>
            </div>
            <div className="mt-2 flex flex-wrap items-center gap-2">
              <input
                type="number"
                min={0}
                max={1440}
                value={incidentReminderMinutes}
                onChange={(event) =>
                  onChangeIncidentReminderMinutes(Number(event.target.value))
                }
                className="w-40 rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
              />
              <span className="text-xs text-slate-400">minutes (0 = off)</span>
              <button
                type="button"
                onClick={onSaveAlertSettings}
                disabled={isSavingAlertSettings}
                className="rounded-lg border border-cyan-400/40 bg-cyan-500/10 px-3 py-2 text-xs text-cyan-300 hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-60"
              >
                {isSavingAlertSettings ? "Saving..." : "Save timing"}
              </button>
            </div>
          </div>

          <ProbeFormCard
            activeProbe={activeProbe}
            onSubmit={onSubmitProbe}
            onCancelEdit={onCancelEdit}
            isSubmitting={isSubmitting}
            mutationError={mutationError}
          />

          <div className="rounded-2xl border border-slate-700 bg-slate-900/70 p-4">
            <h3 className="mb-3 text-sm font-semibold text-slate-100">Existing Probes</h3>
            <div className="overflow-x-auto">
              <table className="w-full min-w-[760px] text-left text-sm text-slate-300">
                <thead className="bg-slate-900 text-xs uppercase tracking-wide text-slate-400">
                  <tr>
                    <th className="px-3 py-2">Name</th>
                    <th className="px-3 py-2">Host</th>
                    <th className="px-3 py-2">Group</th>
                    <th className="px-3 py-2">Interval</th>
                    <th className="px-3 py-2">Enabled</th>
                    <th className="px-3 py-2">Actions</th>
                  </tr>
                </thead>
                <tbody>
                  {probes.map((probe) => (
                    <tr key={probe.id} className="border-t border-slate-800">
                      <td className="px-3 py-2 font-medium text-slate-100">{probe.name}</td>
                      <td className="px-3 py-2">{probe.host}</td>
                      <td className="px-3 py-2">{probe.group}</td>
                      <td className="px-3 py-2">{probe.probe_interval}s</td>
                      <td className="px-3 py-2">{probe.enabled ? "Yes" : "No"}</td>
                      <td className="px-3 py-2">
                        <div className="flex gap-2">
                          <button
                            type="button"
                            onClick={() => onEditProbe(probe)}
                            className="rounded-md border border-cyan-400/40 bg-cyan-500/10 px-2 py-1 text-xs text-cyan-300 hover:bg-cyan-500/20"
                          >
                            Edit
                          </button>
                          <button
                            type="button"
                            onClick={() => onDeleteProbe(probe)}
                            className="rounded-md border border-red-400/40 bg-red-500/10 px-2 py-1 text-xs text-red-300 hover:bg-red-500/20"
                          >
                            Delete
                          </button>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
