# PlantScan AI - Decision Log

---

## Decision 001

**Date:** 2026-08-07

### Decision

The project will follow a modular architecture instead of a single monolithic application.

### Reason

Separating the project into independent modules improves maintainability, debugging, testing, and future scalability.

### Modules

- Dataset Management
- Data Preprocessing
- Plant Part Classification
- Disease Classification
- Unknown Disease Detection
- Treatment Recommendation
- Backend API
- Mobile Application

### Alternatives Considered

Single project with all code in one folder.

### Reason Rejected

Would become difficult to maintain as the project grows.

---

## Decision 002

**Date:** 2026-08-07

### Decision

Use MobileNetV2 as the first disease classification model.

### Reason

- Lightweight
- Fast inference
- TensorFlow Lite support
- Suitable for mobile deployment
- Strong research support for plant disease classification

### Alternatives

- EfficientNet-B0
- ResNet50
- DenseNet121

### Reason Rejected

Higher computational requirements with limited benefit for the first version.

---

## Decision 003

**Date:** 2026-08-07

### Decision

Develop one mobile application supporting both Offline and Online prediction modes.

### Reason

Maintaining a single application reduces development effort and provides a consistent user experience.

### Workflow

Internet Available
→ Cloud Prediction

Internet Unavailable
→ TensorFlow Lite Offline Prediction

### Alternative

Develop two separate applications.

### Reason Rejected

Would duplicate development, testing, and maintenance effort.

---

## Decision 004

**Date:** 2026-08-07

### Decision

Treatment recommendations will prioritize organic methods before chemical methods.

### Reason

- Encourages environmentally friendly farming
- Reduces unnecessary chemical usage
- Better aligns with sustainable agriculture goals

### Workflow

Disease

↓

Organic Treatment

↓

Chemical Treatment (if required)

↓

Prevention Tips

---

## Decision 005

**Date:** 2026-08-07

### Decision

Support multilingual output.

### Initial Languages

- English
- Kannada
- Hindi

### Future

Additional Indian regional languages.

---

## Decision 006

**Date:** 2026-08-07

### Decision

Follow an Engineering First approach.

### Development Order

Planning

↓

Dataset

↓

EDA

↓

Preprocessing

↓

Training

↓

Evaluation

↓

Backend

↓

Mobile Application

↓

Deployment

### Reason

Avoids redesign later and produces a more maintainable system.