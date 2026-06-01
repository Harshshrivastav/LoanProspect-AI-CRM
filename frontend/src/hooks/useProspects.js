// src/hooks/useProspects.js
import { useState, useEffect, useCallback } from "react";
import { getProspects } from "../api/client";

export function useProspects(limit = 20) {
  const [prospects, setProspects] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await getProspects(limit);
      setProspects(data.prospects || []);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [limit]);

  useEffect(() => {
    fetch();
  }, [fetch]);

  return { prospects, loading, error, refetch: fetch };
}
