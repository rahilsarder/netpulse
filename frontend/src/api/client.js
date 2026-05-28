const API_BASE = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:5001/api";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { "Content-Type": "application/json", ...(options.headers ?? {}) },
    ...options,
  });
  
  if (!response.ok) {
    const errorPayload = await response.text();
    throw new Error(errorPayload || "Request failed");
  }

  return response.json();
}

export const apiClient = {
  getKpis: () => request("/dashboard/kpis"),
  getProbes: () => request("/probes"),
  getRecentResults: (limit = 100) => request(`/results/recent?limit=${limit}`),
  getProbeHistory: (probeId, minutes = 24 * 60, source = "default") =>
    request(
      `/probes/${probeId}/history?minutes=${minutes}&source=${encodeURIComponent(source)}`
    ),
  getIncidents: (status = "ACTIVE") => request(`/incidents?status=${status}`),
  getAlertSettings: () => request("/settings/alerts"),
  updateAlertSettings: (payload) =>
    request("/settings/alerts", {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  runMonitorOnce: () => request("/monitor/run-once", { method: "POST" }),
  createProbe: (payload) =>
    request("/probes", {
      method: "POST",
      body: JSON.stringify(payload),
    }),
  updateProbe: (probeId, payload) =>
    request(`/probes/${probeId}`, {
      method: "PUT",
      body: JSON.stringify(payload),
    }),
  deleteProbe: (probeId) =>
    request(`/probes/${probeId}`, {
      method: "DELETE",
    }),
};
