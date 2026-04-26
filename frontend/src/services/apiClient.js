const API_URL = import.meta.env.VITE_API_URL;

function isLocalApiUrl(value) {
  return /^https?:\/\/(127\.0\.0\.1|localhost)(:\d+)?$/i.test((value || "").trim());
}

function resolveApiBaseUrl() {
  const configured = (API_URL || "").trim().replace(/\/+$/, "");

  if (typeof window === "undefined") {
    return configured;
  }

  const currentOrigin = window.location.origin.replace(/\/+$/, "");
  const isLocalBrowser =
    window.location.hostname === "127.0.0.1" || window.location.hostname === "localhost";

  if (!configured) {
    return currentOrigin;
  }

  if (!isLocalBrowser && isLocalApiUrl(configured)) {
    return currentOrigin;
  }

  return configured;
}

function buildUrl(path) {
  return `${resolveApiBaseUrl()}${path}`;
}

async function parsePayload(response) {
  try {
    return await response.json();
  } catch {
    return null;
  }
}

export async function request(path, { accessToken, headers, ...options } = {}) {
  const nextHeaders = { ...(headers || {}) };
  if (accessToken) {
    nextHeaders.Authorization = `Bearer ${accessToken}`;
  }

  let response;
  try {
    response = await fetch(buildUrl(path), { ...options, headers: nextHeaders });
  } catch {
    throw new Error(
      "Unable to reach the API. Check VITE_API_URL or make sure the backend is running."
    );
  }
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
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  let response;
  try {
    response = await fetch(buildUrl(path), {
      method,
      headers,
      body: body ? JSON.stringify(body) : "{}"
    });
  } catch {
    throw new Error(
      "Unable to reach the API. Check VITE_API_URL or make sure the backend is running."
    );
  }

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
  if (accessToken) {
    headers.Authorization = `Bearer ${accessToken}`;
  }

  let response;
  try {
    response = await fetch(buildUrl(path), { headers });
  } catch {
    throw new Error(
      "Unable to reach the API. Check VITE_API_URL or make sure the backend is running."
    );
  }
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
