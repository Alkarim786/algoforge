const TOKEN_KEY = "algoforge-token";

export function getToken() {
  try {
    return localStorage.getItem(TOKEN_KEY);
  } catch {
    return null;
  }
}

export function setToken(token) {
  try {
    if (token) localStorage.setItem(TOKEN_KEY, token);
    else localStorage.removeItem(TOKEN_KEY);
  } catch {
    // Storage can be blocked; the user just has to sign in again after a reload.
  }
}

let meRequest = null;

/** The signed-in user, fetched once and shared. Resolves to null when signed out or the token expired. */
export function fetchMe() {
  if (!getToken()) return Promise.resolve(null);
  meRequest ??= api("/auth/me").catch((failure) => {
    meRequest = null;
    if (failure.status === 401) {
      setToken(null);
      return null;
    }
    throw failure;
  });
  return meRequest;
}

export function signIn(token) {
  setToken(token);
  meRequest = null;
}

export function signOut() {
  setToken(null);
  meRequest = null;
}

export class ApiError extends Error {
  constructor(status, message) {
    super(message);
    this.status = status;
  }
}

function errorMessage(body, status) {
  if (typeof body?.detail === "string") return body.detail;
  if (Array.isArray(body?.detail)) return body.detail.map((item) => item.msg).join("; ");
  return `Request failed (${status}). Is the API running?`;
}

export async function api(path, { method = "GET", json, form } = {}) {
  const headers = {};
  const token = getToken();
  if (token) headers.Authorization = `Bearer ${token}`;
  let body;
  if (json !== undefined) {
    headers["Content-Type"] = "application/json";
    body = JSON.stringify(json);
  } else if (form) {
    body = new URLSearchParams(form);
  }
  const response = await fetch(`/api${path}`, { method, headers, body });
  const data = await response.json().catch(() => null);
  if (!response.ok) throw new ApiError(response.status, errorMessage(data, response.status));
  return data;
}
