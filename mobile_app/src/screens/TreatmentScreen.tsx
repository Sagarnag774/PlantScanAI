import React, { useState } from 'react';
import {
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import { SpeechService } from '../services/speechService';
import { getTranslation } from '../translations';
import { PredictionResponse, SupportedLanguage, TreatmentItem } from '../types';

interface TreatmentScreenProps {
  route: { params: { result: PredictionResponse } };
  language: SupportedLanguage;
}

export const TreatmentScreen: React.FC<TreatmentScreenProps> = ({ route, language }) => {
  const { result } = route.params;
  const t = getTranslation(language);
  const rec = result.recommendation;
  const [isPlayingAudio, setIsPlayingAudio] = useState<boolean>(false);

  const handleToggleAudio = async () => {
    if (isPlayingAudio) {
      await SpeechService.stop();
      setIsPlayingAudio(false);
    } else {
      setIsPlayingAudio(true);
      await SpeechService.speakTreatment(result, language);
      setIsPlayingAudio(false);
    }
  };

  const isUnsupportedPart = result.status === 'unsupported_part_disease';

  const renderTreatmentItem = (item: TreatmentItem, isChemical: boolean = false) => (
    <View key={item.name} style={styles.itemCard}>
      <View style={styles.itemHeaderRow}>
        <Text style={styles.itemName}>{item.name}</Text>
        {item.caution_level && (
          <View
            style={[
              styles.cautionBadge,
              item.caution_level === 'High'
                ? styles.cautionHigh
                : item.caution_level === 'Moderate'
                ? styles.cautionModerate
                : styles.cautionLow,
            ]}
          >
            <Text style={styles.cautionText}>{item.caution_level}</Text>
          </View>
        )}
      </View>
      {item.active_ingredient && (
        <Text style={styles.itemMeta}>Active Ingredient: {item.active_ingredient}</Text>
      )}
      {item.dosage && <Text style={styles.itemMeta}>Dilution/Dosage: {item.dosage}</Text>}
      {item.method && <Text style={styles.itemDetail}>{item.method}</Text>}
      {item.safety_precautions && (
        <View style={styles.safetyBox}>
          <Text style={styles.safetyText}>⚠️ PPE: {item.safety_precautions}</Text>
        </View>
      )}
    </View>
  );

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        {/* Title Header */}
        <View style={styles.header}>
          <Text style={styles.title}>{t.treatment.title}</Text>
          <Text style={styles.targetCrop}>
            {result.crop} • {result.display_name}
          </Text>
        </View>

        {/* Voice Playback Button */}
        <TouchableOpacity
          style={[styles.audioButton, isPlayingAudio && styles.audioButtonActive]}
          onPress={handleToggleAudio}
        >
          <Text style={styles.audioIcon}>{isPlayingAudio ? '⏹' : '🔊'}</Text>
          <Text style={styles.audioButtonText}>
            {isPlayingAudio ? t.result.stopAudio : t.treatment.listenGuidance}
          </Text>
        </TouchableOpacity>

        {/* High-level Advisory Summary */}
        {rec?.summary && (
          <View style={styles.summaryCard}>
            <Text style={styles.summaryTitle}>📋 {t.treatment.advisorySummary}</Text>
            <Text style={styles.summaryBody}>{rec.summary}</Text>
          </View>
        )}

        {/* Stem & Bark / Unsupported Plant Part Safety Warning */}
        {isUnsupportedPart && (
          <View style={styles.dangerAlertCard}>
            <Text style={styles.dangerTitle}>🛑 {t.treatment.safetyWarning}</Text>
            <Text style={styles.dangerBody}>{t.treatment.stemBarkWarning}</Text>
          </View>
        )}

        {/* Priority 1: Organic & Biological Measures */}
        {rec?.organic && rec.organic.length > 0 && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>🌿 {t.treatment.priority1Organic}</Text>
            {rec.organic.map((item) => renderTreatmentItem(item, false))}
          </View>
        )}

        {/* Priority 2: Chemical Interventions */}
        {rec?.chemical && rec.chemical.length > 0 && !isUnsupportedPart && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>🧪 {t.treatment.priority2Chemical}</Text>
            {rec.chemical.map((item) => renderTreatmentItem(item, true))}
          </View>
        )}

        {/* Priority 3: Cultural & Field Prevention */}
        {rec?.prevention && rec.prevention.length > 0 && (
          <View style={styles.sectionContainer}>
            <Text style={styles.sectionTitle}>🛡️ {t.treatment.priority3Prevention}</Text>
            {rec.prevention.map((tip, idx) => (
              <View key={idx} style={styles.bulletRow}>
                <Text style={styles.bulletPoint}>•</Text>
                <Text style={styles.bulletText}>{tip}</Text>
              </View>
            ))}
          </View>
        )}

        {/* Safety Notes */}
        {rec?.safety_notes && rec.safety_notes.length > 0 && (
          <View style={styles.safetyNotesCard}>
            <Text style={styles.safetyNotesTitle}>⚠️ {t.treatment.safetyWarning}</Text>
            {rec.safety_notes.map((note, idx) => (
              <Text key={idx} style={styles.safetyNoteText}>
                {note}
              </Text>
            ))}
          </View>
        )}

        {/* Disclaimer */}
        {rec?.disclaimer && (
          <View style={styles.disclaimerCard}>
            <Text style={styles.disclaimerTitle}>📜 {t.treatment.disclaimer}</Text>
            <Text style={styles.disclaimerText}>{rec.disclaimer}</Text>
          </View>
        )}
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
  header: {
    marginBottom: 14,
  },
  title: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1a4329',
  },
  targetCrop: {
    fontSize: 14,
    color: '#4f6b56',
    fontWeight: '600',
    marginTop: 4,
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
  summaryCard: {
    backgroundColor: '#eaf4ee',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#2d6a4f',
  },
  summaryTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#1b4332',
    marginBottom: 4,
  },
  summaryBody: {
    fontSize: 13,
    color: '#2d4a34',
    lineHeight: 19,
  },
  dangerAlertCard: {
    backgroundColor: '#fde8e8',
    borderRadius: 14,
    padding: 14,
    marginBottom: 16,
    borderLeftWidth: 4,
    borderLeftColor: '#c1121f',
  },
  dangerTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#9b1c1c',
    marginBottom: 4,
  },
  dangerBody: {
    fontSize: 13,
    color: '#771d1d',
    lineHeight: 18,
  },
  sectionContainer: {
    marginBottom: 16,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#1a4329',
    marginBottom: 10,
  },
  itemCard: {
    backgroundColor: '#ffffff',
    borderRadius: 12,
    padding: 14,
    marginBottom: 10,
    elevation: 1,
    shadowColor: '#000',
    shadowOpacity: 0.04,
    shadowRadius: 4,
  },
  itemHeaderRow: {
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
    marginBottom: 6,
  },
  itemName: {
    fontSize: 15,
    fontWeight: '700',
    color: '#2d4a34',
    flex: 1,
  },
  cautionBadge: {
    paddingVertical: 3,
    paddingHorizontal: 8,
    borderRadius: 6,
  },
  cautionLow: {
    backgroundColor: '#d8f3dc',
  },
  cautionModerate: {
    backgroundColor: '#ffedd5',
  },
  cautionHigh: {
    backgroundColor: '#fee2e2',
  },
  cautionText: {
    fontSize: 10,
    fontWeight: '700',
    color: '#333',
  },
  itemMeta: {
    fontSize: 12,
    color: '#55755e',
    fontWeight: '600',
    marginBottom: 4,
  },
  itemDetail: {
    fontSize: 13,
    color: '#495057',
    lineHeight: 18,
    marginTop: 2,
  },
  safetyBox: {
    backgroundColor: '#fffbeb',
    padding: 8,
    borderRadius: 6,
    marginTop: 8,
  },
  safetyText: {
    fontSize: 12,
    color: '#92400e',
  },
  bulletRow: {
    flexDirection: 'row',
    alignItems: 'flex-start',
    marginBottom: 8,
  },
  bulletPoint: {
    fontSize: 18,
    color: '#2d6a4f',
    marginRight: 8,
    lineHeight: 20,
  },
  bulletText: {
    fontSize: 13,
    color: '#344e41',
    flex: 1,
    lineHeight: 19,
  },
  safetyNotesCard: {
    backgroundColor: '#fef3c7',
    borderRadius: 12,
    padding: 14,
    marginBottom: 16,
  },
  safetyNotesTitle: {
    fontSize: 14,
    fontWeight: '700',
    color: '#78350f',
    marginBottom: 6,
  },
  safetyNoteText: {
    fontSize: 12,
    color: '#92400e',
    lineHeight: 18,
    marginBottom: 4,
  },
  disclaimerCard: {
    backgroundColor: '#edf2f7',
    borderRadius: 12,
    padding: 12,
    marginTop: 6,
  },
  disclaimerTitle: {
    fontSize: 12,
    fontWeight: '700',
    color: '#4a5568',
    marginBottom: 4,
  },
  disclaimerText: {
    fontSize: 11,
    color: '#718096',
    lineHeight: 16,
  },
});
