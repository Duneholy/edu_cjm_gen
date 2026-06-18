export const $ = (sel) => document.querySelector(sel);

export function escapeHtml(s) {
  const d = document.createElement("div");
  d.textContent = s;
  return d.innerHTML;
}

export function escapeAttr(s) {
  return String(s)
    .replace(/&/g, "&amp;")
    .replace(/"/g, "&quot;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;");
}

export function showStatus(el, msg, type = "error") {
  el.textContent = msg;
  el.className = `status ${type}`;
  el.classList.remove("hidden");
}
