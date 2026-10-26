import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  Image,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TouchableOpacity,
  View,
} from 'react-native';
import * as ImagePicker from 'expo-image-picker';
import { ApiService, ApiError } from '../services/apiService';
import { getTranslation } from '../translations';
import { SupportedLanguage } from '../types';

interface ScanScreenProps {
  navigation: any;
  language: SupportedLanguage;
}

const SUPPORTED_CROPS = [
  'Auto-Detect',
  'Tomato',
  'Potato',
  'Rice',
  'Maize',
  'Apple',
  'Grape',
  'Mango',
  'Banana',
  'Cotton',
  'Bell pepper',
];

const PLANT_PARTS = ['Auto-Detect', 'Leaf', 'Stem', 'Fruit', 'Bark'];

export const ScanScreen: React.FC<ScanScreenProps> = ({ navigation, language }) => {
  const t = getTranslation(language);
  const [selectedImage, setSelectedImage] = useState<string | null>(null);
  const [selectedCrop, setSelectedCrop] = useState<string>('Auto-Detect');
  const [selectedPart, setSelectedPart] = useState<string>('Auto-Detect');
  const [loading, setLoading] = useState<boolean>(false);
  const [stageProgress, setStageProgress] = useState<string>('');

  const handlePickImage = async () => {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Camera roll permissions are needed to select photos.');
      return;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const handleTakePhoto = async () => {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Camera permissions are required to take crop photos.');
      return;
    }

    const result = await ImagePicker.launchCameraAsync({
      allowsEditing: true,
      aspect: [1, 1],
      quality: 0.85,
    });

    if (!result.canceled && result.assets && result.assets.length > 0) {
      setSelectedImage(result.assets[0].uri);
    }
  };

  const handleDiagnose = async () => {
    if (!selectedImage) return;

    setLoading(true);
    setStageProgress(t.scan.analyzingStage1);

    try {
      const response = await ApiService.predictImage(
        selectedImage,
        selectedCrop === 'Auto-Detect' ? undefined : selectedCrop,
        selectedPart === 'Auto-Detect' ? undefined : selectedPart,
        language
      );
      setLoading(false);
      navigation.navigate('ResultScreen', { result: response, imageUri: selectedImage });
    } catch (err: any) {
      setLoading(false);
      const message =
        err instanceof ApiError && err.code === 'TIMEOUT'
          ? t.scan.timeoutMessage
          : t.scan.networkErrorMessage;
      Alert.alert('Diagnosis Error', message);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.header}>
          <Text style={styles.title}>{t.scan.title}</Text>
          <Text style={styles.subtitle}>{t.scan.instruction}</Text>
        </View>

        {/* Crop Selection Section */}
        <Text style={styles.sectionLabel}>{t.scan.cropHint}</Text>
        <ScrollView horizontal showsHorizontalScrollIndicator={false} style={styles.pillScroll}>
          {SUPPORTED_CROPS.map((crop) => (
            <TouchableOpacity
              key={crop}
              style={[styles.pill, selectedCrop === crop && styles.pillActive]}
              onPress={() => setSelectedCrop(crop)}
            >
              <Text style={[styles.pillText, selectedCrop === crop && styles.pillTextActive]}>
                {crop}
              </Text>
            </TouchableOpacity>
          ))}
        </ScrollView>

        {/* Plant Part Selection Section */}
        <Text style={styles.sectionLabel}>{t.scan.partHint}</Text>
        <View style={styles.partRow}>
          {PLANT_PARTS.map((part) => (
            <TouchableOpacity
              key={part}
              style={[styles.partButton, selectedPart === part && styles.partButtonActive]}
              onPress={() => setSelectedPart(part)}
            >
              <Text style={[styles.partText, selectedPart === part && styles.partTextActive]}>
                {part}
              </Text>
            </TouchableOpacity>
          ))}
        </View>

        {/* Image Preview or Capture Placeholder */}
        <View style={styles.imageContainer}>
          {selectedImage ? (
            <View style={styles.previewWrapper}>
              <Image source={{ uri: selectedImage }} style={styles.previewImage} />
              <TouchableOpacity style={styles.retakeBtn} onPress={() => setSelectedImage(null)}>
                <Text style={styles.retakeText}>✕ {t.scan.retake}</Text>
              </TouchableOpacity>
            </View>
          ) : (
            <View style={styles.placeholderBox}>
              <Text style={styles.cameraIcon}>📷</Text>
              <Text style={styles.placeholderText}>No photo selected yet</Text>
            </View>
          )}
        </View>

        {/* Action Buttons */}
        {!selectedImage ? (
          <View style={styles.buttonRow}>
            <TouchableOpacity style={styles.primaryButton} onPress={handleTakePhoto}>
              <Text style={styles.primaryButtonText}>{t.scan.takePhoto}</Text>
            </TouchableOpacity>
            <TouchableOpacity style={styles.secondaryButton} onPress={handlePickImage}>
              <Text style={styles.secondaryButtonText}>{t.scan.chooseGallery}</Text>
            </TouchableOpacity>
          </View>
        ) : (
          <TouchableOpacity
            style={[styles.diagnoseButton, loading && styles.buttonDisabled]}
            disabled={loading}
            onPress={handleDiagnose}
          >
            {loading ? (
              <View style={styles.loadingRow}>
                <ActivityIndicator color="#ffffff" style={{ marginRight: 8 }} />
                <Text style={styles.diagnoseText}>{stageProgress || t.scan.analyzing}</Text>
              </View>
            ) : (
              <Text style={styles.diagnoseText}>🔍 {t.scan.diagnose}</Text>
            )}
          </TouchableOpacity>
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
    padding: 18,
    paddingBottom: 40,
  },
  header: {
    marginBottom: 16,
  },
  title: {
    fontSize: 24,
    fontWeight: '700',
    color: '#1a4329',
    marginBottom: 6,
  },
  subtitle: {
    fontSize: 14,
    color: '#4f6b56',
    lineHeight: 20,
  },
  sectionLabel: {
    fontSize: 14,
    fontWeight: '600',
    color: '#2d4a34',
    marginTop: 12,
    marginBottom: 8,
  },
  pillScroll: {
    flexDirection: 'row',
    marginBottom: 10,
  },
  pill: {
    paddingHorizontal: 14,
    paddingVertical: 7,
    borderRadius: 20,
    backgroundColor: '#e6efe8',
    marginRight: 8,
    borderWidth: 1,
    borderColor: '#cde0d1',
  },
  pillActive: {
    backgroundColor: '#2d6a4f',
    borderColor: '#1e4835',
  },
  pillText: {
    fontSize: 13,
    color: '#344e41',
  },
  pillTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  partRow: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 8,
    marginBottom: 16,
  },
  partButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 8,
    backgroundColor: '#edf2ed',
    borderWidth: 1,
    borderColor: '#d2ddd3',
  },
  partButtonActive: {
    backgroundColor: '#52796f',
    borderColor: '#354f52',
  },
  partText: {
    fontSize: 12,
    color: '#354f52',
  },
  partTextActive: {
    color: '#ffffff',
    fontWeight: '600',
  },
  imageContainer: {
    marginVertical: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  placeholderBox: {
    width: '100%',
    height: 240,
    borderRadius: 16,
    borderWidth: 2,
    borderColor: '#bad1c0',
    borderStyle: 'dashed',
    backgroundColor: '#f0f5f1',
    alignItems: 'center',
    justifyContent: 'center',
  },
  cameraIcon: {
    fontSize: 48,
    marginBottom: 8,
  },
  placeholderText: {
    fontSize: 14,
    color: '#718f78',
  },
  previewWrapper: {
    width: '100%',
    height: 280,
    borderRadius: 16,
    overflow: 'hidden',
    position: 'relative',
    backgroundColor: '#000',
  },
  previewImage: {
    width: '100%',
    height: '100%',
    resizeMode: 'cover',
  },
  retakeBtn: {
    position: 'absolute',
    top: 12,
    right: 12,
    backgroundColor: 'rgba(0,0,0,0.65)',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 14,
  },
  retakeText: {
    color: '#fff',
    fontSize: 12,
    fontWeight: '600',
  },
  buttonRow: {
    flexDirection: 'row',
    gap: 12,
    marginTop: 8,
  },
  primaryButton: {
    flex: 1,
    backgroundColor: '#2d6a4f',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    elevation: 2,
  },
  primaryButtonText: {
    color: '#ffffff',
    fontSize: 15,
    fontWeight: '600',
  },
  secondaryButton: {
    flex: 1,
    backgroundColor: '#d8f3dc',
    paddingVertical: 14,
    borderRadius: 12,
    alignItems: 'center',
    borderWidth: 1,
    borderColor: '#b7e4c7',
  },
  secondaryButtonText: {
    color: '#1b4332',
    fontSize: 15,
    fontWeight: '600',
  },
  diagnoseButton: {
    backgroundColor: '#1b4332',
    paddingVertical: 16,
    borderRadius: 14,
    alignItems: 'center',
    marginTop: 10,
    elevation: 3,
  },
  buttonDisabled: {
    backgroundColor: '#6b8a74',
  },
  diagnoseText: {
    color: '#ffffff',
    fontSize: 16,
    fontWeight: '700',
  },
  loadingRow: {
    flexDirection: 'row',
    alignItems: 'center',
  },
});
