# PlantScan AI - System Architecture

Version: 1.0

---

# 1. Overview

PlantScan AI is an AI-powered Plant Health Assistant designed to help farmers detect plant diseases, identify plant parts, provide treatment recommendations, and support both online and offline diagnosis.

The application follows a modular architecture where every component is independent and replaceable.

---

# 2. High-Level Architecture

                    User
                      │
                      ▼
          Mobile Application (React Native)
                      │
        ┌─────────────┴─────────────┐
        │                           │
        ▼                           ▼
 Offline Prediction          Online Prediction
(TensorFlow Lite)             (FastAPI Backend)
        │                           │
        └─────────────┬─────────────┘
                      ▼
              AI Prediction Engine
                      │
      ┌───────────────┼────────────────┐
      │               │                │
      ▼               ▼                ▼
Plant Part      Disease Model    Unknown Detector
Classifier
      │               │                │
      └───────────────┼────────────────┘
                      ▼
            Recommendation Engine
                      │
     ┌────────┬────────┬────────┬────────┐
     ▼        ▼        ▼        ▼
 Organic  Chemical Prevention Voice Output

---

# 3. Major Components

## Mobile Application

Responsibilities

- Capture plant image
- Display prediction
- Voice assistance
- Offline prediction
- Online prediction
- History

Technology

- React Native

---

## Backend

Responsibilities

- Receive images
- Run AI models
- Store prediction history
- Return treatment recommendations
- Handle multilingual responses

Technology

- FastAPI
- Python

---

## AI Module

Responsible for all machine learning tasks.

Contains three independent models.

### Model 1

Plant Part Classification

Output

- Leaf
- Stem
- Fruit
- Bark

---

### Model 2

Disease Classification

Example

Tomato

↓

Early Blight

Confidence

95%

---

### Model 3

Unknown Disease Detection

If confidence is below the threshold,

Prediction

↓

Unknown Disease

Instead of giving an incorrect diagnosis.

---

## Recommendation Engine

Responsible for generating:

- Organic treatment
- Chemical treatment
- Prevention methods

Priority

Organic

↓

Chemical

↓

Prevention

---

## Voice Module

Reads results aloud.

Languages

- English
- Kannada
- Hindi

Future

Additional Indian languages.

---

# 4. Prediction Workflow

User

↓

Capture Image

↓

Image Preprocessing

↓

Plant Part Detection

↓

Disease Detection

↓

Confidence Evaluation

↓

Health Score Calculation

↓

Treatment Recommendation

↓

Voice Output

↓

History

---

# 5. Offline Workflow

Camera

↓

TensorFlow Lite Model

↓

Prediction

↓

Treatment

↓

Voice

No Internet Required

---

# 6. Online Workflow

Camera

↓

FastAPI

↓

AI Models

↓

Prediction

↓

Database

↓

Response

---

# 7. Plant Health Report

Every prediction returns

- Plant Name
- Plant Part
- Disease
- Confidence
- Health Score
- Organic Treatment
- Chemical Treatment
- Prevention Tips

---

# 8. Future Modules

Future versions may include

- Weather Prediction
- GPS Disease Map
- Recovery Tracking
- Expert Consultation
- Farmer Community
- IoT Integration
- Drone Support

---

# 9. Project Modules

PlantScanAI

├── Backend

├── Mobile Application

├── Machine Learning

├── Dataset Management

├── Treatment Database

├── Documentation

---

# 10. Design Principles

- Modular Architecture
- Offline First
- Mobile Optimized
- Sustainable Agriculture
- Explainable AI
- Easy Model Replacement