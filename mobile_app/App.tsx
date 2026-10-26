import React, { useState } from 'react';
import { StatusBar } from 'expo-status-bar';
import { NavigationContainer } from '@react-navigation/native';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { Text } from 'react-native';

import { ScanScreen } from './src/screens/ScanScreen';
import { ResultScreen } from './src/screens/ResultScreen';
import { TreatmentScreen } from './src/screens/TreatmentScreen';
import { SettingsScreen } from './src/screens/SettingsScreen';
import { getTranslation } from './src/translations';
import { RootStackParamList, SupportedLanguage } from './src/types';

const Stack = createNativeStackNavigator<RootStackParamList>();
const Tab = createBottomTabNavigator();

export default function App() {
  const [language, setLanguage] = useState<SupportedLanguage>('en');
  const t = getTranslation(language);

  const MainTabs = () => (
    <Tab.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: '#1b4332' },
        headerTintColor: '#ffffff',
        headerTitleStyle: { fontWeight: '700' },
        tabBarActiveTintColor: '#2d6a4f',
        tabBarInactiveTintColor: '#6c757d',
        tabBarStyle: {
          backgroundColor: '#ffffff',
          borderTopColor: '#e0e0e0',
          height: 60,
          paddingBottom: 8,
          paddingTop: 8,
        },
      }}
    >
      <Tab.Screen
        name="ScanTab"
        options={{
          title: t.tabs.scan,
          headerTitle: t.appName,
          tabBarIcon: () => <Text style={{ fontSize: 20 }}>📷</Text>,
        }}
      >
        {(props) => <ScanScreen {...props} language={language} />}
      </Tab.Screen>

      <Tab.Screen
        name="SettingsTab"
        options={{
          title: t.tabs.settings,
          headerTitle: t.settings.title,
          tabBarIcon: () => <Text style={{ fontSize: 20 }}>⚙️</Text>,
        }}
      >
        {(props) => (
          <SettingsScreen
            {...props}
            language={language}
            onLanguageChange={(newLang) => setLanguage(newLang)}
          />
        )}
      </Tab.Screen>
    </Tab.Navigator>
  );

  return (
    <NavigationContainer>
      <StatusBar style="light" />
      <Stack.Navigator
        screenOptions={{
          headerStyle: { backgroundColor: '#1b4332' },
          headerTintColor: '#ffffff',
          headerTitleStyle: { fontWeight: '700' },
        }}
      >
        <Stack.Screen
          name="MainTabs"
          component={MainTabs}
          options={{ headerShown: false }}
        />
        <Stack.Screen
          name="ResultScreen"
          options={{ title: t.result.title }}
        >
          {(props: any) => <ResultScreen {...props} language={language} />}
        </Stack.Screen>
        <Stack.Screen
          name="TreatmentScreen"
          options={{ title: t.treatment.title }}
        >
          {(props: any) => <TreatmentScreen {...props} language={language} />}
        </Stack.Screen>
      </Stack.Navigator>
    </NavigationContainer>
  );
}
