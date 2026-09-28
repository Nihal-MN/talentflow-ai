"use client";

import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api";

export interface ApiState<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
  reload: () => void;
}

interface Snapshot<T> {
  data: T | null;
  error: ApiError | null;
  loading: boolean;
}

/**
 * Minimal data-fetching hook for client components.
 *
 * `fn` must be stable (define it outside the component or wrap in
 * `useCallback`); the hook refetches when `deps` change. Results arriving out
 * of order are discarded via a request id, so rapid reloads can't clobber
 * newer data. `reload()` re-fetches with a visible loading state; deps-driven
 * refetches are silent (previous data stays on screen until the new arrives).
 */
export function useApi<T>(fn: () => Promise<T>, deps: unknown[] = []): ApiState<T> {
  const [snapshot, setSnapshot] = useState<Snapshot<T>>({ data: null, error: null, loading: true });
  const [tick, setTick] = useState(0);
  const requestId = useRef(0);
  const fnRef = useRef(fn);

  useEffect(() => {
    fnRef.current = fn;
    const id = ++requestId.current;
    let cancelled = false;

    fnRef
      .current()
      .then((data) => {
        if (!cancelled && id === requestId.current) {
          setSnapshot({ data, error: null, loading: false });
        }
      })
      .catch((err: unknown) => {
        if (!cancelled && id === requestId.current) {
          const error = err instanceof ApiError ? err : new ApiError(String(err));
          setSnapshot((previous) => ({ data: previous.data, error, loading: false }));
        }
      });

    return () => {
      cancelled = true;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick]);

  const reload = useCallback(() => {
    setSnapshot((previous) => ({ ...previous, loading: true }));
    setTick((value) => value + 1);
  }, []);

  return { data: snapshot.data, error: snapshot.error, loading: snapshot.loading, reload };
}
