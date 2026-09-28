import { describe, expect, it, vi, afterEach } from "vitest";

import { api, ApiError, API_BASE_URL } from "@/lib/api";

afterEach(() => {
  vi.restoreAllMocks();
});

describe("api client error handling", () => {
  it("turns the backend's structured error into an ApiError", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue(
        new Response(
          JSON.stringify({ error: { code: "not_found", message: "Job 9999 does not exist." } }),
          { status: 404, headers: { "Content-Type": "application/json" } },
        ),
      ),
    );

    await expect(api.jobs.get(9999)).rejects.toMatchObject({
      name: "ApiError",
      code: "not_found",
      status: 404,
      message: "Job 9999 does not exist.",
    });
  });

  it("produces a helpful message when the network is unreachable", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new TypeError("Failed to fetch")));

    const error = await api.health.full().catch((err: unknown) => err);
    expect(error).toBeInstanceOf(ApiError);
    expect((error as ApiError).code).toBe("network_error");
    expect((error as ApiError).message).toContain(API_BASE_URL);
  });

  it("survives non-JSON error bodies", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => Promise.resolve(new Response("gateway timeout", { status: 504 }))),
    );
    await expect(api.jobs.list()).rejects.toMatchObject({ status: 504 });
  });

  it("returns undefined for 204 responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 204 })));
    await expect(api.candidates.remove(1)).resolves.toBeUndefined();
  });
});

describe("api client request shaping", () => {
  it("builds query strings and drops empty filters", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(new Response(JSON.stringify([]), { status: 200 })));
    vi.stubGlobal("fetch", fetchMock);

    await api.jobs.list({ status: "open", q: "" });
    const url = fetchMock.mock.calls[0][0] as string;
    expect(url).toContain("/api/v1/jobs?status=open");
    expect(url).not.toContain("q=");

    await api.candidates.list({ q: "amira" });
    expect(fetchMock.mock.calls[1][0]).toContain("/api/v1/candidates?q=amira");
  });

  it("sends JSON content-type for JSON bodies but not for FormData", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation(() => Promise.resolve(new Response(JSON.stringify({}), { status: 201 })));
    vi.stubGlobal("fetch", fetchMock);

    await api.jobs.create({ jd_text: "x".repeat(40) });
    const jsonInit = fetchMock.mock.calls[0][1] as RequestInit;
    expect((jsonInit.headers as Record<string, string>)["Content-Type"]).toBe("application/json");

    const file = new File(["resume text"], "resume.txt", { type: "text/plain" });
    await api.candidates.upload(file);
    const formInit = fetchMock.mock.calls[1][1] as RequestInit;
    expect(formInit.body).toBeInstanceOf(FormData);
    expect((formInit.headers as Record<string, string>)["Content-Type"]).toBeUndefined();
  });
});
