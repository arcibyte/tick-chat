const API_URL = "http://localhost:8000";

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
    const data = await res.json();
    // El backend retorna {"users": [...]}, así que extraemos la propiedad o devolvemos array vacío
    return Array.isArray(data.users) ? data.users : [];
  } catch {
    return [];
  }
}

export async function getHistory() {
  try {
    const res = await fetch(`${API_URL}/history`);
    const data = await res.json();
    // El backend retorna {"history": [...]}, extraemos la lista correctamente
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
    return res.ok;
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
