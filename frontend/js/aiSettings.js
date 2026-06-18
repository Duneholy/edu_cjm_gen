import { PROVIDER_CONFIG } from "./config.js";
import { fetchModels } from "./api.js";
import { $ } from "./utils.js";
import { showLoader, hideLoader } from "./loader.js";

const els = {
  providerSelect: $("#providerSelect"),
  credential: $("#credential"),
  credentialLabelText: $("#credentialLabelText"),
  scopeWrap: $("#scopeWrap"),
  scopeSelect: $("#scopeSelect"),
  modelSelect: $("#modelSelect"),
  loadModels: $("#loadModels"),
  gigachatHint: $("#gigachatHint"),
};

function currentProvider() {
  return els.providerSelect.value;
}

function providerCfg() {
  return PROVIDER_CONFIG[currentProvider()];
}

function fillDefaultModels() {
  const cfg = providerCfg();
  els.modelSelect.innerHTML = "";
  cfg.defaultModels.forEach((m) => {
    const opt = document.createElement("option");
    opt.value = m.id;
    opt.textContent = m.name;
    els.modelSelect.appendChild(opt);
  });
  const saved = localStorage.getItem(cfg.modelKey);
  if (saved) {
    const exists = [...els.modelSelect.options].some((o) => o.value === saved);
    if (!exists) {
      const opt = document.createElement("option");
      opt.value = saved;
      opt.textContent = saved;
      els.modelSelect.appendChild(opt);
    }
    els.modelSelect.value = saved;
  } else {
    const preferred = cfg.prefer([...els.modelSelect.options]);
    if (preferred) els.modelSelect.value = preferred.value;
  }
}

function updateProviderUI() {
  const cfg = providerCfg();
  const isGiga = currentProvider() === "gigachat";

  els.credentialLabelText.textContent = cfg.credentialLabel;
  els.credential.placeholder = cfg.placeholder;
  els.scopeWrap.classList.toggle("hidden", !isGiga);
  els.gigachatHint.classList.toggle("hidden", !isGiga);
  els.credential.value = localStorage.getItem(cfg.storageKey) || "";
  fillDefaultModels();
}

export function getAiFormData() {
  const cfg = providerCfg();
  return {
    provider: currentProvider(),
    credential: els.credential.value.trim(),
    model: els.modelSelect.value,
    scope: els.scopeSelect.value,
    cfg,
  };
}

export function persistAiSettings({ provider, credential, model, scope, cfg }) {
  localStorage.setItem(cfg.storageKey, credential);
  localStorage.setItem(cfg.modelKey, model);
  if (provider === "gigachat") {
    localStorage.setItem("gigachat_scope", scope);
  }
}

export function initAiSettings() {
  const savedScope = localStorage.getItem("gigachat_scope");
  if (savedScope) els.scopeSelect.value = savedScope;

  els.providerSelect.addEventListener("change", updateProviderUI);
  updateProviderUI();

  els.loadModels.addEventListener("click", async () => {
    const cfg = providerCfg();
    const cred = els.credential.value.trim();
    if (!cred) {
      alert(`Введите ${cfg.credentialLabel}`);
      return;
    }
    localStorage.setItem(cfg.storageKey, cred);

    showLoader("Загрузка моделей...");
    try {
      const body = { provider: currentProvider(), credential: cred };
      if (currentProvider() === "gigachat") body.scope = els.scopeSelect.value;

      const data = await fetchModels(body);
      els.modelSelect.innerHTML = "";
      data.models.forEach((m) => {
        const opt = document.createElement("option");
        opt.value = m.id;
        opt.textContent = m.name || m.id;
        els.modelSelect.appendChild(opt);
      });
      const preferred = cfg.prefer([...els.modelSelect.options]);
      if (preferred) els.modelSelect.value = preferred.value;
    } catch (e) {
      alert(e.message);
    } finally {
      hideLoader();
    }
  });
}
