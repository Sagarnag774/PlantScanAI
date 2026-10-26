import { ApiService, ApiError } from '../services/apiService';
import { environment } from '../config/environment';

declare const global: any;

describe('ApiService Unit Tests', () => {
  beforeEach(() => {
    environment.apiUrl = 'http://test-server:8000';
    // Mock global fetch
    (global as any).fetch = jest.fn();
  });

  afterEach(() => {
    jest.resetAllMocks();
  });

  it('correctly constructs multipart request and parses successful prediction response', async () => {
    const mockResponse = {
      status: 'success',
      crop: 'Tomato',
      predicted_class: 'tomato_early_blight',
      display_name: 'Tomato Early Blight',
      confidence: 0.94,
      is_healthy: false,
      plant_part: 'Leaf',
      plant_part_confidence: 0.96,
      plant_health_score: 45,
      recommendation: {
        summary: 'Targeted early blight treatment.',
        organic: [{ name: 'Neem Oil Spray' }],
        chemical: [{ name: 'Mancozeb 75 WP' }],
        prevention: ['Avoid overhead splash.'],
        safety_notes: ['Wear gloves and mask.'],
        disclaimer: 'Advisory only.',
        sources: ['PlantScan AI KB'],
      },
      model_version: 'MobileNetV2-PlantScan-v1',
      inference_time_ms: 125.4,
    };

    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await ApiService.predictImage(
      'file:///data/user/0/leaf.jpg',
      'Tomato',
      'Leaf',
      'en'
    );

    expect(result.status).toBe('success');
    expect(result.crop).toBe('Tomato');
    expect(result.predicted_class).toBe('tomato_early_blight');
    expect(result.confidence).toBe(0.94);
    expect(result.plant_part).toBe('Leaf');
    expect(result.plant_health_score).toBe(45);
    expect((global as any).fetch).toHaveBeenCalledTimes(1);
    expect((global as any).fetch.mock.calls[0][0]).toBe('http://test-server:8000/api/v1/predict');
  });

  it('correctly parses unsupported plant part disease response', async () => {
    const mockResponse = {
      status: 'unsupported_part_disease',
      crop: 'Tomato',
      predicted_class: 'unsupported_part_disease',
      display_name: 'Unsupported Plant Part (Stem)',
      confidence: 0.25,
      is_healthy: false,
      plant_part: 'Stem',
      plant_part_confidence: 0.88,
      plant_health_score: 50,
      recommendation: {
        summary: 'Deep learning models for stem pathology are in development.',
        organic: [],
        chemical: [],
        prevention: ['Sterilize pruning tools.'],
        safety_notes: ['Do not apply chemical pesticides without laboratory confirmation.'],
        disclaimer: 'Advisory only.',
        sources: ['PlantScan AI KB'],
      },
      model_version: 'MobileNetV2-PlantScan-v1',
      inference_time_ms: 65.2,
    };

    (global as any).fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockResponse,
    });

    const result = await ApiService.predictImage(
      'file:///data/user/0/stem.jpg',
      'Tomato',
      'Stem',
      'en'
    );

    expect(result.status).toBe('unsupported_part_disease');
    expect(result.plant_part).toBe('Stem');
    expect(result.recommendation?.chemical.length).toBe(0);
  });

  it('throws ApiError with NETWORK_ERROR code on network failure', async () => {
    (global as any).fetch.mockRejectedValueOnce(new Error('Failed to connect'));

    await expect(
      ApiService.predictImage('file:///data/user/0/leaf.jpg')
    ).rejects.toThrow(ApiError);
  });
});
