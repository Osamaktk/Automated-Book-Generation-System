import { supabase } from "../lib/supabase";

const API_URL = import.meta.env.VITE_API_URL;

function buildUrl(path) {
  return `${API_URL}${path}`;
}

async function parsePayload(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

async function resolveAccessToken(accessToken) {
  if (accessToken) {
    return accessToken;
  }

  const {
    data: { session }
  } = await supabase.auth.getSession();
  return session?.access_token || null;
}

export async function request(path, { accessToken, headers, ...options } = {}) {
  const nextHeaders = { ...(headers || {}) };
  const resolvedAccessToken = await resolveAccessToken(accessToken);
  if (resolvedAccessToken) {
    nextHeaders.Authorization = `Bearer ${resolvedAccessToken}`;
  }

  const response = await fetch(buildUrl(path), { ...options, headers: nextHeaders });
  const payload = await parsePayload(response);

  if (!response.ok) {
    const message =
      payload?.detail || payload?.error || payload?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export async function sharedRequest(path, shareToken) {
  const separator = path.includes("?") ? "&" : "?";
  const response = await fetch(buildUrl(`${path}${separator}share=${encodeURIComponent(shareToken)}`));
  const payload = await parsePayload(response);

  if (!response.ok) {
    const message =
      payload?.detail || payload?.error || payload?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return payload;
}

export async function streamRequest(path, { accessToken, method = "POST", body } = {}) {
  const headers = { "Content-Type": "application/json" };
  const resolvedAccessToken = await resolveAccessToken(accessToken);
  if (resolvedAccessToken) {
    headers.Authorization = `Bearer ${resolvedAccessToken}`;
  }

  const response = await fetch(buildUrl(path), {
    method,
    headers,
    body: body ? JSON.stringify(body) : "{}"
  });

  if (!response.ok || !response.body) {
    const payload = await parsePayload(response);
    const message =
      payload?.detail || payload?.error || payload?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  return response;
}

export async function downloadRequest(path, { accessToken } = {}) {
  const headers = {};
  const resolvedAccessToken = await resolveAccessToken(accessToken);
  if (resolvedAccessToken) {
    headers.Authorization = `Bearer ${resolvedAccessToken}`;
  }

  const response = await fetch(buildUrl(path), { headers });
  if (!response.ok) {
    const payload = await parsePayload(response);
    const message =
      payload?.detail || payload?.error || payload?.message || `Request failed with status ${response.status}`;
    throw new Error(message);
  }

  const blob = await response.blob();
  const contentDisposition = response.headers.get("Content-Disposition") || "";
  const match = contentDisposition.match(/filename=\"?([^\"]+)\"?/i);
  return {
    blob,
    filename: match?.[1] || "download"
  };
}
