import * as Speech from 'expo-speech';
import { PredictionResponse, SupportedLanguage } from '../types';

export class SpeechService {
  private static _isSpeaking: boolean = false;

  private static getLanguageCode(lang: SupportedLanguage): string {
    switch (lang) {
      case 'kn':
        return 'kn-IN';
      case 'hi':
        return 'hi-IN';
      case 'en':
      default:
        return 'en-US';
    }
  }

  /**
   * Reads the diagnostic summary aloud in the specified language.
   */
  public static async speakDiagnosis(
    result: PredictionResponse,
    language: SupportedLanguage = 'en'
  ): Promise<void> {
    try {
      await Speech.stop();

      const langCode = this.getLanguageCode(language);
      let textToSpeak = '';

      if (language === 'kn') {
        textToSpeak = `ಪ್ಲಾಂಟ್‌ಸ್ಕ್ಯಾನ್ ರೋಗನಿರ್ಣಯ ವರದಿ. ಬೆಳೆ: ${result.crop}. ಸಸ್ಯದ ಅಂಗಾಂಗ: ${result.plant_part}. ಸ್ಥಿತಿ: ${result.display_name}. ವಿಶ್ವಾಸಾರ್ಹತೆ: ಶೇಕಡಾ ${Math.round(result.confidence * 100)}. ಸಸ್ಯ ಆರೋಗ್ಯ ಸ್ಕೋರ್: ನೂರರಲ್ಲಿ ${result.plant_health_score}.`;
        if (result.recommendation?.summary) {
          textToSpeak += ` ಸಲಹೆ: ${result.recommendation.summary}`;
        }
      } else if (language === 'hi') {
        textToSpeak = `प्लांटस्कैन रोग निदान रिपोर्ट। फसल: ${result.crop}। पौधे का अंग: ${result.plant_part}। स्थिति: ${result.display_name}। सटीकता: ${Math.round(result.confidence * 100)} प्रतिशत। स्वास्थ्य स्कोर: 100 में से ${result.plant_health_score}।`;
        if (result.recommendation?.summary) {
          textToSpeak += ` सलाह: ${result.recommendation.summary}`;
        }
      } else {
        textToSpeak = `PlantScan diagnostic report. Target crop: ${result.crop}. Plant part: ${result.plant_part}. Diagnosis: ${result.display_name}. Confidence score: ${Math.round(result.confidence * 100)} percent. Plant health score: ${result.plant_health_score} out of 100.`;
        if (result.recommendation?.summary) {
          textToSpeak += ` Advisory summary: ${result.recommendation.summary}`;
        }
      }

      this._isSpeaking = true;
      Speech.speak(textToSpeak, {
        language: langCode,
        pitch: 1.0,
        rate: 0.95,
        onDone: () => {
          this._isSpeaking = false;
        },
        onError: () => {
          this._isSpeaking = false;
        },
      });
    } catch (e) {
      this._isSpeaking = false;
      console.warn('Speech playback unavailable on this device:', e);
    }
  }

  /**
   * Reads IPM treatment recommendations aloud.
   */
  public static async speakTreatment(
    result: PredictionResponse,
    language: SupportedLanguage = 'en'
  ): Promise<void> {
    try {
      await Speech.stop();
      const langCode = this.getLanguageCode(language);
      let speechText = '';

      const rec = result.recommendation;
      if (!rec) return;

      if (language === 'kn') {
        speechText = `ಸಮಗ್ರ ಕೀಟ ನಿರ್ವಹಣೆ ಸಲಹೆಗಳು. ${rec.summary} `;
        if (rec.organic && rec.organic.length > 0) {
          speechText += `ಜೈವಿಕ ಕ್ರಮ: ${rec.organic[0].name}. `;
        }
        if (rec.chemical && rec.chemical.length > 0) {
          speechText += `ರಾಸಾಯನಿಕ ಕ್ರಮ: ${rec.chemical[0].name}. `;
        }
        if (rec.safety_notes && rec.safety_notes.length > 0) {
          speechText += `ಸುರಕ್ಷತಾ ಎಚ್ಚರಿಕೆ: ${rec.safety_notes[0]}`;
        }
      } else if (language === 'hi') {
        speechText = `समेकित कीट प्रबंधन सुझाव। ${rec.summary} `;
        if (rec.organic && rec.organic.length > 0) {
          speechText += `जैविक उपाय: ${rec.organic[0].name}। `;
        }
        if (rec.chemical && rec.chemical.length > 0) {
          speechText += `रासायनिक उपचार: ${rec.chemical[0].name}। `;
        }
        if (rec.safety_notes && rec.safety_notes.length > 0) {
          speechText += `सुरक्षा चेतावनी: ${rec.safety_notes[0]}`;
        }
      } else {
        speechText = `Integrated pest management advisory. ${rec.summary} `;
        if (rec.organic && rec.organic.length > 0) {
          speechText += `Organic priority: ${rec.organic[0].name}. `;
        }
        if (rec.chemical && rec.chemical.length > 0) {
          speechText += `Chemical intervention: ${rec.chemical[0].name}. `;
        }
        if (rec.safety_notes && rec.safety_notes.length > 0) {
          speechText += `Safety warning: ${rec.safety_notes[0]}`;
        }
      }

      this._isSpeaking = true;
      Speech.speak(speechText, {
        language: langCode,
        pitch: 1.0,
        rate: 0.92,
        onDone: () => {
          this._isSpeaking = false;
        },
        onError: () => {
          this._isSpeaking = false;
        },
      });
    } catch (e) {
      this._isSpeaking = false;
      console.warn('Speech playback unavailable on this device:', e);
    }
  }

  public static async stop(): Promise<void> {
    try {
      await Speech.stop();
    } catch (e) {
      // Ignored
    } finally {
      this._isSpeaking = false;
    }
  }

  public static isSpeaking(): boolean {
    return this._isSpeaking;
  }
}
