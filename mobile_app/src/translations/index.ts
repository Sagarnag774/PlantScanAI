import { SupportedLanguage } from '../types';

export interface TranslationDictionary {
  appName: string;
  tagline: string;
  tabs: {
    scan: string;
    results: string;
    settings: string;
  };
  scan: {
    title: string;
    instruction: string;
    cropHint: string;
    partHint: string;
    autoDetect: string;
    takePhoto: string;
    chooseGallery: string;
    retake: string;
    diagnose: string;
    analyzing: string;
    analyzingStage1: string;
    analyzingStage2: string;
    offlineTitle: string;
    offlineMessage: string;
    timeoutMessage: string;
    networkErrorMessage: string;
  };
  result: {
    title: string;
    plantPart: string;
    diagnosis: string;
    confidence: string;
    healthScore: string;
    healthy: string;
    diseased: string;
    uncertain: string;
    unsupportedPart: string;
    severity: string;
    lesionsDetected: string;
    listenAudio: string;
    stopAudio: string;
    viewTreatments: string;
    newScan: string;
  };
  treatment: {
    title: string;
    advisorySummary: string;
    priority1Organic: string;
    priority2Chemical: string;
    priority3Prevention: string;
    safetyWarning: string;
    stemBarkWarning: string;
    disclaimer: string;
    dosage: string;
    application: string;
    frequency: string;
    caution: string;
    listenGuidance: string;
  };
  settings: {
    title: string;
    language: string;
    serverUrl: string;
    testConnection: string;
    connectionSuccess: string;
    connectionFailed: string;
    about: string;
    version: string;
  };
}

export const translations: Record<SupportedLanguage, TranslationDictionary> = {
  en: {
    appName: 'PlantScan AI',
    tagline: 'Two-Stage Intelligent Crop Pathology & IPM Advisory',
    tabs: {
      scan: 'Scan',
      results: 'Diagnostics',
      settings: 'Settings',
    },
    scan: {
      title: 'Crop Disease Scanner',
      instruction: 'Take a clear photograph of the affected plant leaf, fruit, stem, or bark in natural light.',
      cropHint: 'Target Crop Species',
      partHint: 'Plant Anatomical Part',
      autoDetect: 'Auto-Detect',
      takePhoto: 'Camera Capture',
      chooseGallery: 'Choose from Gallery',
      retake: 'Retake Photo',
      diagnose: 'Run Two-Stage Diagnosis',
      analyzing: 'Analyzing crop sample...',
      analyzingStage1: 'Stage 1: Identifying plant anatomical part...',
      analyzingStage2: 'Stage 2: Classifying disease pathology...',
      offlineTitle: 'Offline Mode',
      offlineMessage: 'No internet connection detected. Please connect to a mobile network or Wi-Fi to run diagnosis.',
      timeoutMessage: 'Server request timed out after 20 seconds. Please check server status and retry.',
      networkErrorMessage: 'Could not connect to PlantScan AI server. Check the configured Server URL in Settings.',
    },
    result: {
      title: 'Diagnostic Report',
      plantPart: 'Plant Tissue',
      diagnosis: 'Identified Condition',
      confidence: 'Confidence',
      healthScore: 'Plant Health Score',
      healthy: 'Healthy Crop Tissue',
      diseased: 'Pathology Detected',
      uncertain: 'Uncertain Diagnosis',
      unsupportedPart: 'Unsupported Plant Part Pathology',
      severity: 'Lesion Severity',
      lesionsDetected: 'Necrotic Lesions Measured',
      listenAudio: 'Listen to Diagnosis',
      stopAudio: 'Stop Voice Playback',
      viewTreatments: 'View IPM Treatment Plan',
      newScan: 'Scan Another Plant',
    },
    treatment: {
      title: 'Integrated Pest Management',
      advisorySummary: 'Advisory Summary',
      priority1Organic: 'Priority 1: Organic & Biological Measures',
      priority2Chemical: 'Priority 2: Chemical Interventions',
      priority3Prevention: 'Priority 3: Cultural & Field Prevention',
      safetyWarning: 'Safety & Environmental Caution',
      stemBarkWarning: 'CRITICAL SAFETY NOTICE: Do not apply chemical fungicides/pesticides to stems or bark without laboratory diagnostic verification.',
      disclaimer: 'Agricultural Disclaimer',
      dosage: 'Dosage',
      application: 'Application Method',
      frequency: 'Frequency',
      caution: 'Caution Level',
      listenGuidance: 'Read Recommendations Aloud',
    },
    settings: {
      title: 'Settings & Connectivity',
      language: 'Select Language',
      serverUrl: 'Backend API URL',
      testConnection: 'Test Server Connection',
      connectionSuccess: 'Connection Successful! Inference engine is ready.',
      connectionFailed: 'Failed to reach backend server. Please verify IP and port.',
      about: 'About PlantScan AI',
      version: 'Version 1.0.0 (Phase 1 Compliant)',
    },
  },
  kn: {
    appName: 'ಪ್ಲಾಂಟ್‌ಸ್ಕ್ಯಾನ್ ಎಐ',
    tagline: 'ಎರಡು-ಹಂತದ ಬುದ್ಧಿವಂತ ಬೆಳೆ ರೋಗನಿರ್ಣಯ ಮತ್ತು ಸಮಗ್ರ ಕೀಟ ನಿರ್ವಹಣೆ',
    tabs: {
      scan: 'ಸ್ಕ್ಯಾನ್',
      results: 'ರೋಗನಿರ್ಣಯ',
      settings: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು',
    },
    scan: {
      title: 'ಬೆಳೆ ರೋಗ ಸ್ಕ್ಯಾನರ್',
      instruction: 'ನೈಸರ್ಗಿಕ ಬೆಳಕಿನಲ್ಲಿ ಬಾಧಿತ ಸಸ್ಯದ ಎಲೆ, ಹಣ್ಣು ಅಥವಾ ಕಾಂಡದ ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
      cropHint: 'ಬೆಳೆ ಪ್ರಕಾರ',
      partHint: 'ಸಸ್ಯದ ಅಂಗಾಂಗ',
      autoDetect: 'ಸ್ವಯಂಚಾಲಿತ ಪತ್ತೆ',
      takePhoto: 'ಕ್ಯಾಮೆರಾ ಮೂಲಕ ಫೋಟೋ ತೆಗೆಯಿರಿ',
      chooseGallery: 'ಗ್ಯಾಲರಿಯಿಂದ ಆಯ್ಕೆಮಾಡಿ',
      retake: 'ಮತ್ತೆ ಫೋಟೋ ತೆಗೆಯಿರಿ',
      diagnose: 'ರೋಗನಿರ್ಣಯ ಪ್ರಾರಂಭಿಸಿ',
      analyzing: 'ಮಾದರಿಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...',
      analyzingStage1: 'ಹಂತ 1: ಸಸ್ಯದ ಅಂಗಾಂಗವನ್ನು ಗುರುತಿಸಲಾಗುತ್ತಿದೆ...',
      analyzingStage2: 'ಹಂತ 2: ರೋಗವನ್ನು ವರ್ಗೀಕರಿಸಲಾಗುತ್ತಿದೆ...',
      offlineTitle: 'ಆಫ್‌ಲೈನ್ ಮೋಡ್',
      offlineMessage: 'ಇಂಟರ್ನೆಟ್ ಸಂಪರ್ಕವಿಲ್ಲ. ದಯವಿಟ್ಟು ನೆಟ್‌ವರ್ಕ್ ಸಂಪರ್ಕ ಪರಿಶೀಲಿಸಿ.',
      timeoutMessage: 'ಸರ್ವರ್ ವಿನಂತಿ ಸಮಯ ಮೀರಿದೆ (20 ಸೆಕೆಂಡುಗಳು). ದಯವಿಟ್ಟು ಪುನಃ ಪ್ರಯತ್ನಿಸಿ.',
      networkErrorMessage: 'ಪ್ಲಾಂಟ್‌ಸ್ಕ್ಯಾನ್ ಸರ್ವರ್ ಸಂಪರ್ಕಿಸಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ.',
    },
    result: {
      title: 'ರೋಗನಿರ್ಣಯ ವರದಿ',
      plantPart: 'ಸಸ್ಯದ ಅಂಗಾಂಗ',
      diagnosis: 'ಗುರುತಿಸಲಾದ ಸ್ಥಿತಿ',
      confidence: 'ವಿಶ್ವಾಸಾರ್ಹತೆ',
      healthScore: 'ಸಸ್ಯ ಆರೋಗ್ಯ ಸ್ಕೋರ್',
      healthy: 'ಆರೋಗ್ಯಕರ ಸಸ್ಯ',
      diseased: 'ರೋಗ ಪತ್ತೆಯಾಗಿದೆ',
      uncertain: 'ಅನಿಶ್ಚಿತ ರೋಗನಿರ್ಣಯ',
      unsupportedPart: 'ಬೆಂಬಲವಿಲ್ಲದ ಸಸ್ಯ ಅಂಗಾಂಗ ರೋಗ',
      severity: 'ಹಾನಿಯ ತೀವ್ರತೆ',
      lesionsDetected: 'ನೆಕ್ರೋಟಿಕ್ ಗಾಯಗಳು ಪತ್ತೆಯಾಗಿವೆ',
      listenAudio: 'ವರದಿಯನ್ನು ಆಲಿಸಿ',
      stopAudio: 'ಧ್ವನಿ ನಿಲ್ಲಿಸಿ',
      viewTreatments: 'ಚಿಕಿತ್ಸಾ ಕ್ರಮಗಳನ್ನು ವೀಕ್ಷಿಸಿ',
      newScan: 'ಮತ್ತೊಂದು ಸ್ಕ್ಯಾನ್ ಮಾಡಿ',
    },
    treatment: {
      title: 'ಸಮಗ್ರ ಕೀಟ ನಿರ್ವಹಣೆ (IPM)',
      advisorySummary: 'ಸಲಹಾ ಸಾರಾಂಶ',
      priority1Organic: 'ಆದ್ಯತೆ 1: ಜೈವಿಕ ಮತ್ತು ಸಾವಯವ ಪರಿಹಾರಗಳು',
      priority2Chemical: 'ಆದ್ಯತೆ 2: ರಾಸಾಯನಿಕ ಕ್ರಮಗಳು',
      priority3Prevention: 'ಆದ್ಯತೆ 3: ಕೃಷಿ ಮತ್ತು ತಡೆಗಟ್ಟುವ ಕ್ರಮಗಳು',
      safetyWarning: 'ಸುರಕ್ಷತೆ ಮತ್ತು ಪರಿಸರ ಎಚ್ಚರಿಕೆ',
      stemBarkWarning: 'ಗಂಭೀರ ಎಚ್ಚರಿಕೆ: ಕಾಂಡ ಅಥವಾ ತೊಗಟೆಗೆ ಪ್ರಯೋಗಾಲಯ ದೃಢೀಕರಣವಿಲ್ಲದೆ ರಾಸಾಯನಿಕ ಕೀಟನಾಶಕಗಳನ್ನು ಸಿಂಪಡಿಸಬೇಡಿ.',
      disclaimer: 'ಕೃಷಿ ಹಕ್ಕುತ್ಯಾಗ',
      dosage: 'ಪ್ರಮಾಣ',
      application: 'ಬಳಕೆಯ ವಿಧಾನ',
      frequency: 'ಆವರ್ತನ',
      caution: 'ಎಚ್ಚರಿಕೆಯ ಮಟ್ಟ',
      listenGuidance: 'ಚಿಕಿತ್ಸಾ ಸಲಹೆಗಳನ್ನು ಆಲಿಸಿ',
    },
    settings: {
      title: 'ಸೆಟ್ಟಿಂಗ್‌ಗಳು ಮತ್ತು ಸಂಪರ್ಕ',
      language: 'ಭಾಷೆ ಆಯ್ಕೆಮಾಡಿ',
      serverUrl: 'ಬ್ಯಾಕೆಂಡ್ ಸರ್ವರ್ URL',
      testConnection: 'ಸರ್ವರ್ ಸಂಪರ್ಕ ಪರೀಕ್ಷಿಸಿ',
      connectionSuccess: 'ಸಂಪರ್ಕ ಯಶಸ್ವಿಯಾಗಿದೆ! AI ಎಂಜಿನ್ ಸಿದ್ಧವಾಗಿದೆ.',
      connectionFailed: 'ಸರ್ವರ್ ತಲುಪಲು ಸಾಧ್ಯವಾಗಲಿಲ್ಲ. IP ಮತ್ತು ಪೋರ್ಟ್ ಪರಿಶೀಲಿಸಿ.',
      about: 'ಪ್ಲಾಂಟ್‌ಸ್ಕ್ಯಾನ್ ಎಐ ಕುರಿತು',
      version: 'ಆವೃತ್ತಿ 1.0.0 (ಹಂತ 1 ಪ್ರಮಾಣೀಕೃತ)',
    },
  },
  hi: {
    appName: 'प्लांटस्कैन एआई',
    tagline: 'द्वि-चरणीय बुद्धिमान फसल रोग निदान एवं समेकित कीट प्रबंधन',
    tabs: {
      scan: 'स्कैन',
      results: 'निदान',
      settings: 'सेटिंग्स',
    },
    scan: {
      title: 'फसल रोग स्कैनर',
      instruction: 'प्राकृतिक प्रकाश में प्रभावित पत्ती, फल, तने या छाल की स्पष्ट तस्वीर लें।',
      cropHint: 'लक्षित फसल',
      partHint: 'पौधे का अंग',
      autoDetect: 'स्वचालित पहचान',
      takePhoto: 'कैमरा से फोटो लें',
      chooseGallery: 'गैलरी से चुनें',
      retake: 'दोबारा फोटो लें',
      diagnose: 'रोग निदान शुरू करें',
      analyzing: 'नमूने का विश्लेषण किया जा रहा है...',
      analyzingStage1: 'चरण 1: पौधे के अंग की पहचान...',
      analyzingStage2: 'चरण 2: रोग का वर्गीकरण...',
      offlineTitle: 'ऑफ़लाइन मोड',
      offlineMessage: 'इंटरनेट कनेक्शन नहीं मिला। कृपया इंटरनेट कनेक्शन की जांच करें।',
      timeoutMessage: 'सर्वर अनुरोध का समय समाप्त (20 सेकंड)। कृपया पुनः प्रयास करें।',
      networkErrorMessage: 'प्लांटस्कैन सर्वर से कनेक्ट नहीं हो सका। सेटिंग्स में सर्वर URL जांचें।',
    },
    result: {
      title: 'रोग निदान रिपोर्ट',
      plantPart: 'पौधे का अंग',
      diagnosis: 'पहचानी गई स्थिति',
      confidence: 'सटीकता विश्वास',
      healthScore: 'पौधा स्वास्थ्य स्कोर',
      healthy: 'स्वस्थ फसल ऊतक',
      diseased: 'रोग के लक्षण मिले',
      uncertain: 'अनिश्चित निदान',
      unsupportedPart: 'इस पौधे के अंग का रोग समर्थित नहीं है',
      severity: 'लक्षणों की गंभीरता',
      lesionsDetected: 'नेक्रोटिक घाव मापे गए',
      listenAudio: 'निदान रिपोर्ट सुनें',
      stopAudio: 'आवाज बंद करें',
      viewTreatments: 'उपचार योजना देखें',
      newScan: 'नया पौधा स्कैन करें',
    },
    treatment: {
      title: 'समेकित कीट प्रबंधन (IPM)',
      advisorySummary: 'सलाह सारांश',
      priority1Organic: 'प्राथमिकता 1: जैविक और प्राकृतिक उपाय',
      priority2Chemical: 'प्राथमिकता 2: रासायनिक उपचार',
      priority3Prevention: 'प्राथमिकता 3: रोकथाम और सुरक्षा उपाय',
      safetyWarning: 'सुरक्षा एवं पर्यावरणीय चेतावनी',
      stemBarkWarning: 'महत्वपूर्ण चेतावनी: प्रयोगशाला पुष्टि के बिना तने या छाल पर रासायनिक कीटनाशक का छिड़काव न करें।',
      disclaimer: 'कृषि अस्वीकरण',
      dosage: 'मात्रा',
      application: 'प्रयोग विधि',
      frequency: 'आवृति',
      caution: 'सावधानी स्तर',
      listenGuidance: 'उपचार सलाह सुनें',
    },
    settings: {
      title: 'सेटिंग्स और कनेक्टिविटी',
      language: 'भाषा चुनें',
      serverUrl: 'बैकएंड एपीआई URL',
      testConnection: 'सर्वर कनेक्शन जांचें',
      connectionSuccess: 'कनेक्शन सफल! एआई मॉडल तैयार है।',
      connectionFailed: 'सर्वर से संपर्क नहीं हो सका। IP और पोर्ट जांचें।',
      about: 'प्लांटस्कैन एआई के बारे में',
      version: 'संस्करण 1.0.0 (चरण 1 अनुपालन)',
    },
  },
};

export const getTranslation = (lang: SupportedLanguage): TranslationDictionary => {
  return translations[lang] || translations.en;
};
