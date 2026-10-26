# PlantScan AI â€” Mobile Application Setup & Architecture Guide

**Platform:** React Native (Expo SDK 51)
**Language:** TypeScript 5.9
**Source Directory:** `mobile_app/`
**State:** Production-Ready Client

---

## 1. Architecture Overview

The PlantScan AI mobile application provides a farmer-centric, high-contrast, field-accessible mobile client designed for smartphone image capture, two-stage pathology screening, and audio-guided Integrated Pest Management (IPM).

### Key Modules:
- **`src/screens/ScanScreen.tsx`**: Camera viewfinder capture, gallery selection, target crop selector, anatomical plant-part selector, image preview with retake capability, and loading feedback.
- **`src/screens/ResultScreen.tsx`**: Displays Stage 1 anatomical plant part with confidence badge, Stage 2 disease diagnosis, Plant Health Score gauge (0-100), lesion severity metrics, and overlay toggle.
- **`src/screens/TreatmentScreen.tsx`**: Structured IPM recommendations (Priority 1 Organic, Priority 2 Chemical, Priority 3 Cultural Prevention) with strict warnings against chemical applications for stem/bark samples.
- **`src/screens/SettingsScreen.tsx`**: Multilingual language switcher (English, Kannada, Hindi), backend API URL configuration, and live server health check.
- **`src/services/apiService.ts`**: Handles multipart/form-data image uploads to `/api/v1/predict` with a 20-second timeout, AbortController, and error parsing.
- **`src/services/speechService.ts`**: Native Text-To-Speech (TTS) using `expo-speech` with language codes `en-US`, `kn-IN`, and `hi-IN`.
- **`src/translations/index.ts`**: Localized string dictionaries for English, à²•à²¨à³à²¨à²¡ (Kannada), and à¤¹à¤¿à¤¨à¥à¤¦à¥€ (Hindi).

---

## 2. Prerequisites & Environment Setup

### Required Tools:
- **Node.js**: v18.0.0 or higher (v24.21.0 verified)
- **Package Manager**: `pnpm` (Corepack) or `npm`
- **Expo CLI**: Installed via local devDependencies or `npx expo`
- **Mobile Device / Emulator**:
  - Android Studio Emulator (uses default loopback `http://10.0.2.2:8000`)
  - Physical Android/iOS device running **Expo Go** (connects via local Wi-Fi IP `http://192.168.x.x:8000`)

---

## 3. Installation & Local Development

### 3.1 Install Dependencies
From the repository root or inside `mobile_app/`:
```bash
cd mobile_app
corepack pnpm install
```

### 3.2 Running the Development Server
```bash
corepack pnpm start
```
- Press `a` to open the Android emulator.
- Press `w` to open in a web browser.
- Scan the QR code using the **Expo Go** app on your physical mobile phone.

### 3.3 Connecting a Physical Phone to Local Backend
1. Connect your computer and mobile phone to the **same Wi-Fi network**.
2. Find your computer's local IP address (`ipconfig` on Windows, e.g. `192.168.1.15`).
3. Ensure FastAPI is running on `0.0.0.0`:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port 8000
   ```
4. In the mobile app, navigate to **Settings**, enter `http://192.168.1.15:8000`, and tap **Test Server Connection**.

---

## 4. Running Automated Tests & Type Checking

### 4.1 TypeScript Static Verification
Verifies that all components, screens, services, and types adhere to strict TypeScript checks with zero errors:
```bash
corepack pnpm typecheck
```

### 4.2 Jest Unit Test Suite
Runs all 11 unit tests covering API request serialization, speech service invocation, and multilingual dictionary completeness:
```bash
corepack pnpm test
```
Expected output:
```
PASS src/__tests__/localization.test.ts
PASS src/__tests__/speechService.test.ts
PASS src/__tests__/apiService.test.ts

Test Suites: 3 passed, 3 total
Tests:       11 passed, 11 total
```

---

## 5. Connecting to Live Cloud Deployment

When the backend is deployed to Render.com:
1. Open the mobile app.
2. Tap the **Settings** tab.
3. Tap **Use Render URL** (sets `https://plantscan-ai-backend.onrender.com`).
4. Tap **Save URL** and **Test Server Connection**.
