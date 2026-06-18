import { initModals } from "./modal.js";
import { initAiSettings } from "./aiSettings.js";
import { initCjmSettings } from "./cjmSettings.js";
import { initCjmColumns } from "./cjmColumns.js";
import { initUpload } from "./upload.js";
import { initStep2 } from "./step2.js";
import { initQuestions } from "./questions.js";

function init() {
  initModals();
  initAiSettings();
  initCjmSettings();
  initCjmColumns();
  initUpload();
  initStep2();
  initQuestions();
}

init();
