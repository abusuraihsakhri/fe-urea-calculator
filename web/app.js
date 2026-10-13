import {
  INPUT_COLUMNS, OUTPUT_COLUMNS, calculateFeUrea, processCsv, serializeCsv
} from "./core.mjs";

const byId = id => document.getElementById(id);
const form = byId("calculator");
const error = byId("form-error");
const score = byId("score");
const label = byId("result-label");
const interpretation = byId("interpretation");
const fileInput = byId("csv-file");
const status = byId("csv-status");
const download = byId("download");
const previewWrap = byId("preview-wrap");
const preview = byId("preview");
let csvResult = null;

function clearResult() {
  score.textContent = "—";
  label.textContent = "Enter all four measurements to calculate FEUrea.";
  interpretation.textContent = "";
  error.hidden = true;
  error.textContent = "";
}

function updateUreaLabels() {
  const title = byId("urea-unit").value.startsWith("BUN") ? "BUN" : "urea";
  document.querySelectorAll(".urea-label").forEach(el => { el.textContent = title; });
}

form.addEventListener("submit", event => {
  event.preventDefault();
  error.hidden = true;
  try {
    const measurements = {};
    for (const key of INPUT_COLUMNS) {
      const input = byId(key);
      if (!input.value.trim()) throw new Error("Enter all four measurements.");
      measurements[key] = Number(input.value);
    }
    const result = calculateFeUrea(measurements);
    score.textContent = result.fe_urea_percent.toFixed(2) + "%";
    label.textContent = result.classification;
    interpretation.textContent = result.clinical_recommendation;
  } catch (ex) {
    clearResult();
    error.textContent = ex.message;
    error.hidden = false;
  }
});

form.addEventListener("reset", () => {
  clearResult();
  // Native reset updates selects after the handler returns.
  queueMicrotask(updateUreaLabels);
});
byId("example").addEventListener("click", () => {
  const sample = {serum_creatinine: 1.2, urine_creatinine: 120,
    serum_urea: 25, urine_urea: 250};
  Object.entries(sample).forEach(([key, val]) => { byId(key).value = String(val); });
  byId("creatinine-unit").value = "mg/dL";
  byId("urea-unit").value = "BUN · mg/dL";
  updateUreaLabels();
  form.requestSubmit();
});
byId("urea-unit").addEventListener("change", () => {
  updateUreaLabels();
  clearResult();
});
byId("creatinine-unit").addEventListener("change", clearResult);
INPUT_COLUMNS.forEach(key => byId(key).addEventListener("input", clearResult));

function downloadText(filename, text) {
  const link = document.createElement("a");
  const url = URL.createObjectURL(new Blob([text], {type: "text/csv;charset=utf-8"}));
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

byId("template").addEventListener("click", () => {
  const sample = ["1.2", "120", "25", "250"];
  downloadText("feurea-template.csv", serializeCsv(INPUT_COLUMNS, [sample]));
});

function renderPreview(data) {
  preview.replaceChildren();
  const thead = document.createElement("thead");
  const hr = document.createElement("tr");
  for (const h of data.headers) {
    const th = document.createElement("th");
    th.scope = "col";
    th.textContent = h;
    hr.appendChild(th);
  }
  thead.appendChild(hr);
  const tbody = document.createElement("tbody");
  for (const row of data.rows.slice(0, 10)) {
    const tr = document.createElement("tr");
    for (const value of row) {
      const td = document.createElement("td");
      td.textContent = String(value);
      tr.appendChild(td);
    }
    tbody.appendChild(tr);
  }
  preview.append(thead, tbody);
  previewWrap.hidden = false;
}

fileInput.addEventListener("change", async () => {
  csvResult = null;
  download.disabled = true;
  previewWrap.hidden = true;
  preview.replaceChildren();
  const file = fileInput.files?.[0];
  if (!file) { status.textContent = "No CSV selected."; return; }
  try {
    if (file.size > 2 * 1024 * 1024) throw new Error("File exceeds the 2 MB limit");
    const text = await file.text();
    const processed = processCsv(text);
    csvResult = processed;
    status.textContent = processed.rows.length + " records: " +
      processed.valid + " valid, " + processed.invalid + " invalid.";
    renderPreview(processed);
    download.disabled = false;
  } catch (ex) {
    status.textContent = "CSV error: " + ex.message;
  }
});
download.addEventListener("click", () => {
  if (!csvResult) return;
  downloadText("feurea-results.csv", serializeCsv(csvResult.headers, csvResult.rows));
});
