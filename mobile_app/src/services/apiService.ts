import { environment } from '../config/environment';
import { PredictionResponse, SupportedLanguage } from '../types';

export class ApiError extends Error {
  public code: string;
  public status?: number;
  public details?: any;

  constructor(message: string, code: string, status?: number, details?: any) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.status = status;
    this.details = details;
  }
}

export class ApiService {
  /**
   * Uploads an image to the PlantScan AI backend for Two-Stage classification.
   */
  public static async predictImage(
    imageUri: string,
    cropHint?: string,
    plantPartHint?: string,
    language: SupportedLanguage = 'en'
  ): Promise<PredictionResponse> {
    const url = `${environment.apiUrl}/api/v1/predict`;
    const formData = new FormData();

    const filename = imageUri.split('/').pop() || 'leaf.jpg';
    const match = /\.(\w+)$/.exec(filename);
    const type = match ? `image/${match[1].toLowerCase() === 'jpg' ? 'jpeg' : match[1].toLowerCase()}` : 'image/jpeg';

    // React Native FormData file specification
    formData.append('file', {
      uri: imageUri,
      name: filename,
      type: type,
    } as any);

    if (cropHint && cropHint !== 'Auto-Detect') {
      formData.append('crop_hint', cropHint);
    }
    if (plantPartHint && plantPartHint !== 'Auto-Detect') {
      formData.append('plant_part_hint', plantPartHint);
    }
    formData.append('language', language);

    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), environment.timeoutMs);

    try {
      const response = await fetch(url, {
        method: 'POST',
        body: formData,
        headers: {
          Accept: 'application/json',
        },
        signal: controller.signal,
      });

      clearTimeout(timeoutId);

      const data = await response.json();

      if (!response.ok) {
        throw new ApiError(
          data?.message || data?.detail?.message || 'Server error occurred during prediction.',
          data?.error_code || data?.detail?.error_code || 'SERVER_ERROR',
          response.status,
          data
        );
      }

      return data as PredictionResponse;
    } catch (err: any) {
      clearTimeout(timeoutId);

      if (err.name === 'AbortError') {
        throw new ApiError(
          'Diagnostic request timed out after 20 seconds. Please retry.',
          'TIMEOUT',
          408
        );
      }
      if (err instanceof ApiError) {
        throw err;
      }
      throw new ApiError(
        'Unable to reach PlantScan AI backend. Check network connectivity or server URL.',
        'NETWORK_ERROR',
        0,
        err.message
      );
    }
  }

  /**
   * Checks the operational health of the backend API.
   */
  public static async checkHealth(): Promise<{ status: string; engine: string; ready: boolean }> {
    const url = `${environment.apiUrl}/api/v1/health`;
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 6000);

    try {
      const res = await fetch(url, { signal: controller.signal });
      clearTimeout(timeoutId);
      if (!res.ok) {
        return { status: 'error', engine: 'Unknown', ready: false };
      }
      const data = await res.json();
      return {
        status: data.status || 'healthy',
        engine: data.active_model_engine || 'TFLiteModelEngine',
        ready: true,
      };
    } catch (e) {
      clearTimeout(timeoutId);
      return { status: 'offline', engine: 'None', ready: false };
    }
  }
}
