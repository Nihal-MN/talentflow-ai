"use client";

import Link from "next/link";
import { useState } from "react";

import { api } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, MethodBadge } from "@/components/ui/Badge";
import { Card, PageHeader } from "@/components/ui/Card";
import { LinkButton } from "@/components/ui/Button";
import { Input } from "@/components/ui/Fields";
import { EmptyState, ErrorState, LoadingBlock } from "@/components/ui/States";
import { formatDate } from "@/lib/format";

function loadJobs(status: string, query: string) {
  return api.jobs.list({
    status: status || undefined,
    q: query || undefined,
  });
}

export default function JobsPage() {
  const [status, setStatus] = useState("");
  const [query, setQuery] = useState("");
  const { data, error, loading, reload } = useApi(() => loadJobs(status, query), [status, query]);

  return (
    <div>
      <PageHeader
        title="Jobs"
        subtitle="Every posting below was created from pasted text or an uploaded file, with requirements extracted and validated."
        action={<LinkButton href="/jobs/new" size="sm">Create job</LinkButton>}
      />

      <div className="mb-4 flex flex-wrap items-center gap-2">
        <Input
          type="search"
          placeholder="Search title or company…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="max-w-xs"
        />
        <select
          aria-label="Filter by status"
          value={status}
          onChange={(event) => setStatus(event.target.value)}
          className="rounded-lg border-0 bg-white px-3 py-2 text-sm shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-indigo-600"
        >
          <option value="">All statuses</option>
          <option value="open">Open</option>
          <option value="paused">Paused</option>
          <option value="closed">Closed</option>
        </select>
      </div>

      {loading && !data ? (
        <LoadingBlock lines={5} />
      ) : error && !data ? (
        <ErrorState error={error} onRetry={reload} />
      ) : data && data.length === 0 ? (
        <EmptyState
          title="No jobs yet"
          description="Create your first job posting by pasting a description or uploading a file — the AI layer extracts structured requirements automatically."
          action={<LinkButton href="/jobs/new" size="sm">Create your first job</LinkButton>}
        />
      ) : data ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3 font-medium">Role</th>
                  <th className="px-4 py-3 font-medium">Location</th>
                  <th className="px-4 py-3 font-medium">Requirements</th>
                  <th className="px-4 py-3 font-medium">Pipeline</th>
                  <th className="px-4 py-3 font-medium">Status</th>
                  <th className="px-4 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.map((job) => (
                  <tr key={job.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3">
                      <Link
                        href={`/jobs/${job.id}`}
                        className="font-medium text-slate-900 hover:text-indigo-600"
                      >
                        {job.title}
                      </Link>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                        <span>{job.company || "—"}</span>
                        <MethodBadge method={job.extraction_method} />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{job.location ?? "—"}</td>
                    <td className="px-4 py-3">
                      <span className="text-slate-700">{job.must_have_count} must</span>
                      <span className="text-slate-400"> · {job.preferred_count} preferred</span>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{job.applications_count}</td>
                    <td className="px-4 py-3">
                      <Badge
                        className={
                          job.status === "open"
                            ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                            : job.status === "paused"
                              ? "bg-amber-50 text-amber-800 ring-amber-200"
                              : "bg-slate-100 text-slate-600 ring-slate-200"
                        }
                      >
                        {job.status}
                      </Badge>
                    </td>
                    <td className="px-4 py-3 text-slate-500">{formatDate(job.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      ) : null}
    </div>
  );
}
