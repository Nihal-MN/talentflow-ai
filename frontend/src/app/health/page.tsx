"use client";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { ErrorState, LoadingBlock } from "@/components/ui/States";
import { StatCard } from "@/components/ui/StatCard";

function StatusPill({ ok, label }: { ok: boolean; label: string }) {
  return (
    <Badge
      className={
        ok
          ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
          : "bg-rose-50 text-rose-700 ring-rose-200"
      }
    >
      <span aria-hidden className={`size-1.5 rounded-full ${ok ? "bg-emerald-500" : "bg-rose-500"}`} />
      {label}
    </Badge>
  );
}

export default function HealthPage() {
  const { data: health, error, loading, reload } = useApi(() => api.health.full(), []);

  return (
    <div>
      <PageHeader
        title="System health"
        subtitle="Live dependency checks — database, AI configuration and data counts. Secrets are never exposed here."
        action={
          <Button variant="secondary" size="sm" onClick={reload} loading={loading}>
            Refresh
          </Button>
        }
      />

      {loading && !health ? (
        <LoadingBlock lines={6} />
      ) : error && !health ? (
        <div className="space-y-4">
          <ErrorState error={error} onRetry={reload} />
          <p className="text-sm text-slate-500">
            The API did not respond. If you run the stack locally, check{" "}
            <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">docker compose ps</code> or start
            the backend with <code className="rounded bg-slate-100 px-1.5 py-0.5 text-xs">make dev</code>.
          </p>
        </div>
      ) : health ? (
        <div className="space-y-6">
          <div
            className={`rounded-xl border px-5 py-4 ${
              health.status === "ok"
                ? "border-emerald-200 bg-emerald-50/60"
                : "border-amber-200 bg-amber-50/60"
            }`}
          >
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold text-slate-900">
                  {health.status === "ok"
                    ? "All systems operational"
                    : "Degraded — one or more dependencies need attention"}
                </h2>
                <p className="mt-0.5 text-xs text-slate-500">
                  {health.app} v{health.version} · checked {new Date(health.time).toLocaleString("en-GB")}
                </p>
              </div>
              <StatusPill ok={health.status === "ok"} label={health.status.toUpperCase()} />
            </div>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
            <StatCard label="Jobs" value={health.counts.jobs} hint={`${health.counts.open_jobs} open`} accent="indigo" />
            <StatCard label="Candidates" value={health.counts.candidates} />
            <StatCard label="Applications" value={health.counts.applications} accent="violet" />
            <StatCard
              label="DB latency"
              value={health.database.latency_ms !== null ? `${health.database.latency_ms} ms` : "—"}
              hint={health.database.dialect}
              accent="emerald"
            />
          </div>

          <div className="grid gap-6 lg:grid-cols-2">
            <Card>
              <CardHeader title="Database" subtitle="Connectivity and dialect" />
              <CardBody className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Status</span>
                  <StatusPill ok={health.database.status === "ok"} label={health.database.status} />
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Dialect</span>
                  <span className="font-mono text-xs text-slate-700">{health.database.dialect}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Round-trip</span>
                  <span className="font-mono text-xs text-slate-700">
                    {health.database.latency_ms !== null ? `${health.database.latency_ms} ms` : "—"}
                  </span>
                </div>
                {health.database.detail ? (
                  <p className="rounded-md bg-rose-50 px-2.5 py-1.5 text-xs text-rose-700">
                    {health.database.detail}
                  </p>
                ) : null}
                <p className="text-xs text-slate-400">
                  PostgreSQL + pgvector in Docker; SQLite for zero-setup local dev. If degraded,{" "}
                  <code className="rounded bg-slate-100 px-1 py-0.5">docker compose logs db</code> helps.
                </p>
              </CardBody>
            </Card>

            <Card>
              <CardHeader title="AI configuration" subtitle="Provider, models and key state (no secrets)" />
              <CardBody className="space-y-3 text-sm">
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Mode</span>
                  <Badge className="bg-slate-100 text-slate-700 ring-slate-200">{health.ai.mode}</Badge>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Provider</span>
                  <span className="font-mono text-xs text-slate-700">{health.ai.provider}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Model</span>
                  <span className="font-mono text-xs text-slate-700">{health.ai.model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">Embeddings</span>
                  <span className="font-mono text-xs text-slate-700">{health.ai.embedding_model}</span>
                </div>
                <div className="flex items-center justify-between">
                  <span className="text-slate-500">OpenAI key configured</span>
                  <StatusPill ok={health.ai.api_key_configured} label={health.ai.api_key_configured ? "yes" : "no"} />
                </div>
                {health.ai.provider === "mock" ? (
                  <p className="text-xs text-slate-400">
                    Running in deterministic mock mode — set{" "}
                    <code className="rounded bg-slate-100 px-1 py-0.5">OPENAI_API_KEY</code> in{" "}
                    <code className="rounded bg-slate-100 px-1 py-0.5">.env</code> and restart to use the
                    OpenAI API. Extraction output is labeled per record either way.
                  </p>
                ) : null}
                {health.ai.misconfigured ? (
                  <p className="rounded-md bg-amber-50 px-2.5 py-1.5 text-xs text-amber-800">
                    AI_PROVIDER=openai but no key is configured — requests will fail until the key is set.
                  </p>
                ) : null}
              </CardBody>
            </Card>
          </div>
        </div>
      ) : null}
    </div>
  );
}
