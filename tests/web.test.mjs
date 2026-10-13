import test from "node:test";
import assert from "node:assert/strict";
import {
  INPUT_COLUMNS, OUTPUT_COLUMNS, calculateFeUrea, parseCsv,
  processCsv, serializeCsv
} from "../web/core.mjs";

const values = (overrides = {}) => ({
  serum_creatinine: 1, urine_creatinine: 100,
  serum_urea: 20, urine_urea: 100, ...overrides
});

test("FEUrea 5%, 35% boundary, and 40% classifications", () => {
  assert.equal(calculateFeUrea(values()).fe_urea_percent, 5);
  assert.equal(calculateFeUrea(values()).classification, "Prerenal Azotemia");
  assert.equal(calculateFeUrea(values({urine_urea: 700})).fe_urea_percent, 35);
  assert.match(calculateFeUrea(values({urine_urea: 700})).classification, /Intrinsic/);
  assert.equal(calculateFeUrea(values({urine_urea: 800})).fe_urea_percent, 40);
});
test("Changing units consistently within a pair does not change FEUrea", () => {
  const original = calculateFeUrea(values({urine_urea: 700}));
  const rescaled = calculateFeUrea(values({
    serum_creatinine: 88.4, urine_creatinine: 8840,
    serum_urea: 42.8, urine_urea: 1498
  }));
  assert.equal(original.fe_urea_percent, rescaled.fe_urea_percent);
});
test("Reject zero, negatives, NaN, Infinity, missing strings and overflow", () => {
  for (const invalid of [0, -1, NaN, Infinity, -Infinity, "", undefined]) {
    assert.throws(() => calculateFeUrea(values({serum_urea: invalid})), RangeError);
  }
  assert.throws(() => calculateFeUrea(values({urine_urea: 1e308, serum_creatinine: 1e308})), RangeError);
});
test("Quoted CSV parsing supports commas, newlines, CRLF, escaping and BOM", () => {
  const input = "\uFEFFa,b\r\n\"one,two\",\"a\"\"b\"\r\n\"multi\nline\",ok\r\n";
  assert.deepEqual(parseCsv(input), [
    ["a", "b"], ["one,two", 'a"b'], ["multi\nline", "ok"]
  ]);
  assert.throws(() => parseCsv('a,b\n"unclosed'), /Unclosed/);
  assert.throws(() => parseCsv('a,b\n"test"x,2'), /Unexpected character/);
});
test("Batch processes valid rows and preserves invalid records without imputation", () => {
  const data = [
    "record_id,serum_creatinine,urine_creatinine,serum_urea,urine_urea",
    "A,1,100,20,700",
    "B,1,100,,700",
    "C,1,100,20,not-a-number",
    "D,1,100,20,0",
    "E,1,100,20,700,extra"
  ].join("\n");
  const result = processCsv(data);
  assert.equal(result.valid, 1);
  assert.equal(result.invalid, 4);
  assert.deepEqual(result.headers.slice(-3), OUTPUT_COLUMNS);
  assert.equal(result.rows[0].at(-3), 35);
  assert.deepEqual(result.rows.slice(1).map(r => r.at(-2)), Array(4).fill("INVALID_INPUT"));
});
test("Batch rejects missing, duplicate and conflicting headers", () => {
  assert.throws(() => processCsv("serum_creatinine,urine_creatinine\n1,2"), /Missing CSV column/);
  assert.throws(() => processCsv("serum_creatinine,serum_creatinine,urine_creatinine,serum_urea,urine_urea\n1,2,3,4,5"), /unique/);
  assert.throws(() => processCsv(INPUT_COLUMNS.concat("classification").join(",") + "\n1,2,3,4,A"), /output column/);
  assert.throws(() => processCsv(INPUT_COLUMNS.join(",") + "\n"), /no data rows/);
});
test("Export prevents CSV formula execution and round-trips quoted text", () => {
  const exportText = serializeCsv(["label", "note"], [["=1+2", 'a,"b"\nnext'], [" @SUM(1)", "+HYPERLINK"]]);
  const rows = parseCsv(exportText);
  assert.equal(rows[1][0], "'=1+2");
  assert.equal(rows[2][0], "' @SUM(1)");
  assert.equal(rows[2][1], "'+HYPERLINK");
  assert.equal(rows[1][1], 'a,"b"\nnext');
});
test("Batch export retains all columns for every processed row", () => {
  const input = INPUT_COLUMNS.join(",") + "\n1,100,20,100\n";
  const result = processCsv(input);
  const exported = parseCsv(serializeCsv(result.headers, result.rows));
  assert.equal(exported[0].length, INPUT_COLUMNS.length + OUTPUT_COLUMNS.length);
  assert.equal(exported[1].at(-3), "5");
});
