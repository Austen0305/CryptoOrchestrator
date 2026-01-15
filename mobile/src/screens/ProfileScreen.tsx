/**
 * Profile Screen for Mobile App
 * User profile management, account settings, and security
 */

import React, { useState, useEffect } from "react";
import {
  View,
  Text,
  StyleSheet,
  ScrollView,
  TextInput,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Switch,
} from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "../services/api";
import AsyncStorage from "@react-native-async-storage/async-storage";
import BiometricAuth from "../services/BiometricAuth";

interface UserProfile {
  id: string;
  email: string;
  username?: string;
  first_name?: string;
  last_name?: string;
  two_factor_enabled?: boolean;
  created_at?: string;
}

export default function ProfileScreen() {
  const queryClient = useQueryClient();
  const [editing, setEditing] = useState(false);
  const [biometricsEnabled, setBiometricsEnabled] = useState(false);
  const [formData, setFormData] = useState({
    username: "",
    first_name: "",
    last_name: "",
    email: "",
  });

  // Fetch user profile
  const { data: profile, isLoading } = useQuery({
    queryKey: ["userProfile"],
    queryFn: async () => {
      return await api.get<UserProfile>("users/me");
    },
  });

  // Update profile mutation
  const updateProfileMutation = useMutation({
    mutationFn: (data: Partial<UserProfile>) => api.post("users/me", data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["userProfile"] });
      setEditing(false);
      Alert.alert("Success", "Profile updated successfully");
    },
    onError: (error: unknown) => {
      const errorData = (error as { response?: { data?: { detail?: string } } }).response?.data;
      const errorDetail = errorData?.detail ?? (error as Error).message;
      Alert.alert("Error", errorDetail);
    },
  });

  // Change password mutation
  const changePasswordMutation = useMutation({
    mutationFn: (data: { current_password: string; new_password: string }) =>
      api.post("users/change-password", data),
    onSuccess: () => {
      Alert.alert("Success", "Password changed successfully");
    },
    onError: (error: unknown) => {
      const errorData = (error as { response?: { data?: { detail?: string } } }).response?.data;
      const errorDetail = errorData?.detail ?? (error as Error).message;
      Alert.alert("Error", errorDetail);
    },
  });

  useEffect(() => {
    if (profile) {
      setFormData({
        username: profile.username ?? "",
        first_name: profile.first_name ?? "",
        last_name: profile.last_name ?? "",
        email: profile.email,
      });
    }
    checkBiometricStatus();
  }, [profile]);

  const checkBiometricStatus = async () => {
    try {
      const result = await BiometricAuth.isBiometricAvailable();
      setBiometricsEnabled(result.available);
    } catch (error) {
      console.error("Error checking biometric status:", error);
    }
  };

  const handleSave = () => {
    updateProfileMutation.mutate(formData);
  };

  const handleChangePassword = () => {
    Alert.prompt(
      "Change Password",
      "Enter your current password:",
      [
        {
          text: "Cancel",
          style: "cancel",
        },
        {
          text: "Next",
          onPress: (currentPassword?: string) => {
            if (!currentPassword) {
              Alert.alert("Error", "Current password is required");
              return;
            }
            Alert.prompt(
              "New Password",
              "Enter your new password:",
              [
                {
                  text: "Cancel",
                  style: "cancel",
                },
                {
                  text: "Change",
                  onPress: (newPassword?: string) => {
                    if (!newPassword || newPassword.length < 8) {
                      Alert.alert("Error", "New password must be at least 8 characters");
                      return;
                    }
                    if (currentPassword) {
                      changePasswordMutation.mutate({
                        current_password: currentPassword,
                        new_password: newPassword,
                      });
                    }
                  },
                },
              ],
              "secure-text"
            );
          },
        },
      ],
      "secure-text"
    );
  };

  const enableBiometricAuth = async () => {
    try {
      const result = await BiometricAuth.authenticate("Enable Biometric Authentication");
      if (result.success) {
        setBiometricsEnabled(true);
        Alert.alert("Success", "Biometric authentication enabled");
      } else {
        Alert.alert("Error", result.error ?? "Failed to enable biometric authentication");
      }
    } catch (error) {
      Alert.alert("Error", "Failed to enable biometric authentication");
    }
  };

  const disableBiometricAuth = () => {
    setBiometricsEnabled(false);
  };

  if (isLoading) {
    return (
      <View style={styles.container}>
        <View style={styles.loadingContainer}>
          <ActivityIndicator size="large" color="#3b82f6" />
          <Text style={styles.loadingText}>Loading profile...</Text>
        </View>
      </View>
    );
  }

  return (
    <ScrollView style={styles.container}>
      <View style={styles.content}>
        {/* Profile Header */}
        <View style={styles.profileHeader}>
          <View style={styles.avatarContainer}>
            <MaterialCommunityIcons name="account-circle" size={80} color="#3b82f6" />
          </View>
          <Text style={styles.profileName}>
            {profile?.first_name && profile.last_name
              ? `${profile.first_name} ${profile.last_name}`
              : profile?.username ?? profile?.email ?? "User"}
          </Text>
          <Text style={styles.profileEmail}>{profile?.email}</Text>
        </View>

        {/* Profile Information */}
        <View style={styles.section}>
          <View style={styles.sectionHeader}>
            <Text style={styles.sectionTitle}>Profile Information</Text>
            {!editing && (
              <TouchableOpacity onPress={() => setEditing(true)}>
                <MaterialCommunityIcons name="pencil" size={20} color="#3b82f6" />
              </TouchableOpacity>
            )}
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Username</Text>
            <TextInput
              style={[styles.input, !editing && styles.inputDisabled]}
              value={formData.username}
              onChangeText={(text) => setFormData({ ...formData, username: text })}
              editable={editing}
              placeholder="Username"
              placeholderTextColor="#6b7280"
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>First Name</Text>
            <TextInput
              style={[styles.input, !editing && styles.inputDisabled]}
              value={formData.first_name}
              onChangeText={(text) => setFormData({ ...formData, first_name: text })}
              editable={editing}
              placeholder="First Name"
              placeholderTextColor="#6b7280"
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Last Name</Text>
            <TextInput
              style={[styles.input, !editing && styles.inputDisabled]}
              value={formData.last_name}
              onChangeText={(text) => setFormData({ ...formData, last_name: text })}
              editable={editing}
              placeholder="Last Name"
              placeholderTextColor="#6b7280"
            />
          </View>

          <View style={styles.formGroup}>
            <Text style={styles.label}>Email</Text>
            <TextInput
              style={[styles.input, styles.inputDisabled]}
              value={formData.email}
              editable={false}
              placeholder="Email"
              placeholderTextColor="#6b7280"
            />
            <Text style={styles.helpText}>Email cannot be changed</Text>
          </View>

          {editing && (
            <View style={styles.buttonRow}>
              <TouchableOpacity
                style={[styles.button, styles.buttonCancel]}
                onPress={() => {
                  setEditing(false);
                  if (profile) {
                    setFormData({
                      username: profile.username ?? "",
                      first_name: profile.first_name ?? "",
                      last_name: profile.last_name ?? "",
                      email: profile.email,
                    });
                  }
                }}
              >
                <Text style={styles.buttonCancelText}>Cancel</Text>
              </TouchableOpacity>
              <TouchableOpacity
                style={[styles.button, styles.buttonSave]}
                onPress={handleSave}
                disabled={updateProfileMutation.isPending}
              >
                {updateProfileMutation.isPending ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text style={styles.buttonSaveText}>Save</Text>
                )}
              </TouchableOpacity>
            </View>
          )}
        </View>

        {/* Security Settings */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Security</Text>

          <TouchableOpacity style={styles.settingItem} onPress={handleChangePassword}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="lock" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Change Password</Text>
                <Text style={styles.settingDescription}>Update your account password</Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </TouchableOpacity>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="fingerprint" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Biometric Authentication</Text>
                <Text style={styles.settingDescription}>Use Face ID, Touch ID, or fingerprint</Text>
              </View>
            </View>
            <Switch
              value={biometricsEnabled}
              onValueChange={(value) => {
                if (value) {
                  void enableBiometricAuth();
                } else {
                  disableBiometricAuth();
                }
              }}
              trackColor={{ false: "#374151", true: "#3b82f6" }}
              thumbColor="#fff"
            />
          </View>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="shield-check" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Two-Factor Authentication</Text>
                <Text style={styles.settingDescription}>
                  {profile?.two_factor_enabled ? "Enabled" : "Not enabled"}
                </Text>
              </View>
            </View>
            <MaterialCommunityIcons name="chevron-right" size={24} color="#9ca3af" />
          </View>
        </View>

        {/* Account Information */}
        <View style={styles.section}>
          <Text style={styles.sectionTitle}>Account</Text>

          <View style={styles.settingItem}>
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="calendar" size={24} color="#3b82f6" />
              <View style={styles.settingText}>
                <Text style={styles.settingLabel}>Member Since</Text>
                <Text style={styles.settingDescription}>
                  {profile?.created_at ? new Date(profile.created_at).toLocaleDateString() : "N/A"}
                </Text>
              </View>
            </View>
          </View>

          <TouchableOpacity
            style={styles.settingItem}
            onPress={() => {
              Alert.alert("Log Out", "Are you sure you want to log out?", [
                { text: "Cancel", style: "cancel" },
                {
                  text: "Log Out",
                  style: "destructive",
                  onPress: () => {
                    void (async () => {
                      try {
                        await api.post("auth/logout", {});
                        await AsyncStorage.removeItem("auth_token");
                        // Navigate to login screen (would need navigation prop)
                      } catch (error) {
                        console.error("Logout error:", error);
                      }
                    })();
                  },
                },
              ]);
            }}
          >
            <View style={styles.settingInfo}>
              <MaterialCommunityIcons name="logout" size={24} color="#ef4444" />
              <View style={styles.settingText}>
                <Text style={[styles.settingLabel, styles.logoutText]}>Log Out</Text>
                <Text style={styles.settingDescription}>Sign out of your account</Text>
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
  loadingContainer: {
    flex: 1,
    justifyContent: "center",
    alignItems: "center",
  },
  loadingText: {
    color: "#9ca3af",
    marginTop: 16,
  },
  profileHeader: {
    alignItems: "center",
    paddingVertical: 32,
    marginBottom: 24,
  },
  avatarContainer: {
    marginBottom: 16,
  },
  profileName: {
    color: "#fff",
    fontSize: 24,
    fontWeight: "bold",
    marginBottom: 4,
  },
  profileEmail: {
    color: "#9ca3af",
    fontSize: 16,
  },
  section: {
    marginBottom: 32,
  },
  sectionHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    marginBottom: 16,
  },
  sectionTitle: {
    color: "#fff",
    fontSize: 18,
    fontWeight: "600",
  },
  formGroup: {
    marginBottom: 16,
  },
  label: {
    color: "#9ca3af",
    fontSize: 14,
    marginBottom: 8,
  },
  input: {
    backgroundColor: "#1e293b",
    borderWidth: 1,
    borderColor: "#334155",
    borderRadius: 8,
    padding: 16,
    color: "#fff",
    fontSize: 16,
  },
  inputDisabled: {
    opacity: 0.6,
  },
  helpText: {
    color: "#6b7280",
    fontSize: 12,
    marginTop: 4,
  },
  buttonRow: {
    flexDirection: "row",
    gap: 12,
    marginTop: 8,
  },
  button: {
    flex: 1,
    padding: 16,
    borderRadius: 8,
    alignItems: "center",
    justifyContent: "center",
    minHeight: 44,
  },
  buttonCancel: {
    backgroundColor: "#1e293b",
    borderWidth: 1,
    borderColor: "#334155",
  },
  buttonCancelText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
  },
  buttonSave: {
    backgroundColor: "#3b82f6",
  },
  buttonSaveText: {
    color: "#fff",
    fontSize: 16,
    fontWeight: "600",
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
  logoutText: {
    color: "#ef4444",
  },
});
