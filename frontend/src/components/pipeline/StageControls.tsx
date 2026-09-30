"use client";

import { useState } from "react";

import { STAGES, STAGE_LABELS, ADVANCE_STAGES } from "@/lib/format";
import type { Stage } from "@/lib/types";
import { Button } from "@/components/ui/Button";

/**
 * Stage controls for one application. Moving is explicit (select + apply) —
 * there is no drag-only interaction, so the flow stays testable and accessible.
 */
export function StageControls({
  stage,
  onMove,
  compact = false,
}: {
  stage: Stage;
  onMove: (toStage: Stage, note?: string) => Promise<void>;
  compact?: boolean;
}) {
  const [busy, setBusy] = useState(false);
  const [note, setNote] = useState("");

  const advanceIndex = ADVANCE_STAGES.indexOf(stage);
  const nextStage = advanceIndex >= 0 && advanceIndex < ADVANCE_STAGES.length - 1
    ? ADVANCE_STAGES[advanceIndex + 1]
    : null;

  async function move(toStage: Stage) {
    setBusy(true);
    try {
      await onMove(toStage, note.trim() || undefined);
      setNote("");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className={compact ? "flex flex-wrap items-center gap-2" : "space-y-2"}>
      <div className="flex flex-wrap items-center gap-1.5">
        <select
          aria-label="Move to stage"
          value={stage}
          disabled={busy}
          onChange={(event) => move(event.target.value as Stage)}
          className={`rounded-lg border-0 bg-white ${compact ? "px-2 py-1 text-[11px]" : "px-2.5 py-1.5 text-xs"} shadow-sm ring-1 ring-inset ring-slate-300 focus:ring-2 focus:ring-indigo-600`}
        >
          {STAGES.map((option) => (
            <option key={option} value={option}>
              {STAGE_LABELS[option]}
            </option>
          ))}
        </select>
        {nextStage ? (
          <Button
            size="sm"
            variant="secondary"
            loading={busy}
            onClick={() => move(nextStage)}
            title={`Move to ${STAGE_LABELS[nextStage]}`}
          >
            → {STAGE_LABELS[nextStage]}
          </Button>
        ) : null}
        {stage !== "REJECTED" ? (
          <Button
            size="sm"
            variant="ghost"
            disabled={busy}
            onClick={() => move("REJECTED")}
            className="text-rose-600 hover:bg-rose-50"
          >
            Reject
          </Button>
        ) : (
          <Button size="sm" variant="ghost" disabled={busy} onClick={() => move("NEW")}>
            Reopen
          </Button>
        )}
      </div>
      {!compact ? (
        <input
          value={note}
          onChange={(event) => setNote(event.target.value)}
          placeholder="Optional note for the next move…"
          aria-label="Move note"
          className="block w-full rounded-lg border-0 bg-white px-3 py-1.5 text-xs shadow-sm ring-1 ring-inset ring-slate-300 placeholder:text-slate-500 focus:ring-2 focus:ring-indigo-600"
        />
      ) : null}
    </div>
  );
}
