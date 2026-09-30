"use client";

import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import type { ApiError } from "@/lib/api";

export function LoadingBlock({ lines = 3, className = "" }: { lines?: number; className?: string }) {
  return (
    <div className={`space-y-3 ${className}`} role="status" aria-label="Loading">
      {Array.from({ length: lines }).map((_, index) => (
        <div key={index} className="skeleton h-4" style={{ width: `${100 - index * 12}%` }} />
      ))}
    </div>
  );
}

export function EmptyState({
  title,
  description,
  action,
  icon,
}: {
  title: string;
  description?: string;
  action?: ReactNode;
  icon?: ReactNode;
}) {
  return (
    <div className="flex flex-col items-center justify-center rounded-xl border border-dashed border-slate-300 bg-slate-50/60 px-6 py-12 text-center">
      {icon ? <div className="mb-3 text-slate-500">{icon}</div> : null}
      <h3 className="text-sm font-semibold text-slate-900">{title}</h3>
      {description ? <p className="mt-1 max-w-md text-sm text-slate-500">{description}</p> : null}
      {action ? <div className="mt-4">{action}</div> : null}
    </div>
  );
}

export function ErrorState({
  error,
  onRetry,
  compact = false,
}: {
  error: ApiError | Error;
  onRetry?: () => void;
  compact?: boolean;
}) {
  const message = error.message || "Something went wrong.";
  if (compact) {
    return (
      <div className="flex items-center justify-between gap-3 rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
        <span>{message}</span>
        {onRetry ? (
          <button onClick={onRetry} className="text-xs font-semibold underline">
            Retry
          </button>
        ) : null}
      </div>
    );
  }
  return (
    <div className="rounded-xl border border-rose-200 bg-rose-50 px-6 py-8 text-center">
      <h3 className="text-sm font-semibold text-rose-800">Something went wrong</h3>
      <p className="mx-auto mt-1 max-w-lg text-sm text-rose-700">{message}</p>
      {onRetry ? (
        <div className="mt-4">
          <Button variant="secondary" size="sm" onClick={onRetry}>
            Try again
          </Button>
        </div>
      ) : null}
    </div>
  );
}

export function InlineError({ message }: { message: string }) {
  return (
    <p className="rounded-lg border border-rose-200 bg-rose-50 px-3 py-2 text-sm text-rose-700">
      {message}
    </p>
  );
}
