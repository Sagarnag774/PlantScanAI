export type PredictionStatus =
  | 'success'
  | 'uncertain'
  | 'unknown'
  | 'invalid_image'
  | 'unsupported_crop'
  | 'unsupported_part_disease'
  | 'error';

export interface TreatmentItem {
  name: string;
  method?: string;
  application?: string;
  frequency?: string;
  active_ingredient?: string;
  dosage?: string;
  safety_precautions?: string;
  caution_level?: 'None' | 'Low' | 'Moderate' | 'High' | string;
}

export interface RecommendationResponse {
  summary: string;
  organic: TreatmentItem[];
  chemical: TreatmentItem[];
  prevention: string[];
  safety_notes: string[];
  photo_guidance?: string[];
  disclaimer: string;
  sources: string[];
}

export interface LesionAnalysis {
  lesion_detected: boolean;
  lesion_count: number;
  affected_area_percentage: number;
  leaf_area_pixels: number;
  lesion_area_pixels: number;
  severity_level: string;
  bounding_boxes: Array<{ x: number; y: number; width: number; height: number }>;
  overlay_image_base64?: string;
  mask_image_base64?: string;
  method_note: string;
}

export interface PredictionResponse {
  status: PredictionStatus;
  crop: string;
  predicted_class: string;
  display_name: string;
  confidence: number;
  is_healthy: boolean;
  plant_part: string;
  plant_part_confidence?: number;
  plant_part_probabilities?: Record<string, number>;
  plant_health_score: number;
  recommendation?: RecommendationResponse;
  lesion_analysis?: LesionAnalysis;
  model_version: string;
  inference_time_ms: number;
  crop_detected_automatically?: boolean;
  crop_confidence?: number;
  candidate_crops?: Array<{ crop: string; confidence: number }>;
  message?: string;
}

export type SupportedLanguage = 'en' | 'kn' | 'hi';

export type RootStackParamList = {
  MainTabs: undefined;
  ResultScreen: { result: PredictionResponse; imageUri: string };
  TreatmentScreen: { result: PredictionResponse };
};
