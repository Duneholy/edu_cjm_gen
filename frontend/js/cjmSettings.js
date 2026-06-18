import { DEFAULT_CJM_ROWS, CJM_ROWS_STORAGE } from "./config.js";
import { $, escapeAttr } from "./utils.js";

const list = $("#cjmRowsList");
let dragSource = null;

export function updateRowsStatus() {
  const el = $("#rowsStatus");
  if (!el) return;
  const count = getCjmRowsFromDom().length || DEFAULT_CJM_ROWS.length;
  el.textContent = `${count} ${count === 1 ? "строка" : count < 5 ? "строки" : "строк"}`;
}

function loadCjmRows() {
  try {
    const saved = localStorage.getItem(CJM_ROWS_STORAGE);
    if (saved) {
      const parsed = JSON.parse(saved);
      if (Array.isArray(parsed) && parsed.length) {
        return parsed
          .map((r) => ({
            key: r.key || `row_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
            title: r.title || "",
          }))
          .filter((r) => r.title.trim());
      }
    }
  } catch (_) {}
  return DEFAULT_CJM_ROWS.map((r) => ({ ...r }));
}

function saveCjmRows(rows) {
  localStorage.setItem(CJM_ROWS_STORAGE, JSON.stringify(rows));
  updateRowsStatus();
}

export function getCjmRowsFromDom() {
  return [...list.querySelectorAll(".cjm-row-item")]
    .map((li) => ({
      key: li.dataset.key,
      title: li.querySelector("input").value.trim(),
    }))
    .filter((r) => r.title);
}

function createRowElement(row) {
  const li = document.createElement("li");
  li.className = "cjm-row-item";
  li.draggable = true;
  li.dataset.key = row.key;
  li.innerHTML = `
    <span class="drag-handle" title="Перетащить">⋮⋮</span>
    <input type="text" value="${escapeAttr(row.title)}" placeholder="Название строки CJM" />
    <button type="button" class="row-delete-button" title="Удалить">×</button>
  `;

  li.querySelector(".row-delete-button").addEventListener("click", () => {
    if (list.children.length <= 1) {
      alert("Должна остаться хотя бы одна строка");
      return;
    }
    li.remove();
    saveCjmRows(getCjmRowsFromDom());
  });

  li.querySelector("input").addEventListener("input", () => {
    saveCjmRows(getCjmRowsFromDom());
  });

  li.addEventListener("dragstart", (e) => {
    dragSource = li;
    li.classList.add("dragging");
    e.dataTransfer.effectAllowed = "move";
    e.dataTransfer.setData("text/plain", row.key);
  });

  li.addEventListener("dragend", () => {
    li.classList.remove("dragging");
    list.querySelectorAll(".cjm-row-item").forEach((el) => el.classList.remove("drag-over"));
    dragSource = null;
    saveCjmRows(getCjmRowsFromDom());
  });

  li.addEventListener("dragover", (e) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "move";
    if (dragSource && dragSource !== li) li.classList.add("drag-over");
  });

  li.addEventListener("dragleave", () => li.classList.remove("drag-over"));

  li.addEventListener("drop", (e) => {
    e.preventDefault();
    li.classList.remove("drag-over");
    if (!dragSource || dragSource === li) return;
    const items = [...list.children];
    const from = items.indexOf(dragSource);
    const to = items.indexOf(li);
    if (from < to) li.after(dragSource);
    else li.before(dragSource);
    saveCjmRows(getCjmRowsFromDom());
  });

  return li;
}

function renderCjmRows(rows) {
  list.innerHTML = "";
  rows.forEach((row) => list.appendChild(createRowElement(row)));
  saveCjmRows(rows);
  updateRowsStatus();
}

export function initCjmSettings() {
  $("#addCjmRow")?.addEventListener("click", () => {
    const rows = getCjmRowsFromDom();
    rows.push({ key: `row_${Date.now()}`, title: "Новая строка" });
    renderCjmRows(rows);
    const lastInput = list.lastElementChild?.querySelector("input");
    lastInput?.focus();
    lastInput?.select();
  });

  $("#resetCjmRows")?.addEventListener("click", () => {
    if (!confirm("Сбросить строки CJM к значениям по умолчанию?")) return;
    renderCjmRows(DEFAULT_CJM_ROWS.map((r) => ({ ...r })));
  });

  renderCjmRows(loadCjmRows());
  updateRowsStatus();
}
