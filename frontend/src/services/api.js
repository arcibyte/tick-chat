const API_URL = import.meta.env.VITE_API_URL || "http://localhost:8000";

export async function checkHealth() {
  try {
    const res = await fetch(`${API_URL}/fed/health`);
    return res.ok;
  } catch {
    return false;
  }
}

export async function getUsers() {
  try {
    const res = await fetch(`${API_URL}/users`);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.users) ? data.users : [];
  } catch {
    return [];
  }
}

export async function getHistory(since = null) {
  try {
    const url =
      since !== null
        ? `${API_URL}/history?since=${since}`
        : `${API_URL}/history`;
    const res = await fetch(url);
    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data.history) ? data.history : [];
  } catch {
    return [];
  }
}

export async function registerUser(username) {
  try {
    const res = await fetch(`${API_URL}/users`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username }),
    });
    // Retorna true si se creó (201) o si ya existía previamente (400)
    return res.ok || res.status === 400;
  } catch {
    return false;
  }
}

export async function postMessage(fromUser, body) {
  try {
    const res = await fetch(`${API_URL}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ from_user: fromUser, body }),
    });
    return res.ok;
  } catch {
    return false;
  }
}
