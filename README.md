# FEUrea Calculator

Calculate **fractional excretion of urea (FEUrea)** from paired serum and urine measurements. This repository provides a standalone browser calculator, a Python CLI (single case and CSV batch), and a FastAPI endpoint. The separate audit-agent interface is retained for backward compatibility; it is not the FEUrea calculation algorithm.

## Browser calculator

The static app is located at [web/index.html](web/index.html). When GitHub Pages is configured to publish the repository root, the top-level [index.html](index.html) redirects visitors to the calculator.

- Enter serum creatinine, urine creatinine, serum urea (or BUN), and urine urea (or BUN).
- Select the measurement conventions used in the paired samples; **do not mix serum BUN with urine urea** or mix units within an analyte pair.
- Calculate FEUrea and view the conventional 35% interpretation with diagnostic limitations.
- Import a local UTF-8 CSV (up to **2 MB / 5,000 rows**) and download results, including row-level input errors.
- Browser calculations use local JavaScript: no backend, network requests, browser storage, or Pyodide is required. No measurements are uploaded by the app.

**CSV columns:** `serum_creatinine,urine_creatinine,serum_urea,urine_urea`. Additional columns are retained. Within each serum/urine analyte pair, use matching units and analyte definitions throughout the file. Avoid patient-identifiable data.

## Calculation and clinical limitations

```text
FEUrea (%) = (Urine urea × Serum creatinine)
            / (Serum urea × Urine creatinine) × 100
```

Paired BUN values can replace paired urea values because their conversion factor cancels. Serum and urine creatinine units must match. All measurements must be finite and positive.

| FEUrea | Conventional association |
| --- | --- |
| Below 35% | Compatible with prerenal physiology |
| 35% or higher | May occur with intrinsic AKI |

**FEUrea cannot independently establish the cause of AKI or determine fluid treatment.** Diagnostic accuracy is heterogeneous and context-dependent, including in patients receiving diuretics. Consider clinical history, hemodynamics, medications, urine findings, and other causes of AKI.

Evidence: [2024 systematic review and meta-analysis](https://pubmed.ncbi.nlm.nih.gov/38768779/) (PMID 38768779); [2026 systematic review and meta-analysis](https://pubmed.ncbi.nlm.nih.gov/41535079/) (PMID 41535079).

## Python installation and usage

Requires Python 3.10+:

```bash
git clone https://github.com/abusuraihsakhri/fe-urea-calculator.git
cd fe-urea-calculator
python -m pip install -e ".[dev]"
python -m fe_urea single --serum-creatinine 1.2 --urine-creatinine 120 \
  --serum-urea 25 --urine-urea 250
python -m fe_urea batch -i sample.csv -o results.csv
```

The Python batch command accepts legacy `v1,v2,v3` columns for compatibility. The legacy `calculate_metrics()` wrapper can synthesize defaults and is **not suitable for evaluating incomplete clinical cases**; the batch importer requires complete measurements. CLI single-case defaults are illustrative only.

## API and legacy agent demonstration

Start the API:

```bash
python cli.py serve --host 127.0.0.1 --port 8000
```

Use `POST /api/fe-urea` with JSON numbers for `serum_creatinine`, `urine_creatinine`, `serum_urea`, and `urine_urea`. Invalid measurements return HTTP 422. Interactive API documentation is served at `/docs`. The original `/api/audit`, `/api/chat`, `/metrics`, and audit endpoints remain for compatibility; `/metrics` returns JSON rather than Prometheus text.

Legacy workers use generic demonstration thresholds that are **not validated FEUrea decision rules**. The conversational adapter produces a deterministic mock response, not clinical verification or an external model call.

Audit logs exist in process memory and use HMAC-SHA256 integrity checks. If running the demonstration audit service beyond local development, configure `AUDIT_SECRET_KEY` securely. Identifier-pattern screening is not comprehensive de-identification or a HIPAA compliance guarantee. Do not send real patient identifiers to the demonstration API.

## Testing and deployment

```bash
python -m pytest -v
python -m compileall -q .
node --check web/app.js
node --test tests/web.test.mjs
```

CI runs Python on 3.10–3.12 and the Node test suite in each matrix entry. The browser app has no build pipeline; the root `index.html` and `web/` directory must be published together for the default GitHub Pages redirect to work.

The repository also includes a `Dockerfile` and `docker-compose.yml` for running the Python API. The static browser app works independently from the container.

**Browser compatibility:** Modern Chromium, Firefox and Safari with ES module support. The UI is responsive and keyboard accessible; live-browser end-to-end testing is separate from the automated unit suite.

## Privacy and license

Browser calculations and CSV parsing run locally. The app neither stores measurements persistently nor transmits input to a remote calculation service. Local CSV exports remain the user's responsibility. The Python API is a separate service and processes data sent to it.

[MIT License](LICENSE).
