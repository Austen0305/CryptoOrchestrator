/**
 * Settings Screen for Mobile App
 * User preferences, security, notifications, and app configuration
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TouchableOpacity,
  Switch,
  Alert,
  TextInput,
} from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigation } from "@react-navigation/native";
import BiometricAuth from "../services/BiometricAuth";
import { api } from "../services/api";
import AsyncStorage from "@react-native-async-storage/async-storage";
import pushNotificationService from "../services/PushNotificationService";
import { useOffline } from "../hooks/useOffline";

export default function SettingsScreen() {
  const navigation = useNavigation();
  const queryClient = useQueryClient();
  const { isOnline, queuedActions, syncNow, clearQueue } = useOffline();
  const [notificationsEnabled, setNotificationsEnabled] = useState(true);
  const [biometricsEnabled, setBiometricsEnabled] = useState(false);
  const [apiUrl, setApiUrl] = useState("");
  const [editingApiUrl, setEditingApiUrl] = useState(false);

  interface Preferences {
    push_notifications_enabled?: boolean;
    [key: string]: unknown;
  }

  // Fetch preferences
  const { data: preferences } = useQuery<Preferences>({
    queryKey: ["preferences"],
    queryFn: async () => {
      try {
        return await api.get<Preferences>("settings/preferences");
      } catch (error) {
        return {};
      }
    },
  });

  // Update preferences mutation
  const updatePreferencesMutation = useMutation({
    mutationFn: (data: Record<string, unknown>) => api.post("settings/preferences", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["preferences"] });
      Alert.alert("Success", "Preferences updated successfully");
    },
  });

  useEffect(() => {
    checkBiometricStatus();
    loadApiUrl();
    if (preferences) {
      setNotificationsEnabled(preferences.push_notifications_enabled ?? true);
    }
  }, [preferences]);

  const loadApiUrl = async () => {
    const url = await AsyncStorage.getItem("api_base_url");
    if (url) {
      setApiUrl(url);
    } else {
      setApiUrl(process.env.API_BASE_URL ?? "http://localhost:8000");
    }
  };

  const checkBiometricStatus = async () => {
    try {
      const result = await BiometricAuth.isBiometricAvailable();
      setBiometricsEnabled(result.available);
    } catch (error) {
      console.error("Error checking biometric status:", error);
    }
  };

  const handleBiometricToggle = async (value: boolean) => {
    if (value) {
      try {
        const result = await BiometricAuth.authenticate("Enable Biometric Authentication");
        if (result.success) {
          setBiometricsEnabled(true);
          updatePreferencesMutation.mutate({ biometric_auth_enabled: true });
          Alert.alert("Success", "Biometric authentication enabled");
        } else {
          Alert.alert("Error", result.error ?? "Failed to enable biometric authentication");
        }
      } catch (error) {
        Alert.alert("Error", "Failed to enable biometric authentication");
      }
    } else {
      setBiometricsEnabled(false);
      updatePreferencesMutation.mutate({ biometric_auth_enabled: false });
    }
  };

  const handleNotificationsToggle = async (value: boolean) => {
    setNotificationsEnabled(value);

    if (value) {
      // Subscribe to push notifications
      const subscribed = await pushNotificationService.subscribe();
      if (subscribed) {
        updatePreferencesMutation.mutate({ push_notifications_enabled: true });
      } else {
        Alert.alert("Error", "Failed to enable push notifications. Please check permissions.");
        setNotificationsEnabled(false);
      }
    } else {
      // Unsubscribe from push notifications
      await pushNotificationService.unsubscribe();
      updatePreferencesMutation.mutate({ push_notifications_enabled: false });
    }
  };

  const handleSaveApiUrl = async () => {
    if (apiUrl) {
      await AsyncStorage.setItem("api_base_url", apiUrl);
      setEditingApiUrl(false);
      Alert.alert("Success", "API URL updated. Restart app to apply changes.");
    }
  };

  const handleClearCache = () => {
    Alert.alert("Clear Cache", "This will clear all cached data. Continue?", [
      { text: "Cancel", style: "cancel" },
      {
        text: "Clear",
        style: "destructive",
        onPress: async () => {
          queryClient.clear();
          await AsyncStorage.multiRemove(["cached_data", "portfolio_cache"]);
          Alert.alert("Success", "Cache cleared");
        },
      },
    ]);
  };

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Security Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Security</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="fingerprint" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Biometric Authentication</Text>
                <Text style={styles.settingDescription}>
                  Use Face ID, Touch ID, or fingerprint to unlock the app
                </Text>
              </View>
            </View>
            <Switch
              value={biometricsEnabled}
              onValueChange={handleBiometricToggle}
              trackColor={{ false: "#374151", true: "#3b82f6" }}
              thumbColor="#fff"
            />
          </View>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              // Navigate to security settings
              Alert.alert("Security Settings", "Password and 2FA settings");
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="shield-lock" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Password & 2FA</Text>
                <Text style={styles.settingDescription}>
                  Change password and manage two-factor authentication
                </Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Notifications Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Notifications</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="bell" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Push Notifications</Text>
                <Text style={styles.settingDescription}>
                  Receive trading alerts and bot status updates
                </Text>
              </View>
            </View>
            <Switch
              value={notificationsEnabled}
              onValueChange={handleNotificationsToggle}
              trackColor={{ false: "#374151", true: "#3b82f6" }}
              thumbColor="#fff"
            />
          </View>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              Alert.alert("Notification Settings", "Configure notification preferences");
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="cog" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Notification Preferences</Text>
                <Text style={styles.settingDescription}>
                  Customize which notifications you receive
                </Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Trading Preferences */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Trading</Text>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              Alert.alert("Risk Settings", "Configure default risk limits");
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="chart-line" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Risk Settings</Text>
                <Text style={styles.settingDescription}>
                  Default risk limits and trading preferences
                </Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              Alert.alert("Trading Hours", "Set preferred trading hours");
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="clock-outline" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Trading Hours</Text>
                <Text style={styles.settingDescription}>Configure when bots can trade</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* Developer/Advanced Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Advanced</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="server-network" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>API URL</Text>
                <Text style={styles.settingDescription}>
                  Backend API endpoint (for development)
                </Text>
              </View>
            </View>
            {editingApiUrl ? (
              <TouchableOpacity onPress={handleSaveApiUrl}>
                <MaterialCommunityIcons name="check" size={24} color="#22c55e" />
              </TouchableOpacity>
            ) : (
              <TouchableOpacity onPress={() => setEditingApiUrl(true)}>
                <MaterialCommunityIcons name="pencil" size={20} color="#3b82f6" />
              </TouchableOpacity>
            )}
          </View>

          {editingApiUrl && (
            <View style={styles.inputContainer}>
              <TextInput
                style={styles.input}
                value={apiUrl}
                onChangeText={setApiUrl}
                placeholder="http://localhost:8000"
                placeholderTextColor="#6b7280"
                autoCapitalize="none"
                keyboardType="url"
              />
            </View>
          )}

          <TouchableOpacity style={styles.settingItem} onPress={handleClearCache}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="delete-outline" size={24} color="#ef4444" />
              <View style={styles.settingText}>
                <Text style={[styles.settingLabel, styles.dangerText]}>Clear Cache</Text>
                <Text style={styles.settingDescription}>Clear all cached data and refresh</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>

          {/* Offline Queue Management */}
          {queuedActions.length > 0 && (
            <View style={styles.settingItem}>
              <View style={styles.settingInfo}>
                <MaterialCommunityIcons name="cloud-upload" size={24} color="#3b82f6" />
                <View style={styles.settingText}>
                  <Text style={styles.settingLabel}>Queued Actions</Text>
                  <Text style={styles.settingDescription}>
                    {queuedActions.length} action{queuedActions.length === 1 ? "" : "s"} waiting to
                    sync
                  </Text>
                </View>
              </View>
              {isOnline && (
                <TouchableOpacity onPress={syncNow} style={styles.syncButton}>
                  <Text style={styles.syncButtonText}>Sync</Text>
                </TouchableOpacity>
              )}
            </View>
          )}

          {queuedActions.length > 0 && (
            <TouchableOpacity
              style={styles.settingItem}
              onPress={() => {
                Alert.alert("Clear Queue", "Are you sure you want to clear all queued actions?", [
                  { text: "Cancel", style: "cancel" },
                  {
                    text: "Clear",
                    style: "destructive",
                    onPress: () => void clearQueue(),
                  },
                ]);
              }}
            >
              <View style={styles.settingInfo}>
                <MaterialCommunityIcons name="delete-sweep" size={24} color="#ef4444" />
                <View style={styles.settingText}>
                  <Text style={[styles.settingLabel, styles.dangerText]}>Clear Queue</Text>
                  <Text style={styles.settingDescription}>Remove all queued actions</Text>
                </View>
              </View>
              <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
            </TouchableOpacity>
          )}
        </View>

        {/* Account Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              // Navigate to profile screen
              navigation.navigate("Profile" as never);
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="account" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Profile</Text>
                <Text style={styles.settingDescription}>View and edit your profile</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>
        </View>

        {/* About Section */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>About</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="information" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Version</Text>
                <Text style={styles.settingDescription}>1.0.0</Text>
              </View>
            </View>
          </View>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              Alert.alert("Help & Support", "Documentation and support resources");
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="help-circle" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Help & Support</Text>
                <Text style={styles.settingDescription}>Documentation and FAQs</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>
        </View>
      </View>
    </ScrollView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: "#0f172a",
  },
  content: {
    padding: 16,
  },
  section: {
    marginBottom: 32,
  },
  sectionTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
    marginBottom: 16,
  },
  settingItem: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "space-between",
    paddingVertical: 16,
    paddingHorizontal: 16,
    backgroundColor: "#1e293b",
    borderRadius: 12,
    marginBottom: 12,
    borderWidth: 1,
    borderColor: "#334155",
    minHeight: 44,
  },
  settingInfo: {
    flexDirection: "row",
    alignItems: "center",
    flex: 1,
  },
  settingText: {
    marginLeft: 12,
    flex: 1,
  },
  settingLabel: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "500",
    marginBottom: 4,
  },
  settingDescription: {
    color: "#9ca3af",
    fontSize: 12,
  },
  inputContainer: {
    marginTop: 8,
    marginBottom: 12,
  },
  input: {
    backgroundColor: "#1e293b",
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 8,
    padding: 16,
    color: "#fff",
    fontSize: 14,
    minHeight: 44,
  },
  dangerText: {
    color: "#ef4444",
  },
  syncButton: {
    paddingHorizontal: 12,
    paddingVertical: 6,
    backgroundColor: "#3b82f6",
    borderRadius: 6,
  },
  syncButtonText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
});
