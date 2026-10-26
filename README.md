# 🌿 PlantScan AI

> **Multi-Crop Disease Diagnosis & Integrated Pest Management (IPM) Advisory System using Deep Learning & Mobile-Cloud Architecture**

---

## 🚀 Quick Execution (1-Click Batch Scripts)

On Windows, you can double-click or run these batch scripts directly in your terminal:

- 🧪 **Run Automated Unit Tests**: `.\run_tests.bat`
- 🌐 **Start FastAPI Server**: `.\run_backend.bat` (`http://localhost:8000/docs`)
- 🔍 **Run Disease Predictor CLI**: `.\run_predictor.bat`

---

## 📚 Complete Project Documentation

For detailed technical design and step-by-step execution guides, please see:

- 📖 **[Project Technical Overview](PROJECT_OVERVIEW.md)**: Full architecture breakdown, 10 crops, 46 canonical classes, dataset deduplication, and ML pipeline details.
- 🛠️ **[Step-by-Step Execution Guide](HOW_TO_RUN.md)**: Complete guide to running unit tests, backend API, model inference CLI, and mobile client.

---

## ⚡ Technical Highlights

- **10 Agricultural Crops**: Apple, Banana, Bell Pepper, Cotton, Grape, Maize, Mango, Potato, Rice, Tomato.
- **46 Canonical Classes**: Fine-grained disease classifications + healthy leaf detection.
- **Integrated Pest Management (IPM)**: Organic, biological, and chemical treatment guidelines with PPE safety rules.
- **Dual Inference Engine**: MobileNetV2 edge TensorFlow Lite (`.tflite`) model with thread-safe inference locks and dynamic multi-crop routing.
- **Foliar Lesion Quantification**: HSV-based chromatic segmentation estimating affected foliar area and lesion severity.
- **Out-of-Scope & Ambiguity Rejection**: Confidence thresholding ($<70\%$) and variance-based quality checks for low-certainty inputs.
- **Production-Hardened REST API**: FastAPI backend with automated Pytest test suite (35/35 tests passing), OWASP security headers, sliding-window rate limiting, and Kubernetes/orchestrator `/api/v1/ready` probes.

---

## 🔒 Production Security & Environment Configuration

PlantScanAI conforms to 12-factor application configuration principles via environment variables:

| Variable | Default | Production Default | Description |
| :--- | :--- | :--- | :--- |
| `PLANTSCAN_ENV` | `development` | `production` | Environment mode (`development`, `staging`, `production`) |
| `PLANTSCAN_DEBUG` | `true` | `false` | Controls OpenAPI `/docs` and interactive schemas exposure |
| `PLANTSCAN_CORS_ORIGINS` | `*` | `http://localhost:8000` | Comma-separated allowed CORS origins |
| `PLANTSCAN_ENABLE_SIMULATION_HEADERS` | `true` | `false` | Gating for `X-Simulate-Class` diagnosis overrides |
| `PLANTSCAN_ENABLE_MOCK_FALLBACK` | `true` | `false` | Prohibits synthetic predictions when model weights are missing |
| `PLANTSCAN_RATE_LIMIT_ENABLED` | `true` | `true` | Enables per-IP sliding-window rate limiting |
| `PLANTSCAN_RATE_LIMIT_RPM` | `60` | `60` | Maximum allowed inference requests per minute per IP |
| `PLANTSCAN_MAX_IMAGE_SIZE_MB` | `10` | `10` | Maximum raw file upload size in megabytes |
| `PLANTSCAN_MAX_IMAGE_PIXELS` | `10000000` | `10000000` | PIL decompression bomb protection limit (10 MP) |
| `PLANTSCAN_MAX_BASE64_CHARS` | `15728640` | `15728640` | Maximum Base64 payload length (~15MB chars) |

---

## 📡 Core API Endpoints

- `GET /` — Root service descriptor and UI redirect.
- `GET /api/v1/health` — Process liveness probe.
- `GET /api/v1/ready` — Application readiness probe (verifies TFLite tensor allocation and treatment database integrity; returns HTTP 503 if unready).
- `GET /api/v1/info` — Metadata, supported crops list, and validation boundaries.
- `POST /api/v1/predict` — Multipart image upload with foliar lesion analysis and IPM advisory.
- `POST /api/v1/predict/json` — Base64 JSON payload endpoint for mobile/edge clients.
- `GET /api/v1/treatments/crops` — List of supported crops.
- `GET /api/v1/treatments/classes` — 46 canonical disease classes.
- `GET /api/v1/treatments/{class_name}` — Multilingual IPM protocols (English, Kannada, Hindi).