import { useState, useEffect } from 'react';

/**
 * Hook to fetch GeoJSON and stats from the FastAPI backend.
 */
export function useAccessibilityData() {
  const [data, setData] = useState({
    tracts: null,
    parks: null,
    neighborhoods: null,
    stats: null,
    loading: true,
    error: null
  });

  // Determine API base based on environment
  const API_BASE = window.location.hostname === 'localhost'
    ? 'http://localhost:8000/api/v1'
    : '/api/v1';

  useEffect(() => {
    async function fetchData() {
      try {
        const [tractsRes, parksRes, neighRes, statsRes] = await Promise.all([
          fetch(`${API_BASE}/tracts`),
          fetch(`${API_BASE}/parks`),
          fetch(`${API_BASE}/neighborhoods`),
          fetch(`${API_BASE}/stats`)
        ]);

        if (!tractsRes.ok || !parksRes.ok || !neighRes.ok || !statsRes.ok) {
          throw new Error('Failed to fetch data from backend. Ensure main.py is running.');
        }

        setData({
          tracts: await tractsRes.json(),
          parks: await parksRes.json(),
          neighborhoods: await neighRes.json(),
          stats: await statsRes.json(),
          loading: false,
          error: null
        });
      } catch (err) {
        setData(prev => ({ ...prev, loading: false, error: err.message }));
      }
    }

    fetchData();
  }, []);

  return data;
}
