"use client";

import { useMemo, useState } from "react";

import type { Certification, Education, Experience, Skill } from "@/lib/types";
import { formatMonth } from "@/lib/format";

export function SummaryBlock({ summary }: { summary: string | null }) {
  if (!summary) return <p className="text-sm text-slate-400">No summary on the resume.</p>;
  return <p className="text-sm leading-relaxed text-slate-700">{summary}</p>;
}

const CATEGORY_ORDER = [
  "language",
  "framework",
  "database",
  "cloud",
  "devops",
  "data",
  "testing",
  "ai",
  "analytics",
  "tool",
  "soft",
  "other",
];

export function SkillChips({ skills }: { skills: Skill[] }) {
  const [showEvidence, setShowEvidence] = useState<number | null>(null);

  const grouped = useMemo(() => {
    const map = new Map<string, Skill[]>();
    for (const skill of skills) {
      const key = skill.category || "other";
      map.set(key, [...(map.get(key) ?? []), skill]);
    }
    return [...map.entries()].sort(
      (a, b) => CATEGORY_ORDER.indexOf(a[0]) - CATEGORY_ORDER.indexOf(b[0]),
    );
  }, [skills]);

  if (skills.length === 0) return <p className="text-sm text-slate-400">No skills extracted.</p>;

  return (
    <div className="space-y-3">
      {grouped.map(([category, categorySkills]) => (
        <div key={category}>
          <p className="mb-1 text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            {category}
          </p>
          <div className="flex flex-wrap gap-1.5">
            {categorySkills.map((skill) => (
              <button
                key={skill.id}
                type="button"
                onClick={() => setShowEvidence(showEvidence === skill.id ? null : skill.id)}
                title={skill.evidence ?? "No direct evidence line"}
                className={`rounded-md px-2 py-0.5 text-xs transition-colors ${
                  skill.evidence
                    ? "bg-indigo-50 text-indigo-700 hover:bg-indigo-100"
                    : "bg-slate-100 text-slate-600 hover:bg-slate-200"
                }`}
              >
                {skill.name}
              </button>
            ))}
          </div>
          {categorySkills.some((skill) => skill.id === showEvidence && skill.evidence) ? (
            <p className="mt-1.5 rounded-md bg-slate-50 px-2.5 py-1.5 text-xs italic text-slate-600">
              “{categorySkills.find((skill) => skill.id === showEvidence)?.evidence}”
            </p>
          ) : null}
        </div>
      ))}
    </div>
  );
}

export function ExperienceTimeline({ experiences }: { experiences: Experience[] }) {
  if (experiences.length === 0) return <p className="text-sm text-slate-400">No roles extracted.</p>;
  return (
    <ol className="relative space-y-4 border-l border-slate-200 pl-4">
      {experiences.map((experience) => (
        <li key={experience.id} className="relative">
          <span
            aria-hidden
            className={`absolute -left-[21px] top-1.5 size-2.5 rounded-full ring-2 ring-white ${
              experience.is_current ? "bg-emerald-500" : "bg-slate-300"
            }`}
          />
          <p className="text-sm font-medium text-slate-900">
            {experience.title ?? "Role"}
            {experience.company ? <span className="text-slate-500"> · {experience.company}</span> : null}
          </p>
          <p className="text-xs text-slate-400">
            {formatMonth(experience.start_date)} – {experience.is_current ? "Present" : formatMonth(experience.end_date)}
            {experience.location ? ` · ${experience.location}` : ""}
          </p>
          {experience.description ? (
            <ul className="mt-1.5 space-y-1">
              {experience.description.split("\n").map((line, index) => (
                <li key={index} className="text-sm leading-snug text-slate-600">
                  {line}
                </li>
              ))}
            </ul>
          ) : null}
        </li>
      ))}
    </ol>
  );
}

export function EducationList({ educations }: { educations: Education[] }) {
  if (educations.length === 0) return <p className="text-sm text-slate-400">No education entries.</p>;
  return (
    <ul className="space-y-2">
      {educations.map((education) => (
        <li key={education.id} className="text-sm text-slate-700">
          <span className="font-medium">{education.degree ?? "Studies"}</span>
          {education.institution ? <span className="text-slate-500"> · {education.institution}</span> : null}
          {education.start_year || education.end_year ? (
            <span className="text-xs text-slate-400">
              {" "}
              ({education.start_year ?? "?"}–{education.end_year ?? "?"})
            </span>
          ) : null}
        </li>
      ))}
    </ul>
  );
}

export function CertificationsList({ certifications }: { certifications: Certification[] }) {
  if (certifications.length === 0) return <p className="text-sm text-slate-400">No certifications.</p>;
  return (
    <ul className="space-y-1.5">
      {certifications.map((certification) => (
        <li key={certification.id} className="text-sm text-slate-700">
          {certification.name}
          {certification.year ? <span className="text-xs text-slate-400"> · {certification.year}</span> : null}
        </li>
      ))}
    </ul>
  );
}

export function ResumeTextCard({ text, filename }: { text: string | null; filename: string | null }) {
  if (!text) return null;
  return (
    <details className="group">
      <summary className="cursor-pointer text-sm font-medium text-indigo-600 hover:underline">
        Show original resume text{filename ? ` (${filename})` : ""}
      </summary>
      <pre className="mt-3 max-h-96 overflow-y-auto whitespace-pre-wrap rounded-lg bg-slate-50 p-4 text-xs leading-relaxed text-slate-700">
        {text}
      </pre>
    </details>
  );
}
