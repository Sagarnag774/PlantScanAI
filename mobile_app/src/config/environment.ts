/**
 * PlantScan AI Mobile Application Environment Configuration
 * Supports dynamic local network IP addressing (for physical devices),
 * Android emulator loopback (10.0.2.2), iOS simulator (localhost),
 * and live cloud deployment (Render.com).
 */

declare const process: any;

class EnvironmentConfig {
  // Default Render production URL / local fallback
  private _apiUrl: string = 'http://10.0.2.2:8000';
  private _renderUrl: string = 'https://plantscan-ai-backend.onrender.com';
  private _timeoutMs: number = 20000;

  constructor() {
    // Check if injected via Expo public env
    const expoPublic = process.env.EXPO_PUBLIC_API_URL;
    if (expoPublic && expoPublic.trim().length > 0) {
      this._apiUrl = expoPublic.trim();
    }
  }

  public get apiUrl(): string {
    return this._apiUrl;
  }

  public set apiUrl(url: string) {
    if (url && url.startsWith('http')) {
      this._apiUrl = url.replace(/\/+$/, '');
    }
  }

  public get renderUrl(): string {
    return this._renderUrl;
  }

  public get timeoutMs(): number {
    return this._timeoutMs;
  }
}

export const environment = new EnvironmentConfig();
