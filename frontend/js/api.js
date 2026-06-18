export async function fetchModels(body) {
  const res = await fetch("/api/models", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Ошибка");
  return data;
}

export async function analyzeDocuments(formData) {
  const res = await fetch("/api/analyze", { method: "POST", body: formData });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Ошибка анализа");
  return data;
}

export async function generateCjm(sessionId, answers) {
  const res = await fetch("/api/generate", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ sessionId, answers }),
  });
  const data = await res.json();
  if (!res.ok) throw new Error(data.error || "Ошибка генерации");
  return data;
}
