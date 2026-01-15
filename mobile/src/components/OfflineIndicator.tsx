/**
 * Offline Indicator Component
 * Shows offline status and queued actions
 */

import React from "react";
import { View, Text, StyleSheet, TouchableOpacity } from "react-native";
import { MaterialCommunityIcons } from "@expo/vector-icons";
import { useOffline } from "../hooks/useOffline";

export default function OfflineIndicator() {
  const { isOnline, status: _status, queuedActions, syncNow } = useOffline();

  if (isOnline && queuedActions.length === 0) {
    return null; // Don't show when online and no queued actions
  }

  return (
    <View style={[styles.container, !isOnline && styles.offlineContainer]}>
      <MaterialCommunityIcons
        name={isOnline ? "cloud-sync" : "cloud-off-outline"}
        size={16}
        color={isOnline ? "#22c55e" : "#ef4444"}
      />
      <Text style={styles.text}>
        {isOnline
          ? `${queuedActions.length} action${queuedActions.length !== 1 ? "s" : ""} queued`
          : "Offline"}
      </Text>
      {isOnline && queuedActions.length > 0 && (
        <TouchableOpacity onPress={syncNow} style={styles.syncButton}>
          <Text style={styles.syncButtonText}>Sync Now</Text>
        </TouchableOpacity>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flexDirection: "row",
    alignItems: "center",
    justifyContent: "center",
    paddingVertical: 8,
    paddingHorizontal: 16,
    backgroundColor: "#22c55e",
    opacity: 0.1,
  },
  offlineContainer: {
    backgroundColor: "#ef4444",
  },
  text: {
    color: "#fff",
    fontSize: 12,
    marginLeft: 6,
    fontWeight: "600",
  },
  syncButton: {
    marginLeft: 12,
    paddingHorizontal: 12,
    paddingVertical: 4,
    backgroundColor: "#3b82f6",
    borderRadius: 4,
  },
  syncButtonText: {
    color: "#fff",
    fontSize: 12,
    fontWeight: "600",
  },
});
