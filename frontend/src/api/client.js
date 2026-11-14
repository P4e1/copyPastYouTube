const TOKEN_KEY = "cpyt_token";

export function readToken() {
  return localStorage.getItem(TOKEN_KEY);
}

export function writeToken(token) {
  localStorage.setItem(TOKEN_KEY, token);
}

export function clearToken() {
  localStorage.removeItem(TOKEN_KEY);
}

function detailText(payload) {
  if (!payload) {
    return "Не удалось выполнить запрос";
  }
  if (typeof payload.detail === "string") {
    return payload.detail;
  }
  if (Array.isArray(payload.detail)) {
    return payload.detail.map((item) => item.msg || String(item)).join(" ");
  }
  return "Не удалось выполнить запрос";
}

export async function api(path, { method = "GET", body, auth = true } = {}) {
  const headers = {};
  if (body !== undefined) {
    headers["Content-Type"] = "application/json";
  }
  if (auth) {
    const token = readToken();
    if (token) {
      headers.Authorization = `Bearer ${token}`;
    }
  }
  const base = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8000";
  const response = await fetch(`${base}${path}`, {
    method,
    headers,
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const payload = response.status === 204 ? null : await response.json().catch(() => null);
  if (!response.ok) {
    const error = new Error(detailText(payload));
    error.status = response.status;
    throw error;
  }
  return payload;
}
