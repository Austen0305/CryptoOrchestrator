import React, { useEffect, useState, useRef } from 'react';
import {
  SafeAreaView,
  StatusBar,
  StyleSheet,
  View,
  Text,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { NavigationContainer, NavigationContainerRef } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { MaterialCommunityIcons } from '@expo/vector-icons';
import * as Notifications from 'expo-notifications';

// Services
import BiometricAuth from './services/BiometricAuth';
import pushNotificationService from './services/PushNotificationService';
import offlineService from './services/OfflineService';

// Screens
import DashboardScreen from './screens/DashboardScreen';
import PortfolioScreen from './screens/PortfolioScreen';
import TradingScreen from './screens/TradingScreen';
import ProfileScreen from './screens/ProfileScreen';

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

import SettingsScreen from './screens/SettingsScreen';

const App = () => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [biometricsAvailable, setBiometricsAvailable] = useState(false);
  const navigationRef = useRef<NavigationContainerRef<any>>(null);

  useEffect(() => {
    initializeApp();
    initializePushNotifications();
    initializeOfflineService();
  }, []);

  const handleNotificationNavigation = (notificationData: any) => {
    if (!navigationRef.current) return;

    const { type, trade_id, bot_id, notification_id } = notificationData || {};

    try {
      // Navigate based on notification type
      switch (type) {
        case 'trade_executed':
        case 'trade_failed':
        case 'order_filled':
          // Navigate to Trading screen, optionally with trade details
          navigationRef.current.navigate('Trading', { tradeId: trade_id });
          break;
        case 'bot_started':
        case 'bot_stopped':
          // Navigate to Dashboard (where bots are displayed)
          navigationRef.current.navigate('Dashboard', { botId: bot_id });
          break;
        case 'risk_alert':
        case 'portfolio_alert':
          // Navigate to Portfolio screen
          navigationRef.current.navigate('Portfolio');
          break;
        case 'price_alert':
          // Navigate to Trading screen
          navigationRef.current.navigate('Trading');
          break;
        default:
          // Default to Dashboard
          navigationRef.current.navigate('Dashboard');
      }
    } catch (error) {
      console.error('Error navigating from notification:', error);
    }
  };

  const initializePushNotifications = async () => {
    try {
      // Request permissions and register
      const token = await pushNotificationService.registerForPushNotifications();
      if (token) {
        // Subscribe to backend
        const subscribed = await pushNotificationService.subscribe();
        if (subscribed) {
          console.log('Successfully subscribed to push notifications');
        } else {
          console.warn('Failed to subscribe to push notifications');
        }
      }

      // Handle notification received while app is in foreground
      const receivedListener = Notifications.addNotificationReceivedListener((notification) => {
        console.log('Notification received (foreground):', notification);
        
        // Show a local alert for foreground notifications
        const { title, body, data } = notification.request.content;
        Alert.alert(
          title || 'Notification',
          body || 'You have a new notification',
          [
            {
              text: 'View',
              onPress: () => handleNotificationNavigation(data),
            },
            {
              text: 'Dismiss',
              style: 'cancel',
            },
          ]
        );
      });

      // Handle notification tapped (when app is in background or closed)
      const responseListener = Notifications.addNotificationResponseReceivedListener((response) => {
        console.log('Notification tapped:', response);
        const { data } = response.notification.request.content;
        handleNotificationNavigation(data);
      });

      // Cleanup listeners on unmount
      return () => {
        Notifications.removeNotificationSubscription(receivedListener);
        Notifications.removeNotificationSubscription(responseListener);
      };
    } catch (error) {
      console.error('Error initializing push notifications:', error);
      Alert.alert(
        'Notification Error',
        'Failed to initialize push notifications. Please check your settings.',
        [{ text: 'OK' }]
      );
    }
  };

  const initializeOfflineService = () => {
    // Listen to offline service events
    offlineService.on('networkStatusChanged', (isOnline: boolean) => {
      console.log('Network status changed:', isOnline);
    });

    offlineService.on('syncCompleted', (result: any) => {
      console.log('Sync completed:', result);
    });
  };

  const initializeApp = async () => {
    try {
      // Check if biometrics are available
      const biometricResult = await BiometricAuth.isBiometricAvailable();
      setBiometricsAvailable(biometricResult.available);

      if (biometricResult.available) {
        // Attempt biometric authentication
        const authResult = await BiometricAuth.authenticate(
          'Unlock CryptoOrchestrator'
        );

        if (authResult.success) {
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
      <NavigationContainer ref={navigationRef}>
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
              } else if (route.name === 'Profile') {
                iconName = focused ? 'account' : 'account-outline';
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
          <Tab.Screen 
            name="Profile" 
            component={ProfileScreen}
            options={{ title: 'Profile', tabBarButton: () => null }} // Hidden from tabs, accessible from Settings
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
