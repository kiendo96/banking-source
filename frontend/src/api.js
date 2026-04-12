const API = ""; // dùng cùng origin

export function setSession(session) {
  // Session is now handled via HttpOnly cookies
}

export function getSession() {
  return "cookie-session-active";
}

export function clearSession() {
  // Clearing should ideally hit a logout API, here we just reset local state if any
}

async function req(path, { method = "GET", body } = {}) {
  const res = await fetch(API + path, {
    method,
    credentials: "include",
    headers: {
      "Content-Type": "application/json",
    },
    body: body ? JSON.stringify(body) : undefined
  });

  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.detail || "Request failed");
  return data;
}

export const api = {
  register: (username, password) =>
    req("/api/auth/register", {
      method: "POST",
      body: { username, password }
    }),

  login: (username, password) =>
    req("/api/auth/login", {
      method: "POST",
      body: { username, password }
    }),

  me: () => req("/api/account/me"),

  transfer: (to_username, amount) =>
    req("/api/transfer/transfer", {
      method: "POST",
      body: { to_username, amount: Number(amount) }
    }),

  notifications: () => req("/api/notifications/notifications")
};
