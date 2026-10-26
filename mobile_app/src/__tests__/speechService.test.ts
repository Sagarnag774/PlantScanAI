import { SpeechService } from '../services/speechService';
import * as Speech from 'expo-speech';
import { PredictionResponse } from '../types';

jest.mock('expo-speech', () => ({
  speak: jest.fn(),
  stop: jest.fn().mockResolvedValue(undefined),
  isSpeakingAsync: jest.fn().mockResolvedValue(false),
}));

describe('SpeechService Unit Tests', () => {
  const sampleResult: PredictionResponse = {
    status: 'success',
    crop: 'Tomato',
    predicted_class: 'tomato_early_blight',
    display_name: 'Tomato Early Blight',
    confidence: 0.94,
    is_healthy: false,
    plant_part: 'Leaf',
    plant_health_score: 45,
    recommendation: {
      summary: 'Prune affected leaves and apply neem oil.',
      organic: [{ name: 'Neem Oil Spray' }],
      chemical: [{ name: 'Copper Oxychloride' }],
      prevention: ['Water at base.'],
      safety_notes: ['Wear gloves.'],
      disclaimer: 'Advisory.',
      sources: [],
    },
    model_version: 'v1',
    inference_time_ms: 50,
  };

  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('invokes expo-speech speak with en-US language code for English', async () => {
    await SpeechService.speakDiagnosis(sampleResult, 'en');

    expect(Speech.speak).toHaveBeenCalledTimes(1);
    const [spokenText, options] = (Speech.speak as jest.Mock).mock.calls[0];
    expect(spokenText).toContain('PlantScan diagnostic report');
    expect(spokenText).toContain('Tomato');
    expect(spokenText).toContain('Leaf');
    expect(options.language).toBe('en-US');
  });

  it('invokes expo-speech speak with kn-IN language code for Kannada', async () => {
    await SpeechService.speakDiagnosis(sampleResult, 'kn');

    expect(Speech.speak).toHaveBeenCalledTimes(1);
    const [spokenText, options] = (Speech.speak as jest.Mock).mock.calls[0];
    expect(spokenText).toContain('ಪ್ಲಾಂಟ್‌ಸ್ಕ್ಯಾನ್');
    expect(options.language).toBe('kn-IN');
  });

  it('invokes expo-speech speak with hi-IN language code for Hindi', async () => {
    await SpeechService.speakDiagnosis(sampleResult, 'hi');

    expect(Speech.speak).toHaveBeenCalledTimes(1);
    const [spokenText, options] = (Speech.speak as jest.Mock).mock.calls[0];
    expect(spokenText).toContain('प्लांटस्कैन');
    expect(options.language).toBe('hi-IN');
  });

  it('stops speech playback cleanly', async () => {
    await SpeechService.stop();
    expect(Speech.stop).toHaveBeenCalled();
    expect(SpeechService.isSpeaking()).toBe(false);
  });
});
