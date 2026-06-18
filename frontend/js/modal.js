import { loadColumnsDetail } from "./cjmColumns.js";
import { $ } from "./utils.js";

const backdrop = $("#modalBackdrop");
const modals = {
  ai: $("#modalAi"),
  cjmRows: $("#modalCjmRows"),
  cjmColumns: $("#modalCjmColumns"),
};

export function closeModal() {
  backdrop.classList.add("hidden");
  backdrop.setAttribute("aria-hidden", "true");
  Object.values(modals).forEach((m) => m?.classList.add("hidden"));
  document.body.classList.remove("modal-open");
}

export function openModal(name) {
  const target = modals[name];
  if (!target) return;
  Object.values(modals).forEach((m) => m?.classList.add("hidden"));
  backdrop.classList.remove("hidden");
  backdrop.setAttribute("aria-hidden", "false");
  target.classList.remove("hidden");
  document.body.classList.add("modal-open");

  if (name === "cjmColumns") {
    const input = $("#cjmColumnsInput");
    if (input) input.value = loadColumnsDetail();
  }
}

export function initModals() {
  $("#toggleSettings")?.addEventListener("click", () => openModal("ai"));
  $("#btnOpenRows")?.addEventListener("click", () => openModal("cjmRows"));
  $("#btnOpenColumns")?.addEventListener("click", () => openModal("cjmColumns"));

  backdrop?.addEventListener("click", (e) => {
    if (e.target === backdrop) closeModal();
  });

  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", closeModal);
  });

  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && !backdrop.classList.contains("hidden")) {
      closeModal();
    }
  });
}
