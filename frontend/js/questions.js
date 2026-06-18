import { generateCjm } from "./api.js";
import { getSessionId, resetSession } from "./state.js";
import { $, escapeHtml, showStatus } from "./utils.js";
import { showLoader, hideLoader } from "./loader.js";
import { resetUploadedFiles } from "./upload.js";
export function renderQuestions(data) {
  $("#programSummary").textContent = data.programSummary || "Резюме программы сформировано.";

  const gapsEl = $("#detectedGaps");
  if (data.detectedGaps?.length) {
    gapsEl.innerHTML =
      "<strong>Обнаруженные пробелы:</strong><ul>" +
      data.detectedGaps.map((g) => `<li>${escapeHtml(g)}</li>`).join("") +
      "</ul>";
    gapsEl.classList.remove("hidden");
  } else {
    gapsEl.classList.add("hidden");
  }

  const form = $("#questionsForm");
  form.innerHTML = "";
  (data.questions || []).forEach((q, i) => {
    const card = document.createElement("div");
    card.className = "question-card";
    card.innerHTML = `
      <label for="ans_${q.id}">${i + 1}. ${escapeHtml(q.question)}</label>
      ${q.hint ? `<span class="question-hint">${escapeHtml(q.hint)}</span>` : ""}
      <textarea id="ans_${q.id}" name="${q.id}" rows="3" placeholder="Ваш ответ..."></textarea>
    `;
    form.appendChild(card);
  });
}

function collectAnswers() {
  const answers = {};
  $("#questionsForm")
    .querySelectorAll("textarea")
    .forEach((ta) => {
      answers[ta.name] = ta.value.trim();
    });
  return answers;
}

export function initQuestions() {
  $("#btnGenerate")?.addEventListener("click", async () => {
    const sessionId = getSessionId();
    if (!sessionId) {
      alert("Сначала выполните анализ");
      return;
    }

    showLoader("ИИ собирает CJM — это может занять 1–3 минуты...");
    $("#statusGenerate").classList.add("hidden");

    try {
      const data = await generateCjm(sessionId, collectAnswers());
      $("#resultInfo").innerHTML = `
        <strong>${escapeHtml(data.programTitle)}</strong><br>
        Собрано колонок CJM: <strong>${data.stagesCount}</strong>
      `;
      $("#btnView").href = data.viewUrl;
      $("#btnDownload").href = data.downloadUrl;
      $("#stepResult").classList.remove("hidden");
      $("#stepResult").scrollIntoView({ behavior: "smooth" });
    } catch (e) {
      showStatus($("#statusGenerate"), e.message);
    } finally {
      hideLoader();
    }
  });

  $("#btnRestart")?.addEventListener("click", () => {
    resetSession();
    $("#stepQuestions").classList.add("hidden");
    $("#stepResult").classList.add("hidden");
    $("#questionsForm").innerHTML = "";
    resetUploadedFiles();
    $("#stepUpload").scrollIntoView({ behavior: "smooth" });
  });
}