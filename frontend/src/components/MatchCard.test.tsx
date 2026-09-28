import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { MatchCard } from "@/components/matching/MatchCard";
import { StageControls } from "@/components/pipeline/StageControls";
import { StageBadge, StatusBadge } from "@/components/ui/Badge";
import type { MatchResult } from "@/lib/types";

const MATCH: MatchResult = {
  candidate_id: 1,
  candidate_name: "Amira Haddad",
  job_id: 1,
  job_title: "Senior Full Stack Engineer",
  application_id: null,
  stage: null,
  composite_score: 82.5,
  components: { must_have: 0.9, preferred: 0.5, experience: 1, domain: 1 },
  weights_used: { must_have: 0.6, preferred: 0.2, experience: 0.1, domain: 0.1 },
  formula: "0.60·must_have[90%] + 0.20·preferred[50%] + 0.10·experience[100%] + 0.10·domain[100%] = 82.5/100 (weights re-normalized over present components)",
  coverage: {
    must_have: { met: 9, partial: 0, missing: 1, unknown: 0, advisory: 0, total: 10 },
    preferred: { met: 1, partial: 1, missing: 0, unknown: 0, advisory: 0, total: 2 },
  },
  semantic_similarity: 0.42,
  engine_version: "matching-engine-v1",
  generated_at: "2026-09-28T10:00:00+00:00",
  requirements: [
    {
      requirement_id: 11,
      kind: "must_have",
      category: "skill",
      label: "Expert-level Python and FastAPI",
      status: "met",
      reason: "Skill 'python' is present in the candidate's profile.",
      skill: "python",
      similarity: null,
      evidence: [
        {
          snippet: "Led the migration of the shipment tracking platform to Python and FastAPI",
          source: "skills",
          match_type: "lexical",
          detail: "skill 'python' extracted from the resume",
        },
      ],
    },
    {
      requirement_id: 12,
      kind: "must_have",
      category: "skill",
      label: "Kubernetes in production",
      status: "missing",
      reason: "No evidence of 'kubernetes' in the candidate's profile or resume.",
      skill: "kubernetes",
      similarity: null,
      evidence: [],
    },
  ],
};

describe("MatchCard", () => {
  it("shows the score, formula, coverage and evidence", () => {
    render(<MatchCard match={MATCH} />);

    expect(screen.getByText("Amira Haddad")).toBeInTheDocument();
    expect(screen.getByText("82.5")).toBeInTheDocument();
    expect(screen.getByText(/weights re-normalized/)).toBeInTheDocument();
    expect(screen.getByText(/9\/10 must-haves met/)).toBeInTheDocument();

    // Requirement statuses are visible and expandable to evidence.
    expect(screen.getByText("python")).toBeInTheDocument();
    fireEvent.click(screen.getByText(/Expert-level Python and FastAPI/));
    expect(screen.getByText(/shipment tracking platform to Python/)).toBeInTheDocument();

    // A concrete miss is explainable too — with its written reason.
    fireEvent.click(screen.getByText(/Kubernetes in production/));
    expect(screen.getByText(/No evidence of 'kubernetes'/)).toBeInTheDocument();
  });

  it("offers 'Add to pipeline' only when not already in the pipeline", () => {
    const { rerender } = render(<MatchCard match={MATCH} />);
    expect(screen.getByRole("button", { name: /add to pipeline/i })).toBeInTheDocument();

    rerender(<MatchCard match={{ ...MATCH, application_id: 7, stage: "SCREENING" }} />);
    expect(screen.queryByRole("button", { name: /add to pipeline/i })).not.toBeInTheDocument();
    expect(screen.getByText("in pipeline")).toBeInTheDocument();
  });
});

describe("StageControls", () => {
  it("moves to the next stage via the advancement button", async () => {
    const onMove = vi.fn().mockResolvedValue(undefined);
    render(<StageControls stage="SCREENING" onMove={onMove} />);

    fireEvent.click(screen.getByRole("button", { name: /shortlisted/i }));
    expect(onMove).toHaveBeenCalledWith("SHORTLISTED", undefined);
  });

  it("supports rejection and reopening", () => {
    const onMove = vi.fn().mockResolvedValue(undefined);
    const { rerender } = render(<StageControls stage="INTERVIEW" onMove={onMove} />);

    fireEvent.click(screen.getByRole("button", { name: /reject/i }));
    expect(onMove).toHaveBeenCalledWith("REJECTED", undefined);

    rerender(<StageControls stage="REJECTED" onMove={onMove} />);
    expect(screen.getByRole("button", { name: /reopen/i })).toBeInTheDocument();
  });
});

describe("badges", () => {
  it("renders human stage labels", () => {
    render(<StageBadge stage="SHORTLISTED" />);
    expect(screen.getByText("Shortlisted")).toBeInTheDocument();
  });

  it("renders requirement status labels", () => {
    render(<StatusBadge status="partial" />);
    expect(screen.getByText("Partial")).toBeInTheDocument();
  });
});
