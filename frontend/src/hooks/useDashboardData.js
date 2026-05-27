import { useCallback, useEffect, useState } from "react";

import { apiClient } from "../api/client";

const DEFAULT_STATE = {
  kpis: null,
  probes: [],
  results: [],
  incidents: [],
  isLoading: true,
  error: null,
};

export function useDashboardData() {
  const [state, setState] = useState(DEFAULT_STATE);

  const load = useCallback(async () => {
    setState((previous) => ({ ...previous, isLoading: true, error: null }));
    try {
      const [kpis, probes, results, incidents] = await Promise.all([
        apiClient.getKpis(),
        apiClient.getProbes(),
        apiClient.getRecentResults(150),
        apiClient.getIncidents("ACTIVE"),
      ]);
      setState({ kpis, probes, results, incidents, isLoading: false, error: null });
    } catch (error) {
      setState((previous) => ({
        ...previous,
        isLoading: false,
        error: error instanceof Error ? error.message : "Unexpected error",
      }));
    }
  }, []);

  useEffect(() => {
    load();
    const intervalId = window.setInterval(load, 5000);
    return () => window.clearInterval(intervalId);
  }, [load]);

  return { ...state, reload: load };
}
