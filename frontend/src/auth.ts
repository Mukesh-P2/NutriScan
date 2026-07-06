// Auth API calls + token storage. Kept separate from api.ts so account concerns
// stay isolated from the scan/ask endpoints.
import type { NutritionTargets, Profile, TargetGuidance, User } from "./types";

const TOKEN_KEY = "nutriscan_token";

export const tokenStore = {
  get: () => localStorage.getItem(TOKEN_KEY),
  set: (t: string) => localStorage.setItem(TOKEN_KEY, t),
  clear: () => localStorage.removeItem(TOKEN_KEY),
};

async function parseError(res: Response): Promise<string> {
  try {
    const data = await res.json();
    if (typeof data.detail === "string") return data.detail;
    return JSON.stringify(data.detail ?? data);
  } catch {
    return `Request failed (${res.status})`;
  }
}

function authHeaders(): HeadersInit {
  const token = tokenStore.get();
  return token ? { Authorization: `Bearer ${token}` } : {};
}

/** Fetch that attaches the bearer token and throws on non-2xx. */
export async function authFetch(path: string, init: RequestInit = {}): Promise<Response> {
  const res = await fetch(path, {
    ...init,
    headers: { ...(init.headers ?? {}), ...authHeaders() },
  });
  if (!res.ok) throw new Error(await parseError(res));
  return res;
}

export async function register(email: string, password: string, name?: string): Promise<string> {
  const res = await fetch("/api/auth/register", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ email, password, name: name || null }),
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  return data.access_token as string;
}

export async function login(email: string, password: string): Promise<string> {
  // Backend uses the OAuth2 password flow → form-encoded `username`/`password`.
  const body = new URLSearchParams({ username: email, password });
  const res = await fetch("/api/auth/login", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body,
  });
  if (!res.ok) throw new Error(await parseError(res));
  const data = await res.json();
  return data.access_token as string;
}

export async function fetchMe(): Promise<User> {
  return (await authFetch("/api/auth/me")).json();
}

export async function fetchProfile(): Promise<Profile> {
  return (await authFetch("/api/profile")).json();
}

export async function saveProfile(profile: Profile): Promise<Profile> {
  return (
    await authFetch("/api/profile", {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(profile),
    })
  ).json();
}

export async function fetchTargets(): Promise<NutritionTargets> {
  return (await authFetch("/api/profile/targets")).json();
}

export async function fetchGuidance(): Promise<TargetGuidance> {
  return (await authFetch("/api/profile/guidance")).json();
}
