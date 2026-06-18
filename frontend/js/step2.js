import { analyzeDocuments } from "./api.js";
import { getAiFormData, persistAiSettings } from "./aiSettings.js";
import { getColumnsDetail } from "./cjmColumns.js";
import { getCjmRowsFromDom } from "./cjmSettings.js";
import { openModal } from "./modal.js";
import { showLoader, hideLoader } from "./loader.js";
import { setSessionId } from "./state.js";
import { $, showStatus } from "./utils.js";
import { renderQuestions } from "./questions.js";
import { getUploadedFiles } from "./upload.js";

export function initStep2() {
  $("#btnAnalyze")?.addEventListener("click", async () => {
    const ai = getAiFormData();
    if (!ai.credential) {
      alert(`Укажите ${ai.cfg.credentialLabel} в настройках ИИ`);
      openModal("ai");
      return;
    }
    persistAiSettings(ai);

    const { brief, concept, details } = getUploadedFiles();
    if (!brief || !concept) {
      alert("Загрузите бриф и концепцию на шаге 1");
      $("#stepUpload")?.scrollIntoView({ behavior: "smooth" });
      return;
    }

    const cjmRows = getCjmRowsFromDom();
    if (!cjmRows.length) {
      alert("Добавьте хотя бы одну строку CJM");
      openModal("cjmRows");
      return;
    }

    const columnsDetail = getColumnsDetail().trim();
    if (!columnsDetail) {
      alert("Укажите степень детализации столбцов CJM");
      openModal("cjmColumns");
      return;
    }

    const fd = new FormData();
    fd.append("provider", ai.provider);
    fd.append("credential", ai.credential);
    fd.append("model", ai.model);
    if (ai.provider === "gigachat") fd.append("scope", ai.scope);
    fd.append("brief", brief);
    fd.append("concept", concept);
    if (details) fd.append("details", details);
    fd.append("cjmRows", JSON.stringify(cjmRows));
    fd.append("cjmColumnsDetail", columnsDetail);

    showLoader("Синтезируем материалы и готовим вопросы...");
    $("#statusAnalyze").classList.add("hidden");

    try {
      const data = await analyzeDocuments(fd);
      setSessionId(data.sessionId);
      renderQuestions(data);
      $("#stepQuestions").classList.remove("hidden");
      $("#stepQuestions").scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      showStatus($("#statusAnalyze"), e.message);
    } finally {
      hideLoader();
    }
  });
}
