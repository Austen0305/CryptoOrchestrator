import React, { useEffect, useState } from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { NavigationContainer } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MaterialCommunityIcons } from '@expo/vector-icons';

// Services
import BiometricAuth from './services/BiometricAuth';

// Screens
import DashboardScreen from './screens/DashboardScreen';

// Create Query Client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 2,
      staleTime: 5000,
      refetchOnWindowFocus: false,
    },
  },
});

// Tab Navigator
const Tab = createBottomTabNavigator();

// Placeholder screens for other tabs
const PortfolioScreen = () => (
  <SafeAreaView style={styles.container}>
    <View style={styles.centered}>
      <MaterialCommunityIcons name="wallet" size={64} color="#10b981" />
      <Text style={styles.title}>Portfolio</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  </SafeAreaView>
);

const TradingScreen = () => (
  <SafeAreaView style={styles.container}>
    <View style={styles.centered}>
      <MaterialCommunityIcons name="chart-line" size={64} color="#3b82f6" />
      <Text style={styles.title}>Trading</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  </SafeAreaView>
);

const SettingsScreen = () => (
  <SafeAreaView style={styles.container}>
    <View style={styles.centered}>
      <MaterialCommunityIcons name="cog" size={64} color="#8b5cf6" />
      <Text style={styles.title}>Settings</Text>
      <Text style={styles.subtitle}>Coming Soon</Text>
    </View>
  </SafeAreaView>
);

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [biometricsAvailable, setBiometricsAvailable] = useState(false);

  useEffect(() => {
    initializeApp();
  }, []);

  const initializeApp = async () => {
    try {
      // Check if biometrics are available
      const available = await BiometricAuth.isBiometricAvailable();
      setBiometricsAvailable(available);

      if (available) {
        // Attempt biometric authentication
        const authenticated = await BiometricAuth.authenticate(
          'Unlock CryptoOrchestrator',
          'Use biometrics to access your trading account'
        );

        if (authenticated) {
          setIsAuthenticated(true);
        } else {
          Alert.alert(
            'Authentication Failed',
            'Biometric authentication failed. Please try again.',
            [
              {
                text: 'Retry',
                onPress: initializeApp,
              },
              {
                text: 'Skip',
                onPress: () => setIsAuthenticated(true),
                style: 'cancel',
              },
            ]
          );
        }
      } else {
        // No biometrics available, proceed without authentication
        setIsAuthenticated(true);
      }
    } catch (error) {
      console.error('App initialization error:', error);
      setIsAuthenticated(true); // Allow access on error
    } finally {
      setIsLoading(false);
    }
  };

  if (isLoading) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centered}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={[styles.subtitle, { marginTop: 16 }]}>
            {biometricsAvailable ? 'Authenticating...' : 'Loading...'}
          </Text>
        </View>
      </SafeAreaView>
    );
  }

  if (!isAuthenticated) {
    return (
      <SafeAreaView style={styles.container}>
        <View style={styles.centered}>
          <MaterialCommunityIcons name="shield-lock" size={64} color="#ef4444" />
          <Text style={styles.title}>Authentication Required</Text>
          <Text style={styles.subtitle}>Please authenticate to continue</Text>
        </View>
      </SafeAreaView>
    );
  }

  return (
    <QueryClientProvider client={queryClient}>
      <NavigationContainer>
        <StatusBar barStyle="light-content" backgroundColor="#1f2937" />
        <Tab.Navigator
          screenOptions={({ route }) => ({
            headerStyle: {
              backgroundColor: '#1f2937',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
            tabBarStyle: {
              backgroundColor: '#1f2937',
              borderTopColor: '#374151',
            },
            tabBarActiveTintColor: '#3b82f6',
            tabBarInactiveTintColor: '#9ca3af',
            tabBarIcon: ({ focused, color, size }) => {
              let iconName: keyof typeof MaterialCommunityIcons.glyphMap = 'help-circle';

              if (route.name === 'Dashboard') {
                iconName = focused ? 'view-dashboard' : 'view-dashboard-outline';
              } else if (route.name === 'Portfolio') {
                iconName = focused ? 'wallet' : 'wallet-outline';
              } else if (route.name === 'Trading') {
                iconName = focused ? 'chart-line' : 'chart-line';
              } else if (route.name === 'Settings') {
                iconName = focused ? 'cog' : 'cog-outline';
              }

              return <MaterialCommunityIcons name={iconName} size={size} color={color} />;
            },
          })}
        >
          <Tab.Screen 
            name="Dashboard" 
            component={DashboardScreen}
            options={{ title: 'Dashboard' }}
          />
          <Tab.Screen 
            name="Portfolio" 
            component={PortfolioScreen}
            options={{ title: 'Portfolio' }}
          />
          <Tab.Screen 
            name="Trading" 
            component={TradingScreen}
            options={{ title: 'Trading' }}
          />
          <Tab.Screen 
            name="Settings" 
            component={SettingsScreen}
            options={{ title: 'Settings' }}
          />
        </Tab.Navigator>
      </NavigationContainer>
    </QueryClientProvider>
  );
};

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#111827',
  },
  centered: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    padding: 24,
  },
  title: {
    fontSize: 24,
    fontWeight: 'bold',
    color: '#f9fafb',
    marginTop: 16,
  },
  subtitle: {
    fontSize: 16,
    color: '#9ca3af',
    marginTop: 8,
    textAlign: 'center',
  },
});

export default App;
