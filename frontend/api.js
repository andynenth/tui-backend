// frontend/api.js
const API_BASE = "http://127.0.0.1:5050";

export async function deal() {
  const res = await fetch(`${API_BASE}/deal`);
  if (!res.ok) {
    throw new Error(`Failed to fetch /deal: ${res.status}`);
  }
  return await res.json();
}
