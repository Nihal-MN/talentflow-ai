"use client";

import { useRouter } from "next/navigation";
import { useRef, useState } from "react";

import { api, ApiError } from "@/lib/api";
import { Button } from "@/components/ui/Button";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { Input, Label, Textarea } from "@/components/ui/Fields";
import { InlineError } from "@/components/ui/States";

const SAMPLE_JD = `Senior Full Stack Engineer

Company: Cedar Freight
Location: Dubai, UAE - Hybrid
Employment type: Full-time

About the role
Cedar Freight builds logistics software that moves shipments across the GCC. You will own features end to end, from PostgreSQL schema design to polished React interfaces.

Requirements
- 5+ years of software engineering experience
- Expert-level Python and FastAPI
- Strong React and TypeScript skills
- PostgreSQL and Docker experience
- Experience deploying services on AWS
- Bachelor's degree in Computer Science or a related field

Nice to have
- Kubernetes
- Experience in logistics or supply chain
`;

export function JobForm() {
  const router = useRouter();
  const [mode, setMode] = useState<"paste" | "upload">("paste");
  const [title, setTitle] = useState("");
  const [company, setCompany] = useState("");
  const [jdText, setJdText] = useState("");
  const [file, setFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);

  async function handleSubmit(event: React.FormEvent) {
    event.preventDefault();
    setError(null);

    if (mode === "paste" && jdText.trim().length < 30) {
      setError("Paste a job description first — at least a few lines so requirements can be extracted.");
      return;
    }
    if (mode === "upload" && !file) {
      setError("Choose a PDF, DOCX or TXT file to upload.");
      return;
    }

    setSubmitting(true);
    try {
      const job =
        mode === "paste"
          ? await api.jobs.create({
              title: title || undefined,
              company,
              jd_text: jdText,
            })
          : await api.jobs.upload(file as File, { title: title || undefined, company });
      router.push(`/jobs/${job.id}`);
    } catch (err) {
      setError(err instanceof ApiError ? err.message : "Could not create the job. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <Card>
      <CardHeader
        title="New job"
        subtitle="Paste the description or upload a file — structured requirements are extracted automatically."
      />
      <CardBody>
        <div className="mb-5 flex gap-1 rounded-lg bg-slate-100 p-1" role="tablist">
          {(["paste", "upload"] as const).map((tab) => (
            <button
              key={tab}
              role="tab"
              aria-selected={mode === tab}
              onClick={() => setMode(tab)}
              className={`flex-1 rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${
                mode === tab ? "bg-white text-slate-900 shadow-sm" : "text-slate-500 hover:text-slate-700"
              }`}
            >
              {tab === "paste" ? "Paste text" : "Upload file"}
            </button>
          ))}
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="grid gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="job-title" hint="optional — inferred from the text when blank">
                Job title
              </Label>
              <Input
                id="job-title"
                value={title}
                onChange={(event) => setTitle(event.target.value)}
                placeholder="e.g. Senior Full Stack Engineer"
              />
            </div>
            <div>
              <Label htmlFor="job-company" hint="optional">
                Company
              </Label>
              <Input
                id="job-company"
                value={company}
                onChange={(event) => setCompany(event.target.value)}
                placeholder="e.g. Cedar Freight"
              />
            </div>
          </div>

          {mode === "paste" ? (
            <div>
              <div className="mb-1 flex items-center justify-between">
                <Label htmlFor="job-jd">Job description</Label>
                <button
                  type="button"
                  onClick={() => setJdText(SAMPLE_JD)}
                  className="text-xs font-medium text-indigo-600 hover:underline"
                >
                  Use a sample JD
                </button>
              </div>
              <Textarea
                id="job-jd"
                rows={12}
                value={jdText}
                onChange={(event) => setJdText(event.target.value)}
                placeholder={"Paste the full job description here…\n\nInclude a Requirements section for the best extraction."}
              />
            </div>
          ) : (
            <div>
              <Label htmlFor="job-file" hint="PDF, DOCX or TXT · max 10 MB">
                Job description file
              </Label>
              <input
                id="job-file"
                ref={fileInput}
                type="file"
                accept=".pdf,.docx,.txt,.md"
                onChange={(event) => setFile(event.target.files?.[0] ?? null)}
                className="block w-full cursor-pointer rounded-lg border border-dashed border-slate-300 bg-slate-50 px-3 py-6 text-sm text-slate-600 file:mr-3 file:rounded-md file:border-0 file:bg-indigo-50 file:px-3 file:py-1.5 file:text-xs file:font-medium file:text-indigo-700 hover:border-indigo-300"
              />
              {file ? <p className="mt-1 text-xs text-slate-500">Selected: {file.name}</p> : null}
            </div>
          )}

          {error ? <InlineError message={error} /> : null}

          <div className="flex items-center gap-3">
            <Button type="submit" loading={submitting}>
              {submitting ? "Extracting requirements…" : "Create job & extract requirements"}
            </Button>
            <p className="text-xs text-slate-400">
              The draft is validated before it is stored — no raw model output becomes database truth.
            </p>
          </div>
        </form>
      </CardBody>
    </Card>
  );
}
