# Fe Urea Calculator

> **Domain:** Nephrology & Renal Replacement Protocols
> **Reference Guidelines & Standards:** KDIGO & KDOQI Clinical Guidelines

<div align="center">

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?logo=python&logoColor=white)
![FastAPI](https://img.shields.io/badge/FastAPI-0.111-009688.svg?logo=fastapi&logoColor=white)
![Audit Trail](https://img.shields.io/badge/Audit-HMAC--SHA256_Tamper--Evident-brightgreen.svg)
![Zero-PHI Guard](https://img.shields.io/badge/Guard-Zero--PHI_Outbound-blue.svg)
![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg?logo=docker&logoColor=white)

</div>

---

## 📖 What It Does

Fractional Excretion of Urea (FEUrea) Calculator differentiates prerenal azotemia from acute tubular necrosis (ATN) when diuretics invalidate FENa (Fractional Excretion of Sodium).

Zero-dependency Python implementation with single and batch evaluation capabilities.

Author: Dr. Abu Suraih Sakhri
License: MIT

---

## ⚙️ Key Capabilities & Algorithmic Modules

### 🔬 Analytical Functions

- **`calculate_fe_urea()`**: Core FEUrea calculation using the standard formula.
- **`calculate_metrics()`**: Legacy compatibility wrapper supporting v1/v2/v3 parameters.
- **`process_single()`**: Evaluate a single case from CLI arguments.
- **`process_batch()`**: Process CSV files with multiple patient records.

---

## 📐 Mathematical Formulation

The Fractional Excretion of Urea is calculated as:

```
FEUrea = (Urine_Urea × Serum_Creatinine) / (Serum_Urea × Urine_Creatinine) × 100
```

### Clinical Interpretation

| FEUrea Value | Classification | Recommendation |
|:-------------|:---------------|:---------------|
| < 35% | Prerenal Azotemia | Consider volume resuscitation and hemodynamic optimization |
| >= 35% | Acute Tubular Necrosis / Intrinsic Renal Disease | Avoid volume overload; consider nephrology consultation |

---

## 💻 Installation

```bash
# Clone the repository
git clone https://github.com/abusuraihsakhri/fe-urea-calculator.git
cd fe-urea-calculator

# Install dependencies
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

---

## 🚀 CLI Quickstart & Usage

### 1. Single Case Evaluation
```bash
python -m fe_urea single --serum-creatinine 1.2 --urine-creatinine 120.0 --serum-urea 25.0 --urine-urea 250.0
```

### 2. Batch CSV Processing
```bash
python -m fe_urea batch -i sample.csv -o results.csv
```

### Parameter Reference
| Parameter | Description | Default |
|:----------|:------------|:--------|
| `--serum-creatinine` | Serum creatinine (mg/dL) | 1.0 |
| `--urine-creatinine` | Urine creatinine (mg/dL) | 100.0 |
| `--serum-urea` | Serum urea (mg/dL) | 20.0 |
| `--urine-urea` | Urine urea (mg/dL) | 200.0 |

### Input Data Schema (CSV)

| Field | Description | Requirement |
|:------|:------------|:------------|
| `Patient_ID` | Patient identifier | Required |
| `serum_creatinine` | Serum creatinine concentration (mg/dL) | Required |
| `urine_creatinine` | Urine creatinine concentration (mg/dL) | Required |
| `serum_urea` | Serum urea concentration (mg/dL) | Required |
| `urine_urea` | Urine urea concentration (mg/dL) | Required |

---

## 🛡️ Security & Enterprise Architecture

* **Zero-PHI Outbound Interceptor:** Active regex inspection blocking SSNs, MRNs, phone numbers, and patient identifiers.
* **Tamper-Evident HMAC-SHA256 Audit Trail:** Chained, cryptographically signed logs for every evaluation.
* **FastAPI & Prometheus Telemetry:** Exposes OpenAPI 3.1 REST endpoints and operational Prometheus metrics (`/metrics`).

### Environment Variables

| Variable | Description | Default |
|:---------|:------------|:--------|
| `AUDIT_SECRET_KEY` | HMAC secret key for audit trail signing | Random (generated per session) |
| `MODEL_PROVIDER` | LLM provider for supervisor chat | `mock` |

> **Security Note:** Always set `AUDIT_SECRET_KEY` in production environments to ensure consistent audit trail verification across restarts.

---

## 🧪 Testing & Verification

Run the automated test suite:

```bash
pytest -v
```

Execute high-throughput batch simulation benchmarks:

```bash
python simulator.py --tasks 1000 --concurrency 8
```

---

## 🐳 Container Deployment

```bash
# Build and run with Docker
docker build -t fe-urea-calculator .
docker run -p 8000:8000 -e AUDIT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))") fe-urea-calculator

# Or use Docker Compose
docker-compose up -d
```

---

## 📁 Project Structure

```
fe-urea-calculator/
├── fe_urea.py              # Core FEUrea calculation logic
├── cli.py                  # Enterprise CLI interface
├── simulator.py            # High-throughput simulation testing
├── enrichment.py           # Domain enrichment engines
├── sample.csv              # Sample input data
├── test_fe_urea.py         # Core functionality tests
├── agents/                 # Enterprise agent framework
│   ├── __init__.py
│   ├── api.py              # FastAPI REST endpoints
│   ├── base.py             # Security, PHI guard, audit trail
│   ├── models.py           # Pydantic data models
│   ├── supervisor.py       # Multi-agent orchestrator
│   ├── workers.py          # Specialized domain workers
│   ├── llm_factory.py      # LLM provider factory
│   ├── learning.py         # Bayesian calibration engine
│   ├── metrics.py          # Prometheus metrics exporter
│   └── streamer.py         # WebSocket telemetry streamer
├── tests/                  # Additional test suites
│   ├── test_enrichment.py
│   └── test_fe_urea_calculator.py
├── web/                    # Operations console UI
│   └── index.html
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
└── README.md
```

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
