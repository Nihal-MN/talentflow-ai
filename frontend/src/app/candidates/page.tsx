"use client";

import Link from "next/link";
import { useCallback, useRef, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { useApi } from "@/hooks/useApi";
import { Badge, MethodBadge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader, PageHeader } from "@/components/ui/Card";
import { Input } from "@/components/ui/Fields";
import { EmptyState, ErrorState, InlineError, LoadingBlock } from "@/components/ui/States";
import { formatDate, formatYears } from "@/lib/format";

interface UploadItem {
  id: number;
  name: string;
  state: "uploading" | "done" | "error";
  message?: string;
}

export default function CandidatesPage() {
  const [query, setQuery] = useState("");
  const { data, error, loading, reload } = useApi(() => api.candidates.list({ q: query || undefined }), [query]);
  const [uploads, setUploads] = useState<UploadItem[]>([]);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const uploadId = useRef(0);

  const handleFiles = useCallback(
    async (fileList: FileList | null) => {
      if (!fileList || fileList.length === 0) return;
      // Snapshot the files NOW: the input is cleared right after the change
      // event, which empties the live FileList and would otherwise silently
      // drop every file after the first one.
      const files = Array.from(fileList);
      setUploadError(null);
      const items: UploadItem[] = files.map((file) => ({
        id: ++uploadId.current,
        name: file.name,
        state: "uploading" as const,
      }));
      setUploads((previous) => [...items, ...previous]);

      for (let index = 0; index < files.length; index += 1) {
        const file = files[index];
        const item = items[index];
        try {
          const candidate = await api.candidates.upload(file);
          setUploads((previous) =>
            previous.map((entry) =>
              entry.id === item.id
                ? { ...entry, state: "done", message: `Extracted: ${candidate.full_name}` }
                : entry,
            ),
          );
        } catch (err) {
          const message = err instanceof ApiError ? err.message : "Upload failed";
          setUploads((previous) =>
            previous.map((entry) => (entry.id === item.id ? { ...entry, state: "error", message } : entry)),
          );
        }
      }
      reload();
    },
    [reload],
  );

  return (
    <div>
      <PageHeader
        title="Candidates"
        subtitle="Resumes in PDF, DOCX or TXT are parsed into validated structured profiles — every extracted skill keeps its evidence."
      />

      <Card className="mb-6">
        <CardHeader
          title="Upload resumes"
          subtitle="Drop several files at once — each one goes through the full ingestion pipeline."
        />
        <CardBody>
          <input
            type="file"
            multiple
            accept=".pdf,.docx,.txt,.md"
            onChange={(event) => {
              void handleFiles(event.target.files);
              event.target.value = "";
            }}
            className="block w-full cursor-pointer rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-indigo-700 hover:border-indigo-300"
          />
          {uploadError ? <div className="mt-3"><InlineError message={uploadError} /></div> : null}
          {uploads.length > 0 ? (
            <ul className="mt-3 space-y-1">
              {uploads.slice(0, 6).map((item) => (
                <li key={item.id} className="flex items-center gap-2 text-xs">
                  <Badge
                    className={
                      item.state === "done"
                        ? "bg-emerald-50 text-emerald-700 ring-emerald-200"
                        : item.state === "error"
                          ? "bg-rose-50 text-rose-700 ring-rose-200"
                          : "bg-slate-100 text-slate-600 ring-slate-200"
                    }
                  >
                    {item.state === "uploading" ? "parsing…" : item.state === "done" ? "done" : "error"}
                  </Badge>
                  <span className="font-medium text-slate-700">{item.name}</span>
                  <span className="truncate text-slate-400">{item.message}</span>
                </li>
              ))}
            </ul>
          ) : null}
        </CardBody>
      </Card>

      <div className="mb-4">
        <Input
          type="search"
          placeholder="Search by name, headline or location…"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          className="max-w-sm"
        />
      </div>

      {loading && !data ? (
        <LoadingBlock lines={5} />
      ) : error && !data ? (
        <ErrorState error={error} onRetry={reload} />
      ) : data && data.length === 0 ? (
        <EmptyState
          title={query ? "No candidates match your search" : "No candidates yet"}
          description={
            query
              ? "Try a different search term."
              : "Upload resumes above (or run the demo seed) — profiles appear here once parsed."
          }
        />
      ) : data ? (
        <Card>
          <div className="overflow-x-auto">
            <table className="min-w-full divide-y divide-slate-200 text-sm">
              <thead>
                <tr className="text-left text-xs uppercase tracking-wide text-slate-500">
                  <th className="px-5 py-3 font-medium">Candidate</th>
                  <th className="px-4 py-3 font-medium">Experience</th>
                  <th className="px-4 py-3 font-medium">Top skills</th>
                  <th className="px-4 py-3 font-medium">Pipeline</th>
                  <th className="px-4 py-3 font-medium">Added</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100">
                {data.map((candidate) => (
                  <tr key={candidate.id} className="hover:bg-slate-50/70">
                    <td className="px-5 py-3">
                      <Link
                        href={`/candidates/${candidate.id}`}
                        className="font-medium text-slate-900 hover:text-indigo-600"
                      >
                        {candidate.full_name}
                      </Link>
                      <div className="mt-0.5 flex items-center gap-2 text-xs text-slate-500">
                        <span className="truncate">{candidate.headline ?? "—"}</span>
                        <MethodBadge method={candidate.extraction_method} />
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">
                      <div>{formatYears(candidate.years_experience)}</div>
                      <div className="text-xs text-slate-400">{candidate.location ?? "—"}</div>
                    </td>
                    <td className="px-4 py-3">
                      <div className="flex max-w-xs flex-wrap gap-1">
                        {candidate.skills.slice(0, 5).map((skill) => (
                          <span
                            key={skill}
                            className="rounded-md bg-slate-100 px-1.5 py-0.5 text-[11px] text-slate-600"
                          >
                            {skill}
                          </span>
                        ))}
                        {candidate.skills.length > 5 ? (
                          <span className="text-[11px] text-slate-400">
                            +{candidate.skills.length - 5} more
                          </span>
                        ) : null}
                      </div>
                    </td>
                    <td className="px-4 py-3 text-slate-600">{candidate.applications_count}</td>
                    <td className="px-4 py-3 text-slate-500">{formatDate(candidate.created_at)}</td>
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
