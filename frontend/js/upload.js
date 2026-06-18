const FILE_IDS = ["fileBrief", "fileConcept", "fileDetails"];

export function initUpload() {
  FILE_IDS.forEach((id) => {
    const input = document.querySelector(`#${id}`);
    const label = document.querySelector(`.file-name[data-for="${id}"]`);
    input?.addEventListener("change", () => {
      label.textContent = input.files[0]?.name || "Файл не выбран";
    });
  });
}

export function getUploadedFiles() {
  return {
    brief: document.querySelector("#fileBrief")?.files[0],
    concept: document.querySelector("#fileConcept")?.files[0],
    details: document.querySelector("#fileDetails")?.files[0],
  };
}

export function resetUploadedFiles() {
  FILE_IDS.forEach((id) => {
    const input = document.querySelector(`#${id}`);
    if (input) input.value = "";
    const label = document.querySelector(`.file-name[data-for="${id}"]`);
    if (label) label.textContent = "Файл не выбран";
  });
}
