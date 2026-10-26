import React, { useState } from 'react';
import {
  ActivityIndicator,
  Alert,
  SafeAreaView,
  ScrollView,
  StyleSheet,
  Text,
  TextInput,
  TouchableOpacity,
  View,
} from 'react-native';
import { environment } from '../config/environment';
import { ApiService } from '../services/apiService';
import { getTranslation } from '../translations';
import { SupportedLanguage } from '../types';

interface SettingsScreenProps {
  language: SupportedLanguage;
  onLanguageChange: (lang: SupportedLanguage) => void;
}

export const SettingsScreen: React.FC<SettingsScreenProps> = ({
  language,
  onLanguageChange,
}) => {
  const t = getTranslation(language);
  const [serverUrl, setServerUrl] = useState<string>(environment.apiUrl);
  const [testing, setTesting] = useState<boolean>(false);
  const [testResult, setTestResult] = useState<{ status: string; engine: string; ready: boolean } | null>(null);

  const handleSaveUrl = () => {
    environment.apiUrl = serverUrl;
    Alert.alert('Saved', `API URL updated to: ${environment.apiUrl}`);
  };

  const handleTestConnection = async () => {
    environment.apiUrl = serverUrl;
    setTesting(true);
    setTestResult(null);

    const res = await ApiService.checkHealth();
    setTesting(false);
    setTestResult(res);

    if (res.ready) {
      Alert.alert('Success', `${t.settings.connectionSuccess}\nEngine: ${res.engine}`);
    } else {
      Alert.alert('Connection Failed', t.settings.connectionFailed);
    }
  };

  const handleUseRenderUrl = () => {
    setServerUrl(environment.renderUrl);
    environment.apiUrl = environment.renderUrl;
  };

  return (
    <SafeAreaView style={styles.container}>
      <ScrollView contentContainerStyle={styles.scrollContent}>
        <Text style={styles.screenTitle}>{t.settings.title}</Text>

        {/* Language Selection */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🌐 {t.settings.language}</Text>
          <View style={styles.langRow}>
            <TouchableOpacity
              style={[styles.langBtn, language === 'en' && styles.langBtnActive]}
              onPress={() => onLanguageChange('en')}
            >
              <Text style={[styles.langText, language === 'en' && styles.langTextActive]}>
                English
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.langBtn, language === 'kn' && styles.langBtnActive]}
              onPress={() => onLanguageChange('kn')}
            >
              <Text style={[styles.langText, language === 'kn' && styles.langTextActive]}>
                ಕನ್ನಡ (Kannada)
              </Text>
            </TouchableOpacity>

            <TouchableOpacity
              style={[styles.langBtn, language === 'hi' && styles.langBtnActive]}
              onPress={() => onLanguageChange('hi')}
            >
              <Text style={[styles.langText, language === 'hi' && styles.langTextActive]}>
                हिन्दी (Hindi)
              </Text>
            </TouchableOpacity>
          </View>
        </View>

        {/* Backend Connectivity Configuration */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>🔌 {t.settings.serverUrl}</Text>
          <Text style={styles.helpText}>
            Configure the endpoint for your backend service. Physical mobile devices should use the
            host computer's Wi-Fi IP address (e.g., http://192.168.1.15:8000) or Render cloud URL.
          </Text>

          <TextInput
            style={styles.input}
            value={serverUrl}
            onChangeText={setServerUrl}
            placeholder="http://10.0.2.2:8000"
            autoCapitalize="none"
            autoCorrect={false}
          />

          <View style={styles.btnRow}>
            <TouchableOpacity style={styles.saveBtn} onPress={handleSaveUrl}>
              <Text style={styles.btnText}>Save URL</Text>
            </TouchableOpacity>

            <TouchableOpacity style={styles.renderBtn} onPress={handleUseRenderUrl}>
              <Text style={styles.btnText}>Use Render URL</Text>
            </TouchableOpacity>
          </View>

          <TouchableOpacity
            style={[styles.testBtn, testing && styles.btnDisabled]}
            disabled={testing}
            onPress={handleTestConnection}
          >
            {testing ? (
              <ActivityIndicator color="#fff" />
            ) : (
              <Text style={styles.testBtnText}>⚡ {t.settings.testConnection}</Text>
            )}
          </TouchableOpacity>

          {testResult && (
            <View
              style={[
                styles.statusBanner,
                testResult.ready ? styles.statusSuccess : styles.statusError,
              ]}
            >
              <Text style={styles.statusBannerText}>
                {testResult.ready ? 'ONLINE' : 'OFFLINE'} • {testResult.engine}
              </Text>
            </View>
          )}
        </View>

        {/* About Card */}
        <View style={styles.card}>
          <Text style={styles.sectionTitle}>ℹ️ {t.settings.about}</Text>
          <Text style={styles.aboutText}>
            PlantScan AI is an edge-optimized agricultural deep learning platform combining Stage 1
            anatomical plant-part classification (Leaf, Stem, Fruit, Bark) and Stage 2 crop
            pathology identification with Integrated Pest Management (IPM).
          </Text>
          <Text style={styles.versionText}>{t.settings.version}</Text>
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
  screenTitle: {
    fontSize: 22,
    fontWeight: '700',
    color: '#1a4329',
    marginBottom: 16,
  },
  card: {
    backgroundColor: '#ffffff',
    borderRadius: 14,
    padding: 16,
    marginBottom: 16,
    elevation: 2,
    shadowColor: '#000',
    shadowOpacity: 0.05,
    shadowRadius: 5,
  },
  sectionTitle: {
    fontSize: 16,
    fontWeight: '700',
    color: '#2d4a34',
    marginBottom: 10,
  },
  langRow: {
    gap: 8,
  },
  langBtn: {
    paddingVertical: 12,
    paddingHorizontal: 16,
    borderRadius: 10,
    backgroundColor: '#f0f5f1',
    borderWidth: 1,
    borderColor: '#d2ddd3',
  },
  langBtnActive: {
    backgroundColor: '#2d6a4f',
    borderColor: '#1e4835',
  },
  langText: {
    fontSize: 14,
    color: '#354f52',
    fontWeight: '500',
  },
  langTextActive: {
    color: '#ffffff',
    fontWeight: '700',
  },
  helpText: {
    fontSize: 12,
    color: '#6c757d',
    lineHeight: 18,
    marginBottom: 10,
  },
  input: {
    borderWidth: 1,
    borderColor: '#cde0d1',
    borderRadius: 10,
    padding: 12,
    fontSize: 14,
    color: '#1b4332',
    backgroundColor: '#fafcfa',
    marginBottom: 10,
  },
  btnRow: {
    flexDirection: 'row',
    gap: 10,
    marginBottom: 10,
  },
  saveBtn: {
    flex: 1,
    backgroundColor: '#52796f',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  renderBtn: {
    flex: 1,
    backgroundColor: '#354f52',
    paddingVertical: 10,
    borderRadius: 8,
    alignItems: 'center',
  },
  btnText: {
    color: '#ffffff',
    fontSize: 13,
    fontWeight: '600',
  },
  testBtn: {
    backgroundColor: '#1b4332',
    paddingVertical: 12,
    borderRadius: 10,
    alignItems: 'center',
  },
  btnDisabled: {
    backgroundColor: '#718f78',
  },
  testBtnText: {
    color: '#ffffff',
    fontSize: 14,
    fontWeight: '700',
  },
  statusBanner: {
    padding: 10,
    borderRadius: 8,
    marginTop: 10,
    alignItems: 'center',
  },
  statusSuccess: {
    backgroundColor: '#d8f3dc',
  },
  statusError: {
    backgroundColor: '#fee2e2',
  },
  statusBannerText: {
    fontSize: 12,
    fontWeight: '700',
    color: '#1b4332',
  },
  aboutText: {
    fontSize: 13,
    color: '#495057',
    lineHeight: 19,
    marginBottom: 10,
  },
  versionText: {
    fontSize: 12,
    color: '#868e96',
    fontWeight: '600',
  },
});
