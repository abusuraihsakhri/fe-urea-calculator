/**
 * FEUrea arithmetic and CSV utilities shared by the browser and Node tests.
 * Measurements within each serum/urine pair must use identical units and
 * analyte definitions (BUN must not be mixed with urea).
 */
export const INPUT_COLUMNS = Object.freeze([
  "serum_creatinine", "urine_creatinine", "serum_urea", "urine_urea"
]);
export const OUTPUT_COLUMNS = Object.freeze([
  "fe_urea_percent", "classification", "clinical_recommendation"
]);
const PRERENAL = "Prerenal Azotemia";
const INTRINSIC = "Acute Tubular Necrosis / Intrinsic Renal Disease";

export function calculateFeUrea(values) {
  for (const name of INPUT_COLUMNS) {
    const value = values[name];
    if (typeof value !== "number" || !Number.isFinite(value) || value <= 0) {
      throw new RangeError(name + " must be a finite, positive number");
    }
  }
  const percent = 100 *
    (values.urine_urea / values.serum_urea) *
    (values.serum_creatinine / values.urine_creatinine);
  if (!Number.isFinite(percent)) {
    throw new RangeError("Calculated FEUrea is not finite; check input magnitudes");
  }
  const below = percent < 35;
  return {
    fe_urea_percent: Number(percent.toFixed(2)),
    classification: below ? PRERENAL : INTRINSIC,
    clinical_recommendation: below
      ? "FEUrea < 35% is compatible with a prerenal physiology pattern. Interpret with clinical assessment; do not determine treatment from FEUrea alone."
      : "FEUrea >= 35% may occur with intrinsic AKI but is not diagnostic of ATN. Interpret with clinical assessment; do not determine treatment from FEUrea alone."
  };
}

/** RFC 4180-style CSV parser, including quoted commas, embedded line breaks and escaped quotes. */
export function parseCsv(source) {
  if (typeof source !== "string" || source.length === 0) {
    throw new Error("CSV is empty");
  }
  const text = source.replace(/^\uFEFF/, "");
  const rows = [];
  let row = [], field = "", state = "start";
  const cell = () => { row.push(field); field = ""; state = "start"; };
  const line = () => { cell(); rows.push(row); row = []; if (rows.length > 5001) throw new Error("CSV exceeds 5000 rows"); };
  for (let i = 0; i < text.length; i++) {
    const ch = text[i];
    if (state === "quoted") {
      if (ch === '"') {
        if (text[i + 1] === '"') { field += '"'; i++; }
        else state = "closed";
      } else field += ch;
    } else if (ch === ",") {
      cell();
    } else if (ch === "\n" || ch === "\r") {
      if (ch === "\r" && text[i + 1] === "\n") i++;
      line();
    } else if (ch === '"' && state === "start") {
      state = "quoted";
    } else if (state === "closed") {
      throw new Error("Unexpected character after closing CSV quote");
    } else if (ch === '"') {
      throw new Error("Unexpected quote in unquoted CSV field");
    } else {
      field += ch; state = "plain";
    }
  }
  if (state === "quoted") throw new Error("Unclosed CSV quote");
  if (row.length || field.length || state !== "start") line();
  if (!rows.length) throw new Error("CSV is empty");
  return rows;
}

/** Import local measurements; invalid data is reported per row rather than imputed. */
export function processCsv(source) {
  const data = parseCsv(source);
  const headers = data.shift().map(h => h.trim());
  if (headers.some(h => !h) || new Set(headers).size !== headers.length) {
    throw new Error("CSV headers must be non-empty and unique");
  }
  for (const name of INPUT_COLUMNS) {
    if (!headers.includes(name)) throw new Error("Missing CSV column: " + name);
  }
  for (const name of OUTPUT_COLUMNS) {
    if (headers.includes(name)) throw new Error("Input CSV already contains output column: " + name);
  }
  const rows = [];
  let valid = 0, invalid = 0;
  for (const fields of data) {
    if (fields.length === 1 && fields[0] === "") continue;
    const item = Object.fromEntries(headers.map((h, i) => [h, fields[i] ?? ""]));
    try {
      if (fields.length !== headers.length) throw new Error("CSV column count mismatch");
      const nums = {};
      for (const key of INPUT_COLUMNS) {
        if (!item[key].trim()) throw new Error("Missing measurement: " + key);
        nums[key] = Number(item[key]);
      }
      const result = calculateFeUrea(nums);
      rows.push([...headers.map(h => item[h]), ...OUTPUT_COLUMNS.map(h => result[h])]);
      valid++;
    } catch (error) {
      rows.push([...headers.map(h => item[h]), "ERROR", "INVALID_INPUT", error.message]);
      invalid++;
    }
  }
  if (!rows.length) throw new Error("CSV contains no data rows");
  return { headers: [...headers, ...OUTPUT_COLUMNS], rows, valid, invalid };
}

/** Neutralize spreadsheet formulas in all exported user-controlled columns. */
export function serializeCsv(headers, rows) {
  const escapeCell = value => {
    let text = String(value ?? "");
    if (/^[\s]*[=+\-@]/.test(text)) text = "'" + text;
    return '"' + text.replace(/"/g, '""') + '"';
  };
  return [headers, ...rows].map(row => row.map(escapeCell).join(",")).join("\r\n") + "\r\n";
}
