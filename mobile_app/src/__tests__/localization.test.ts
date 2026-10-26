import { translations, getTranslation } from '../translations';
import { SupportedLanguage } from '../types';

describe('Localization & Translation Unit Tests', () => {
  const languages: SupportedLanguage[] = ['en', 'kn', 'hi'];

  it.each(languages)('has all core translation keys for language: %s', (lang) => {
    const dict = getTranslation(lang);
    expect(dict).toBeDefined();
    expect(dict.appName).toBeDefined();
    expect(dict.appName.length).toBeGreaterThan(0);

    // Scan keys
    expect(dict.scan.title).toBeDefined();
    expect(dict.scan.takePhoto).toBeDefined();
    expect(dict.scan.chooseGallery).toBeDefined();
    expect(dict.scan.diagnose).toBeDefined();
    expect(dict.scan.timeoutMessage).toBeDefined();

    // Result keys
    expect(dict.result.plantPart).toBeDefined();
    expect(dict.result.diagnosis).toBeDefined();
    expect(dict.result.confidence).toBeDefined();
    expect(dict.result.healthScore).toBeDefined();
    expect(dict.result.listenAudio).toBeDefined();

    // Treatment keys
    expect(dict.treatment.title).toBeDefined();
    expect(dict.treatment.priority1Organic).toBeDefined();
    expect(dict.treatment.priority2Chemical).toBeDefined();
    expect(dict.treatment.stemBarkWarning).toBeDefined();
    expect(dict.treatment.stemBarkWarning.length).toBeGreaterThan(15);
  });

  it('falls back to English when unknown language is requested', () => {
    const dict = getTranslation('unknown' as any);
    expect(dict.appName).toBe('PlantScan AI');
  });
});
