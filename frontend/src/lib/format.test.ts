import { describe, expect, it } from "vitest";

import {
  ADVANCE_STAGES,
  formatYears,
  initials,
  percent,
  scoreTone,
  STAGE_LABELS,
  STAGES,
} from "@/lib/format";

describe("stage constants", () => {
  it("defines the seven pipeline stages in order", () => {
    expect(STAGES).toEqual([
      "NEW",
      "SCREENING",
      "SHORTLISTED",
      "INTERVIEW",
      "OFFER",
      "HIRED",
      "REJECTED",
    ]);
  });

  it("treats REJECTED as an off-ramp, not an advance target", () => {
    expect(ADVANCE_STAGES).not.toContain("REJECTED");
    expect(ADVANCE_STAGES.at(-1)).toBe("HIRED");
  });

  it("has a human label for every stage", () => {
    for (const stage of STAGES) {
      expect(STAGE_LABELS[stage]).toBeTruthy();
    }
  });
});

describe("formatting helpers", () => {
  it("formats years and percentages", () => {
    expect(formatYears(8)).toBe("8 yrs");
    expect(formatYears(8.25)).toBe("8.3 yrs");
    expect(formatYears(null)).toBe("—");
    expect(percent(0.875)).toBe("88%");
    expect(percent(null)).toBe("—");
  });

  it("derives initials from names", () => {
    expect(initials("Amira Haddad")).toBe("AH");
    expect(initials("Priya")).toBe("P");
  });

  it("maps scores to tones consistently", () => {
    expect(scoreTone(80)).toContain("emerald");
    expect(scoreTone(60)).toContain("amber");
    expect(scoreTone(30)).toContain("rose");
    expect(scoreTone(null)).toContain("slate");
  });
});
