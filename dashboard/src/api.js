// src/api.js
export async function fetchInsights() {
  try {
    const response = await fetch("http://127.0.0.1:8000/insights");
    if (!response.ok) throw new Error("Failed to fetch insights");
    return await response.json();
  } catch (err) {
    console.error(err);
    return null;
  }
}
