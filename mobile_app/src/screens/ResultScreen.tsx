import React, { useState } from 'react';
import {
  Image,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SpeechService } from '../services/speechService';
import { getTranslation } from '../translations';
import { PredictionResponse, SupportedLanguage } from '../types';

interface ResultScreenProps {
  route: { params: { result: PredictionResponse; imageUri: string } };
  navigation: any;
  language: SupportedLanguage;
}

export const ResultScreen: React.FC<ResultScreenProps> = ({ route, navigation, language }) => {
  const { result, imageUri } = route.params;
  const t = getTranslation(language);
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);
  const [showOverlay, setShowOverlay] = useState<boolean>(false);

  const handleToggleAudio = async () => {
    if (isPlayingAudio) {
      await SpeechService.stop();
      setIsPlayingAudio(false);
    } else {
      setIsPlayingAudio(true);
      await SpeechService.speakDiagnosis(result, language);
      setIsPlayingAudio(false);
    }
  };

  const getHealthScoreColor = (score: number) => {
    if (score >= 80) return '#2d6a4f';
    if (score >= 50) return '#e09f3e';
    return '#c1121f';
  };

  const isUnsupportedPart = result.status === 'unsupported_part_disease';
  const isHealthy = result.is_healthy;
  const confidencePct = Math.round(result.confidence * 100);

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Plant Image / Overlay Display */}
        <View style={styles.imageCard}>
          <Image
            source={{
              uri:
                showOverlay && result.lesion_analysis?.overlay_image_base64
                  ? `data:image/jpeg;base64,${result.lesion_analysis.overlay_image_base64}`
                  : imageUri,
            }}
            style={styles.mainImage}
          />
          {result.lesion_analysis?.overlay_image_base64 && (
            <TouchableOpacity
              style={styles.overlayToggle}
              onPress={() => setShowOverlay(!showOverlay)}
            >
              <Text style={styles.overlayToggleText}>
                {showOverlay ? 'Hide Lesions' : 'Show Lesion Overlay'}
              </Text>
            </TouchableOpacity>
          )}
        </View>

        {/* Stage 1 Anatomical Part Tag */}
        <View style={styles.partBadgeContainer}>
          <Text style={styles.partBadgeText}>
            🌱 {t.result.plantPart}: <Text style={{ fontWeight: '700' }}>{result.plant_part}</Text>
          </Text>
          {result.plant_part_confidence && (
            <Text style={styles.partConfidenceText}>
              ({Math.round(result.plant_part_confidence * 100)}% match)
            </Text>
          )}
        </View>

        {/* Diagnosis Header Card */}
        <View
          style={[
            styles.card,
            isUnsupportedPart
              ? styles.unsupportedCard
              : isHealthy
              ? styles.healthyCard
              : styles.diseaseCard,
          ]}
        >
          <Text style={styles.cropLabel}>
            {result.crop} • {isHealthy ? t.result.healthy : isUnsupportedPart ? t.result.unsupportedPart : t.result.diseased}
          </Text>
          <Text style={styles.diagnosisTitle}>{result.display_name}</Text>

          <View style={styles.metaRow}>
            <View style={styles.badge}>
              <Text style={styles.badgeText}>
                {t.result.confidence}: {confidencePct}%
              </Text>
            </View>
            <View
              style={[
                styles.healthScoreBadge,
                { backgroundColor: getHealthScoreColor(result.plant_health_score) },
              ]}
            >
              <Text style={styles.healthScoreText}>
                {t.result.healthScore}: {result.plant_health_score}/100
              </Text>
            </View>
          </View>
        </View>

        {/* Voice Playback Control */}
        <TouchableOpacity
          style={[styles.audioButton, isPlayingAudio && styles.audioButtonActive]}
          onPress={handleToggleAudio}
        >
          <Text style={styles.audioIcon}>{isPlayingAudio ? '⏹' : '🔊'}</Text>
          <Text style={styles.audioButtonText}>
            {isPlayingAudio ? t.result.stopAudio : t.result.listenAudio}
          </Text>
        </TouchableOpacity>

        {/* Lesion Severity Summary */}
        {result.lesion_analysis && result.lesion_analysis.lesion_detected && (
          <View style={styles.card}>
            <Text style={styles.cardHeader}>🔬 {t.result.severity}</Text>
            <View style={styles.statsRow}>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>
                  {result.lesion_analysis.affected_area_percentage.toFixed(1)}%
                </Text>
                <Text style={styles.statLabel}>Tissue Affected</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{result.lesion_analysis.lesion_count}</Text>
                <Text style={styles.statLabel}>Necrotic Spots</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statValue}>{result.lesion_analysis.severity_level}</Text>
                <Text style={styles.statLabel}>Visual Grade</Text>
              </View>
            </View>
          </View>
        )}

        {/* Bottom Actions */}
        <View style={styles.actionRow}>
          <TouchableOpacity
            style={styles.treatmentBtn}
            onPress={() => navigation.navigate('TreatmentScreen', { result })}
          >
            <Text style={styles.treatmentBtnText}>📋 {t.result.viewTreatments}</Text>
          </TouchableOpacity>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#f6f9f6',
  },
  scrollContent: {
    padding: 16,
    paddingBottom: 40,
  },
  imageCard: {
    width: '100%',
    height: 240,
    borderRadius: 16,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#000',
    marginBottom: 12,
  },
  mainImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  overlayToggle: {
    position: 'absolute',
    bottom: 12,
    right: 12,
    backgroundColor: 'rgba(0,0,0,0.75)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  overlayToggleText: {
    color: '#ffffff',
    fontSize: 12,
    fontWeight: '600',
  },
  partBadgeContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: '#e2ece4',
    paddingVertical: 8,
    paddingHorizontal: 14,
    borderRadius: 12,
    alignSelf: 'flex-start',
    marginBottom: 12,
  },
  partBadgeText: {
    color: '#2d4a34',
    fontSize: 13,
  },
  partConfidenceText: {
    color: '#55755e',
    fontSize: 12,
    marginLeft: 6,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 16,
    padding: 16,
    marginBottom: 14,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 6,
  },
  healthyCard: {
    borderLeftWidth: 6,
    borderLeftColor: '#2d6a4f',
  },
  diseaseCard: {
    borderLeftWidth: 6,
    borderLeftColor: '#c1121f',
  },
  unsupportedCard: {
    borderLeftWidth: 6,
    borderLeftColor: '#e09f3e',
  },
  cropLabel: {
    fontSize: 13,
    color: '#6c757d',
    fontWeight: '600',
    textTransform: 'uppercase',
    letterSpacing: 0.5,
  },
  diagnosisTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1a202c',
    marginVertical: 6,
  },
  metaRow: {
    flexDirection: 'row',
    gap: 10,
    marginTop: 8,
  },
  badge: {
    backgroundColor: '#e9ecef',
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  badgeText: {
    fontSize: 12,
    fontWeight: '600',
    color: '#495057',
  },
  healthScoreBadge: {
    paddingVertical: 6,
    paddingHorizontal: 10,
    borderRadius: 8,
  },
  healthScoreText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#ffffff',
  },
  audioButton: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    backgroundColor: '#d8f3dc',
    paddingVertical: 14,
    borderRadius: 12,
    marginBottom: 14,
    borderWidth: 1,
    borderColor: '#95d5b2',
  },
  audioButtonActive: {
    backgroundColor: '#ffccd5',
    borderColor: '#ff758f',
  },
  audioIcon: {
    fontSize: 18,
    marginRight: 8,
  },
  audioButtonText: {
    color: '#1b4332',
    fontSize: 15,
    fontWeight: '600',
  },
  cardHeader: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d4a34',
    marginBottom: 12,
  },
  statsRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
  },
  statBox: {
    alignItems: 'center',
    flex: 1,
  },
  statValue: {
    fontSize: 18,
    fontWeight: '700',
    color: '#1b4332',
  },
  statLabel: {
    fontSize: 11,
    color: '#6c757d',
    marginTop: 2,
  },
  actionRow: {
    marginTop: 6,
  },
  treatmentBtn: {
    backgroundColor: '#1b4332',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
  },
  treatmentBtnText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
});
