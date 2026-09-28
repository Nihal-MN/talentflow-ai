"use client";

import { PageHeader } from "@/components/ui/Card";
import { JobForm } from "@/components/jobs/JobForm";

export default function NewJobPage() {
  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Create a job"
        subtitle="Paste a job description or upload a file. Requirements are extracted into must-have and preferred, with skills normalized for matching."
      />
      <JobForm />
    </div>
  );
}
