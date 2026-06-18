import { $ } from "./utils.js";

const loader = $("#loader");
const loaderText = $("#loaderText");

export function showLoader(text) {
  loaderText.textContent = text;
  loader.classList.remove("hidden");
}

export function hideLoader() {
  loader.classList.add("hidden");
}
