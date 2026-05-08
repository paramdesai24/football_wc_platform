const API_BASE_URL = import.meta.env.VITE_API_URL || "http://localhost:8000/api/v1";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

interface RequestConfig {
  method?: HttpMethod;
  body?: unknown;
  headers?: Record<string, string>;
  params?: Record<string, string | number | boolean | undefined>;
  signal?: AbortSignal;
}

class ApiClient {
  private baseUrl: string;

  constructor(baseUrl: string) {
    this.baseUrl = baseUrl;
  }

  private buildUrl(endpoint: string, params?: Record<string, string | number | boolean | undefined>): string {
    const url = new URL(`${this.baseUrl}${endpoint}`);
    if (params) {
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined) url.searchParams.append(key, String(value));
      });
    }
    return url.toString();
  }

  private async request<T>(endpoint: string, config: RequestConfig = {}): Promise<T> {
    const { method = "GET", body, headers = {}, params, signal } = config;
    const url = this.buildUrl(endpoint, params);
    const response = await fetch(url, {
      method,
      headers: { "Content-Type": "application/json", ...headers },
      body: body ? JSON.stringify(body) : undefined,
      signal,
    });
    if (!response.ok) {
      const errorBody = await response.text();
      throw new ApiError(response.status, response.statusText, errorBody);
    }
    return response.json();
  }

  async get<T>(endpoint: string, params?: Record<string, string | number | boolean | undefined>, signal?: AbortSignal): Promise<T> {
    return this.request<T>(endpoint, { method: "GET", params, signal });
  }

  async post<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "POST", body });
  }

  async put<T>(endpoint: string, body?: unknown): Promise<T> {
    return this.request<T>(endpoint, { method: "PUT", body });
  }

  async delete<T>(endpoint: string): Promise<T> {
    return this.request<T>(endpoint, { method: "DELETE" });
  }
}

export class ApiError extends Error {
  constructor(public status: number, public statusText: string, public body: string) {
    super(`API Error ${status}: ${statusText}`);
    this.name = "ApiError";
  }
}

export const apiClient = new ApiClient(API_BASE_URL);

export const endpoints = {
  health: "/health",
  countries: { list: "/countries", detail: (id: string) => `/countries/${id}`, rankings: "/countries/rankings" },
  players: { list: "/players", detail: (id: string) => `/players/${id}`, byCountry: (id: string) => `/players/country/${id}`, search: "/players/search" },
  predictions: { predict: "/predictions/predict", history: "/predictions/history", upcoming: "/predictions/upcoming" },
  simulation: { run: "/simulation/run", results: "/simulation/results", latest: "/simulation/latest" },
  analytics: { team: (id: string) => `/analytics/team/${id}`, compare: "/analytics/compare", trends: (id: string) => `/analytics/trends/${id}` },
} as const;
