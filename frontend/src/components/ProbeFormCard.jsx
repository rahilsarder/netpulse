import { useEffect, useMemo, useState } from "react";

const DEFAULT_FORM = {
  name: "",
  host: "",
  group: "Default",
  probe_interval: 5,
  latency_threshold: 80,
  packet_loss_threshold: 5,
  enabled: true,
};

export default function ProbeFormCard({
  activeProbe,
  onSubmit,
  onCancelEdit,
  isSubmitting,
  mutationError,
}) {
  const [formState, setFormState] = useState(DEFAULT_FORM);

  const isEditing = useMemo(() => Boolean(activeProbe), [activeProbe]);

  useEffect(() => {
    if (!activeProbe) {
      setFormState(DEFAULT_FORM);
      return;
    }

    setFormState({
      name: activeProbe.name ?? "",
      host: activeProbe.host ?? "",
      group: activeProbe.group ?? "Default",
      probe_interval: Number(activeProbe.probe_interval ?? 5),
      latency_threshold: Number(activeProbe.latency_threshold ?? 80),
      packet_loss_threshold: Number(activeProbe.packet_loss_threshold ?? 5),
      enabled: Boolean(activeProbe.enabled),
    });
  }, [activeProbe]);

  function updateField(field, value) {
    setFormState((previous) => ({
      ...previous,
      [field]: value,
    }));
  }

  function handleSubmit(event) {
    event.preventDefault();
    onSubmit(formState);
  }

  return (
    <div className="rounded-2xl border border-slate-700 bg-slate-900/70 p-5 shadow-glow backdrop-blur-sm">
      <h2 className="text-lg font-semibold text-slate-100">
        {isEditing ? "Edit Probe" : "Add New Probe"}
      </h2>
      <p className="mt-1 text-xs text-slate-400">
        Configure destination, thresholds, and probe interval.
      </p>

      {mutationError ? (
        <div className="mt-4 rounded-xl border border-red-500/40 bg-red-500/10 p-3 text-xs text-red-200">
          {mutationError}
        </div>
      ) : null}

      <form className="mt-4 grid gap-3 md:grid-cols-2" onSubmit={handleSubmit}>
        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Name
          <input
            required
            value={formState.name}
            onChange={(event) => updateField("name", event.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Host/IP
          <input
            required
            value={formState.host}
            onChange={(event) => updateField("host", event.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Group
          <input
            value={formState.group}
            onChange={(event) => updateField("group", event.target.value)}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Probe interval (sec)
          <input
            type="number"
            min={1}
            value={formState.probe_interval}
            onChange={(event) => updateField("probe_interval", Number(event.target.value))}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Latency threshold (ms)
          <input
            type="number"
            min={1}
            value={formState.latency_threshold}
            onChange={(event) => updateField("latency_threshold", Number(event.target.value))}
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="flex flex-col gap-1 text-xs text-slate-300">
          Packet loss threshold (%)
          <input
            type="number"
            min={0}
            max={100}
            value={formState.packet_loss_threshold}
            onChange={(event) =>
              updateField("packet_loss_threshold", Number(event.target.value))
            }
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm text-slate-100 outline-none focus:border-cyan-400"
          />
        </label>

        <label className="col-span-full flex items-center gap-2 text-xs text-slate-300">
          <input
            type="checkbox"
            checked={formState.enabled}
            onChange={(event) => updateField("enabled", event.target.checked)}
          />
          Probe enabled
        </label>

        <div className="col-span-full flex gap-2">
          <button
            type="submit"
            disabled={isSubmitting}
            className="rounded-lg border border-cyan-400/40 bg-cyan-500/10 px-4 py-2 text-xs font-medium text-cyan-300 hover:bg-cyan-500/20 disabled:cursor-not-allowed disabled:opacity-60"
          >
            {isSubmitting ? "Saving..." : isEditing ? "Update probe" : "Create probe"}
          </button>
          {isEditing ? (
            <button
              type="button"
              onClick={onCancelEdit}
              disabled={isSubmitting}
              className="rounded-lg border border-slate-700 bg-slate-950 px-4 py-2 text-xs font-medium text-slate-300 hover:border-slate-500 disabled:cursor-not-allowed disabled:opacity-60"
            >
              Cancel edit
            </button>
          ) : null}
        </div>
      </form>
    </div>
  );
}
