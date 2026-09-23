import {
  AnalyzeRequest,
  AnalyzeResponse,
  ContributionCreateRequest,
  TechnicianContribution,
  SearchRequestParams,
  SearchAPIResponseModel,
  RetrievalHealthResponseModel,
  EquipmentAsset,
  SessionDetailResponse,
} from "@/types/relay";

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  providers?: {
    retrieval: string;
    moss_status: string;
    llm: string;
  };
}

/**
 * Check backend API health and connectivity status.
 */
export async function checkBackendHealth(): Promise<SystemHealth> {
  const res = await fetch(`${API_BASE_URL}/api/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Health check failed with HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Execute end-to-end evidence-grounded diagnostic analysis.
 * Records precise client-side roundtrip latency.
 */
export async function analyzeQuery(
  request: AnalyzeRequest
): Promise<AnalyzeResponse> {
  const startTime = performance.now();
  try {
    const res = await fetch(`${API_BASE_URL}/api/reasoning/analyze`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      body: JSON.stringify(request),
    });

    const elapsed = Math.round(performance.now() - startTime);

    if (!res.ok) {
      let errorDetail = `HTTP ${res.status}`;
      try {
        const errorJson = await res.json();
        errorDetail =
          errorJson.detail?.message ||
          (typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail)) ||
          errorDetail;
      } catch {
        errorDetail = res.statusText || errorDetail;
      }
      throw new Error(`Reasoning request failed: ${errorDetail}`);
    }

    const data: AnalyzeResponse = await res.json();
    return {
      ...data,
      client_latency_ms: elapsed,
    };
  } catch (err: any) {
    if (err.name === "TypeError" && err.message.includes("fetch")) {
      throw new Error(
        `Unable to reach Relay Backend at ${API_BASE_URL}. Ensure the FastAPI server is running on port 8000.`
      );
    }
    throw err;
  }
}

/**
 * Submit a field-discovered technician contribution to Relay ("Teach Relay").
 * This creates a pending-review non-authoritative knowledge record.
 */
export async function createContribution(
  request: ContributionCreateRequest
): Promise<TechnicianContribution> {
  const res = await fetch(`${API_BASE_URL}/api/knowledge/contributions`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(request),
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail =
        errorJson.detail?.message ||
        (typeof errorJson.detail === "string" ? errorJson.detail : JSON.stringify(errorJson.detail)) ||
        errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(`Failed to submit contribution: ${errorDetail}`);
  }

  return res.json();
}

/**
 * Fetch all registered technician contributions, optionally filtered by asset ID.
 */
export async function getContributions(
  assetId?: string
): Promise<TechnicianContribution[]> {
  const url = new URL(`${API_BASE_URL}/api/knowledge/contributions`);
  if (assetId) {
    url.searchParams.set("asset_id", assetId);
  }
  const res = await fetch(url.toString(), {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch contributions: HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Perform live low-latency knowledge retrieval search over Moss index.
 */
export async function searchRetrieval(
  params: SearchRequestParams
): Promise<SearchAPIResponseModel> {
  const res = await fetch(`${API_BASE_URL}/api/retrieval/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify(params),
  });

  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errorJson = await res.json();
      errorDetail = errorJson.detail?.message || errorDetail;
    } catch {
      errorDetail = res.statusText || errorDetail;
    }
    throw new Error(`Retrieval search failed: ${errorDetail}`);
  }

  return res.json();
}

/**
 * Fetch Moss retrieval provider health and configuration status.
 */
export async function getRetrievalHealth(): Promise<RetrievalHealthResponseModel> {
  const res = await fetch(`${API_BASE_URL}/api/retrieval/health`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch retrieval health: HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch equipment specifications for an asset.
 */
export async function getDemoAsset(assetId: string): Promise<EquipmentAsset> {
  const res = await fetch(`${API_BASE_URL}/api/demo/asset/${encodeURIComponent(assetId)}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch asset ${assetId}: HTTP ${res.status}`);
  }
  return res.json();
}

/**
 * Fetch detailed state for a technician session.
 */
export async function getDemoSession(sessionId: string): Promise<SessionDetailResponse> {
  const res = await fetch(`${API_BASE_URL}/api/demo/session/${encodeURIComponent(sessionId)}`, {
    method: "GET",
    headers: { Accept: "application/json" },
    cache: "no-store",
  });
  if (!res.ok) {
    throw new Error(`Failed to fetch session ${sessionId}: HTTP ${res.status}`);
  }
  return res.json();
}

