export const PROVIDER_CONFIG = {
  openrouter: {
    credentialLabel: "API-ключ OpenRouter",
    placeholder: "sk-or-v1-...",
    storageKey: "openrouter_credential",
    modelKey: "openrouter_model",
    defaultModels: [
      { id: "qwen/qwen3.7-plus", name: "qwen/qwen3.7-plus" },
      { id: "qwen/qwen3-235b-a22b-instruct-2507", name: "qwen/qwen3-235b-a22b-instruct-2507" },
    ],
    prefer: (opts) => opts.find((o) => /qwen/i.test(o.value)),
  },
  gigachat: {
    credentialLabel: "Authorization Key",
    placeholder: "MDE5Yzk5Zjkt...",
    storageKey: "gigachat_credential",
    modelKey: "gigachat_model",
    defaultModels: [
      { id: "GigaChat-2-Max", name: "GigaChat 2 Max" },
      { id: "GigaChat-2-Pro", name: "GigaChat 2 Pro" },
      { id: "GigaChat-2", name: "GigaChat 2" },
      { id: "GigaChat-Max", name: "GigaChat Max" },
      { id: "GigaChat-Pro", name: "GigaChat Pro" },
      { id: "GigaChat", name: "GigaChat" },
    ],
    prefer: (opts) => opts.find((o) => /GigaChat-2-Pro/i.test(o.value)) || opts[0],
  },
};

export const DEFAULT_CJM_ROWS = [
  { key: "student_action", title: "Пользовательское действие (ученик)" },
  { key: "mentor_action", title: "Пользовательское действие (наставник)" },
  { key: "motivation", title: "Мотивация (цели ученика)" },
  { key: "problems", title: "Проблемы (барьеры, с которыми сталкивается ученик)" },
  { key: "artifacts", title: "Артефакты (материалы и формы, присутствующие на этапе)" },
  { key: "contacts", title: "Контакты (точки контакта с учеником)" },
];

export const CJM_ROWS_STORAGE = "cjm_rows_config";
export const CJM_COLUMNS_STORAGE = "cjm_columns_detail";

export const DEFAULT_COLUMNS_PLACEHOLDER =
  "Укажите степень детализации CJM: нужна верхнеуровневая карта с небольшим количеством столбцов (по модулям/этапам) или подробная — с отдельным столбцом на каждый урок?";
