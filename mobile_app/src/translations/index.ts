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
    nonPlantTitle: string;
    nonPlantMessage: string;
    blurryTitle: string;
    blurryMessage: string;
    ambiguousTitle: string;
    ambiguousMessage: string;
    lowQualityTitle: string;
    lowQualityMessage: string;
    tryAnotherPhoto: string;
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
      nonPlantTitle: 'Not a Plant',
      nonPlantMessage: 'This image does not appear to be a plant. Please upload a clear photo of a plant leaf or supported plant part.',
      blurryTitle: 'Blurry Image',
      blurryMessage: 'The uploaded image is too blurry. Please hold your camera steady and upload a sharp, well-focused photo.',
      ambiguousTitle: 'Ambiguous Image',
      ambiguousMessage: 'Plant presence cannot be reliably determined. Please upload a clearer photo of a plant leaf or fruit.',
      lowQualityTitle: 'Low Quality Image',
      lowQualityMessage: 'The uploaded image is too dark or washed out. Please take a photo in good natural lighting.',
      tryAnotherPhoto: 'Upload Another Photo',
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
      nonPlantTitle: 'ಸಸ್ಯವಲ್ಲದ ಚಿತ್ರ',
      nonPlantMessage: 'ಈ ಚಿತ್ರವು ಸಸ್ಯವನ್ನು ಹೊಂದಿಲ್ಲ. ದಯವಿಟ್ಟು ಸಸ್ಯದ ಎಲೆ ಅಥವಾ ಬೆಂಬಲಿತ ಭಾಗದ ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.',
      blurryTitle: 'ಅಸ್ಪಷ್ಟ ಚಿತ್ರ',
      blurryMessage: 'ಅಪ್‌ಲೋಡ್ ಮಾಡಿದ ಚಿತ್ರವು ತುಂಬಾ ಅಸ್ಪಷ್ಟವಾಗಿದೆ. ದಯವಿಟ್ಟು ಕ್ಯಾಮರಾವನ್ನು ಸ್ಥಿರವಾಗಿಟ್ಟು ಸ್ಪಷ್ಟ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
      ambiguousTitle: 'ಅನಿಶ್ಚಿತ ಚಿತ್ರ',
      ambiguousMessage: 'ಸಸ್ಯದ ಉಪಸ್ಥಿತಿಯನ್ನು ವಿಶ್ವಾಸಾರ್ಹವಾಗಿ ನಿರ್ಧರಿಸಲಾಗುತ್ತಿಲ್ಲ. ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟ ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ.',
      lowQualityTitle: 'ಕಡಿಮೆ ಗುಣಮಟ್ಟದ ಚಿತ್ರ',
      lowQualityMessage: 'ಚಿತ್ರವು ತುಂಬಾ ಕತ್ತಲೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಉತ್ತಮ ಬೆಳಕಿನಲ್ಲಿ ಫೋಟೋ ತೆಗೆದುಕೊಳ್ಳಿ.',
      tryAnotherPhoto: 'ಮತ್ತೊಂದು ಫೋಟೋ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ',
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
      nonPlantTitle: 'पौधा नहीं है',
      nonPlantMessage: 'यह चित्र किसी पौधे का नहीं लगता। कृपया पौधे की पत्ती या समर्थित अंग की स्पष्ट तस्वीर अपलोड करें।',
      blurryTitle: 'धुंधली तस्वीर',
      blurryMessage: 'अपलोड की गई तस्वीर बहुत धुंधली है। कृपया कैमरे को स्थिर रखें और साफ फोटो लें।',
      ambiguousTitle: 'अस्पष्ट छवि',
      ambiguousMessage: 'पौधे की उपस्थिति स्पष्ट रूप से निर्धारित नहीं की जा सकती। कृपया पौधे की स्पष्ट तस्वीर अपलोड करें।',
      lowQualityTitle: 'कम गुणवत्ता वाली छवि',
      lowQualityMessage: 'तस्वीर बहुत अंधेरी या धुंधली है। कृपया अच्छी प्राकृतिक रोशनी में फोटो लें।',
      tryAnotherPhoto: 'दूसरी फोटो अपलोड करें',
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
