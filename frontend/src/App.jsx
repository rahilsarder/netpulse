import {
  ArrowPathIcon,
  ExclamationTriangleIcon,
  GlobeAltIcon,
} from "@heroicons/react/24/outline";
import { useEffect, useMemo, useState } from "react";

import LatencyTrendChart from "./charts/LatencyTrendChart";
import IncidentsPanel from "./components/IncidentsPanel";
import KpiCard from "./components/KpiCard";
import ProbeManagementModal from "./components/ProbeManagementModal";
import ProbeStatusTable from "./components/ProbeStatusTable";
import { apiClient } from "./api/client";
import { useDashboardData } from "./hooks/useDashboardData";

const DURATION_OPTIONS = [
  { label: "5m", value: "5m", minutes: 5 },
  { label: "30m", value: "30m", minutes: 30 },
  { label: "6h", value: "6h", minutes: 6 * 60 },
  { label: "24h", value: "24h", minutes: 24 * 60 },
  { label: "1w", value: "1w", minutes: 7 * 24 * 60 },
  { label: "1m", value: "1m", minutes: 30 * 24 * 60 },
];

export default function App() {
  const { kpis, probes, results, incidents, isLoading, error, reload } = useDashboardData();
  const [activeProbe, setActiveProbe] = useState(null);
  const [isSubmittingProbe, setIsSubmittingProbe] = useState(false);
  const [mutationError, setMutationError] = useState(null);
  const [isProbeModalOpen, setIsProbeModalOpen] = useState(false);
  const [selectedProbeId, setSelectedProbeId] = useState(null);
  const [selectedDuration, setSelectedDuration] = useState("24h");
  const [selectedProbeHistory, setSelectedProbeHistory] = useState([]);
  const [isHistoryLoading, setIsHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState(null);

  useEffect(() => {
    if (!probes.length) {
      setSelectedProbeId(null);
      setSelectedProbeHistory([]);
      return;
    }

    const hasSelectedProbe = probes.some((probe) => probe.id === selectedProbeId);
    if (!hasSelectedProbe) {
      setSelectedProbeId(probes[0].id);
    }
  }, [probes, selectedProbeId]);

  useEffect(() => {
    if (!selectedProbeId) {
      return;
    }

    let cancelled = false;

    async function loadProbeHistory() {
      setIsHistoryLoading(true);
      setHistoryError(null);
      try {
        const duration = DURATION_OPTIONS.find((item) => item.value === selectedDuration);
        const minutes = duration?.minutes ?? 24 * 60;
        const history = await apiClient.getProbeHistory(selectedProbeId, minutes, "default");
        if (!cancelled) {
          setSelectedProbeHistory(history);
        }
      } catch (fetchError) {
        if (!cancelled) {
          setHistoryError(
            fetchError instanceof Error ? fetchError.message : "Failed to load probe history."
          );
        }
      } finally {
        if (!cancelled) {
          setIsHistoryLoading(false);
        }
      }
    }

    loadProbeHistory();
    const intervalId = window.setInterval(loadProbeHistory, 5000);

    return () => {
      cancelled = true;
      window.clearInterval(intervalId);
    };
  }, [selectedProbeId, selectedDuration]);

  const selectedProbe = useMemo(
    () => probes.find((probe) => probe.id === selectedProbeId) ?? null,
    [probes, selectedProbeId]
  );

  async function handleProbeSubmit(formData) {
    const payload = {
      name: String(formData.name ?? "").trim(),
      host: String(formData.host ?? "").trim(),
      group: String(formData.group ?? "Default").trim() || "Default",
      probe_interval: Number(formData.probe_interval),
      latency_threshold: Number(formData.latency_threshold),
      packet_loss_threshold: Number(formData.packet_loss_threshold),
      enabled: Boolean(formData.enabled),
    };

    if (!payload.name || !payload.host) {
      setMutationError("Probe name and host are required.");
      return;
    }

    setIsSubmittingProbe(true);
    setMutationError(null);
    try {
      if (activeProbe?.id) {
        await apiClient.updateProbe(activeProbe.id, payload);
      } else {
        await apiClient.createProbe(payload);
      }
      setActiveProbe(null);
      await reload();
    } catch (submitError) {
      setMutationError(submitError instanceof Error ? submitError.message : "Save failed.");
    } finally {
      setIsSubmittingProbe(false);
    }
  }

  function handleEditProbe(probe) {
    setMutationError(null);
    setActiveProbe(probe);
    setIsProbeModalOpen(true);
  }

  async function handleDeleteProbe(probe) {
    const confirmed = window.confirm(
      `Delete probe "${probe.name}" (${probe.host})? This action cannot be undone.`
    );
    if (!confirmed) {
      return;
    }

    setMutationError(null);
    setIsSubmittingProbe(true);
    try {
      await apiClient.deleteProbe(probe.id);
      if (activeProbe?.id === probe.id) {
        setActiveProbe(null);
      }
      await reload();
    } catch (deleteError) {
      setMutationError(deleteError instanceof Error ? deleteError.message : "Delete failed.");
    } finally {
      setIsSubmittingProbe(false);
    }
  }

  return (
    <main className="min-h-screen bg-gradient-to-b from-slate-950 via-slate-950 to-slate-900 px-4 py-6 text-slate-100 md:px-8">
      <div className="mx-auto flex w-full max-w-7xl flex-col gap-6">
        <header className="flex flex-col gap-4 rounded-2xl border border-cyan-500/30 bg-slate-900/70 p-6 shadow-glow backdrop-blur-sm md:flex-row md:items-center md:justify-between">
          <div>
            <p className="text-xs uppercase tracking-[0.24em] text-cyan-300">NetPulse</p>
            <h1 className="mt-2 text-3xl font-semibold">ISP Destination Monitoring</h1>
            <p className="mt-2 text-sm text-slate-400">
              Real-time latency, loss, and incident intelligence dashboard.
            </p>
          </div>
          <div className="flex gap-2">
            <button
              type="button"
              onClick={() => apiClient.runMonitorOnce().then(reload)}
              className="inline-flex items-center gap-2 rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-200 hover:border-cyan-400 hover:text-cyan-300"
            >
              <ArrowPathIcon className="h-4 w-4" />
              Run check
            </button>
            <button
              type="button"
              onClick={reload}
              className="rounded-xl border border-cyan-400/40 bg-cyan-500/10 px-4 py-2 text-sm text-cyan-300 hover:bg-cyan-500/20"
            >
              Refresh
            </button>
            <button
              type="button"
              onClick={() => {
                setMutationError(null);
                setActiveProbe(null);
                setIsProbeModalOpen(true);
              }}
              className="rounded-xl border border-slate-700 bg-slate-950 px-4 py-2 text-sm text-slate-200 hover:border-cyan-400 hover:text-cyan-300"
            >
              Manage probes
            </button>
          </div>
        </header>

        {error ? (
          <div className="rounded-2xl border border-red-500/40 bg-red-500/10 p-4 text-sm text-red-200">
            API error: {error}
          </div>
        ) : null}

        <section className="grid gap-4 md:grid-cols-3 lg:grid-cols-6">
          <KpiCard title="Total Probes" value={kpis?.total_probes ?? "-"} />
          <KpiCard title="Active Incidents" value={kpis?.active_incidents ?? "-"} accent="yellow" />
          <KpiCard title="Targets Down" value={kpis?.targets_down ?? "-"} accent="red" />
          <KpiCard title="Degraded" value={kpis?.targets_degraded ?? "-"} accent="yellow" />
          <KpiCard title="Avg Latency (ms)" value={kpis?.average_latency ?? "-"} />
          <KpiCard title="Avg Loss (%)" value={kpis?.average_packet_loss ?? "-"} />
        </section>

        <section className="grid gap-4 lg:grid-cols-3">
          <div className="lg:col-span-2">
            <LatencyTrendChart
              selectedProbeName={selectedProbe?.name ?? null}
              durationOptions={DURATION_OPTIONS}
              selectedDuration={selectedDuration}
              onSelectDuration={setSelectedDuration}
              results={selectedProbeHistory}
              isLoading={isHistoryLoading}
              error={historyError}
            />
          </div>
          <IncidentsPanel incidents={incidents} />
        </section>

        <ProbeStatusTable
          probes={probes}
          latestResults={results}
          selectedProbeId={selectedProbeId}
          onSelectProbe={setSelectedProbeId}
        />

        <footer className="flex items-center justify-between text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <GlobeAltIcon className="h-4 w-4" />
            <span>Dark-mode first NOC interface</span>
          </div>
          <div className="flex items-center gap-2">
            <ExclamationTriangleIcon className="h-4 w-4" />
            <span>{isLoading ? "Refreshing data..." : "Live polling every 5s"}</span>
          </div>
        </footer>
      </div>

      <ProbeManagementModal
        isOpen={isProbeModalOpen}
        probes={probes}
        activeProbe={activeProbe}
        onClose={() => {
          setIsProbeModalOpen(false);
          setActiveProbe(null);
          setMutationError(null);
        }}
        onSubmitProbe={handleProbeSubmit}
        onCancelEdit={() => setActiveProbe(null)}
        onEditProbe={handleEditProbe}
        onDeleteProbe={handleDeleteProbe}
        isSubmitting={isSubmittingProbe}
        mutationError={mutationError}
      />
    </main>
  );
}
