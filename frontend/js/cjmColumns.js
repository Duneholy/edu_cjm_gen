import { CJM_COLUMNS_STORAGE, DEFAULT_COLUMNS_PLACEHOLDER } from "./config.js";
import { $ } from "./utils.js";

export function loadColumnsDetail() {
  return localStorage.getItem(CJM_COLUMNS_STORAGE) || "";
}

export function saveColumnsDetail(text) {
  localStorage.setItem(CJM_COLUMNS_STORAGE, text.trim());
  updateColumnsStatus();
}

export function getColumnsDetail() {
  return loadColumnsDetail();
}

export function updateColumnsStatus() {
  const el = $("#columnsStatus");
  if (!el) return;
  const text = loadColumnsDetail();
  if (!text.trim()) {
    el.textContent = "Не задано";
    return;
  }
  const preview = text.length > 72 ? `${text.slice(0, 72)}…` : text;
  el.textContent = preview;
}

export function initCjmColumns() {
  const input = $("#cjmColumnsInput");
  if (input) {
    input.placeholder = DEFAULT_COLUMNS_PLACEHOLDER;
    input.value = loadColumnsDetail();
  }

  $("#saveCjmColumns")?.addEventListener("click", () => {
    saveColumnsDetail(input?.value || "");
    $("#modalCjmColumns")?.querySelector("[data-close-modal]")?.click();
  });

  input?.addEventListener("input", () => {
    // live preview on card when modal closes
  });

  updateColumnsStatus();
}
