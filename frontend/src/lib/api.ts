/**
 * Typed API client for the TalentFlow AI backend.
 *
 * Every call funnels through `request()` so errors are uniform: the backend's
 * structured error shape is turned into an ApiError with a human message, and
 * network failures produce a helpful "is the backend running?" message.
 */

import type {
  Activity,
  Application,
  CandidateDetail,
  CandidateListItem,
  Health,
  JobDetail,
  JobListItem,
  MatchResult,
  Note,
  ScreeningListItem,
  ScreeningQuestion,
  Stage,
  Tag,
  TagUsage,
} from "@/lib/types";

export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "") ?? "http://localhost:8000";

export class ApiError extends Error {
  code: string;
  status: number;
  detail?: unknown;

  constructor(message: string, options: { code?: string; status?: number; detail?: unknown } = {}) {
    super(message);
    this.name = "ApiError";
    this.code = options.code ?? "error";
    this.status = options.status ?? 0;
    this.detail = options.detail;
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/v1${path}`, {
      cache: "no-store",
      ...init,
      headers: {
        ...(init.body instanceof FormData ? {} : { "Content-Type": "application/json" }),
        ...(init.headers ?? {}),
      },
    });
  } catch {
    throw new ApiError(
      `Cannot reach the API at ${API_BASE_URL}. Is the backend running?`,
      { code: "network_error" },
    );
  }

  if (!response.ok) {
    let code = `http_${response.status}`;
    let message = `Request failed (HTTP ${response.status})`;
    let detail: unknown;
    try {
      const body = await response.json();
      if (body?.error?.message) {
        code = body.error.code ?? code;
        message = body.error.message;
        detail = body.error.detail;
      }
    } catch {
      /* non-JSON error body — keep defaults */
    }
    throw new ApiError(message, { code, status: response.status, detail });
  }

  if (response.status === 204) {
    return undefined as T;
  }
  return (await response.json()) as T;
}

function query(params: Record<string, string | number | boolean | undefined>): string {
  const search = new URLSearchParams();
  for (const [key, value] of Object.entries(params)) {
    if (value !== undefined && value !== "") {
      search.set(key, String(value));
    }
  }
  const serialized = search.toString();
  return serialized ? `?${serialized}` : "";
}

export const api = {
  health: {
    full: () => request<Health>("/health"),
    live: () => request<{ status: string }>("/health/live"),
  },

  jobs: {
    list: (params: { status?: string; q?: string } = {}) =>
      request<JobListItem[]>(`/jobs${query(params)}`),
    get: (id: number) => request<JobDetail>(`/jobs/${id}`),
    create: (payload: {
      title?: string;
      company?: string;
      location?: string;
      employment_type?: string;
      jd_text: string;
    }) => request<JobDetail>("/jobs", { method: "POST", body: JSON.stringify(payload) }),
    upload: (file: File, extra: { title?: string; company?: string } = {}) => {
      const form = new FormData();
      form.append("file", file);
      if (extra.title) form.append("title", extra.title);
      if (extra.company) form.append("company", extra.company);
      return request<JobDetail>("/jobs/upload", { method: "POST", body: form });
    },
    update: (id: number, payload: { status?: string; title?: string; company?: string }) =>
      request<JobDetail>(`/jobs/${id}`, { method: "PATCH", body: JSON.stringify(payload) }),
    remove: (id: number) => request<void>(`/jobs/${id}`, { method: "DELETE" }),
  },

  candidates: {
    list: (params: { q?: string; skill?: string } = {}) =>
      request<CandidateListItem[]>(`/candidates${query(params)}`),
    get: (id: number) => request<CandidateDetail>(`/candidates/${id}`),
    upload: (file: File) => {
      const form = new FormData();
      form.append("file", file);
      return request<CandidateDetail>("/candidates/upload", { method: "POST", body: form });
    },
    remove: (id: number) => request<void>(`/candidates/${id}`, { method: "DELETE" }),
    addNote: (candidateId: number, payload: { body: string; author?: string; job_id?: number }) =>
      request<Note>(`/candidates/${candidateId}/notes`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    deleteNote: (candidateId: number, noteId: number) =>
      request<void>(`/candidates/${candidateId}/notes/${noteId}`, { method: "DELETE" }),
    addTag: (candidateId: number, payload: { name: string; color?: string }) =>
      request<Tag>(`/candidates/${candidateId}/tags`, {
        method: "POST",
        body: JSON.stringify(payload),
      }),
    removeTag: (candidateId: number, tagId: number) =>
      request<void>(`/candidates/${candidateId}/tags/${tagId}`, { method: "DELETE" }),
  },

  applications: {
    list: (params: { job_id?: number; candidate_id?: number; stage?: string } = {}) =>
      request<Application[]>(`/applications${query(params)}`),
    board: (params: { job_id?: number } = {}) =>
      request<Record<Stage, Application[]>>(`/applications/board${query(params)}`),
    activity: (limit = 10) => request<Activity[]>(`/applications/activity${query({ limit })}`),
    get: (id: number) => request<Application>(`/applications/${id}`),
    create: (payload: { candidate_id: number; job_id: number; note?: string }) =>
      request<Application>("/applications", { method: "POST", body: JSON.stringify(payload) }),
    moveStage: (id: number, payload: { to_stage: Stage; note?: string }) =>
      request<Application>(`/applications/${id}/stage`, {
        method: "PATCH",
        body: JSON.stringify(payload),
      }),
    remove: (id: number) => request<void>(`/applications/${id}`, { method: "DELETE" }),
  },

  matching: {
    forJob: (jobId: number, params: { limit?: number; only_applicants?: boolean } = {}) =>
      request<MatchResult[]>(`/matching/job/${jobId}${query(params)}`),
    forCandidate: (candidateId: number, limit = 10) =>
      request<MatchResult[]>(`/matching/candidate/${candidateId}${query({ limit })}`),
    pair: (jobId: number, candidateId: number) =>
      request<MatchResult>(`/matching/pair${query({ job_id: jobId, candidate_id: candidateId })}`),
  },

  screening: {
    list: () => request<ScreeningListItem[]>("/screening"),
    forApplication: (applicationId: number) =>
      request<ScreeningQuestion[]>(`/screening/applications/${applicationId}`),
    generate: (applicationId: number) =>
      request<ScreeningQuestion[]>(`/screening/applications/${applicationId}/generate`, {
        method: "POST",
      }),
  },

  tags: {
    list: () => request<TagUsage[]>("/tags"),
  },
};
