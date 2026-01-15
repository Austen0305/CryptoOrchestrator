/**
 * Offline Service for Mobile App
 * Handles offline mode, data caching, and sync queue
 */

import AsyncStorage from "@react-native-async-storage/async-storage";
import NetInfo from "@react-native-community/netinfo";
import { api } from "./api";

// Simple EventEmitter implementation for React Native
class EventEmitter {
  private readonly listeners: Map<string, Function[]> = new Map();

  on(event: string, listener: Function): void {
    const eventListeners = this.listeners.get(event) ?? [];
    if (!this.listeners.has(event)) {
      this.listeners.set(event, eventListeners);
    }
    eventListeners.push(listener);
  }

  off(event: string, listener: Function): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      const index = eventListeners.indexOf(listener);
      if (index > -1) {
        eventListeners.splice(index, 1);
      }
    }
  }

  emit(event: string, ...args: unknown[]): void {
    const eventListeners = this.listeners.get(event);
    if (eventListeners) {
      eventListeners.forEach((listener) => listener(...args));
    }
  }
}

export interface QueuedAction {
  id: string;
  type: "trade" | "bot_action" | "withdrawal" | "deposit";
  action: string;
  payload: Record<string, unknown>;
  timestamp: number;
  retries: number;
  maxRetries?: number;
}

export interface OfflineStatus {
  isOnline: boolean;
  isConnected: boolean;
  queuedActions: number;
  lastSyncTime: number | null;
}

class OfflineService extends EventEmitter {
  private isOnline: boolean = true;
  private queuedActions: QueuedAction[] = [];
  private syncInProgress: boolean = false;
  private readonly maxRetries: number = 3;
  private readonly retryDelay: number = 5000; // 5 seconds

  // constructor is inherited from EventEmitter

  /**
   * Initialize offline service explicitly
   */
  public async initialize(): Promise<void> {
    // Load queued actions from storage
    await this.loadQueuedActions();

    // Monitor network status
    this.monitorNetworkStatus();

    // Start periodic sync
    this.startPeriodicSync();
  }

  /**
   * Monitor network status
   */
  private monitorNetworkStatus(): void {
    // Subscribe to network state changes
    NetInfo.addEventListener((state) => {
      const wasOnline = this.isOnline;
      this.isOnline = state.isConnected ?? false;

      if (wasOnline !== this.isOnline) {
        this.emit("networkStatusChanged", this.isOnline);

        if (this.isOnline) {
          // Network came back online, sync queued actions
          void this.syncQueuedActions();
        }
      }
    });

    // Store unsubscribe function for cleanup if needed
  }

  /**
   * Get current offline status
   */
  async getStatus(): Promise<OfflineStatus> {
    const networkState = await NetInfo.fetch();
    const isConnected = networkState.isConnected ?? false;

    return {
      isOnline: isConnected,
      isConnected,
      queuedActions: this.queuedActions.length,
      lastSyncTime: await this.getLastSyncTime(),
    };
  }

  /**
   * Check if device is online
   */
  async isDeviceOnline(): Promise<boolean> {
    const networkState = await NetInfo.fetch();
    return networkState.isConnected ?? false;
  }

  /**
   * Queue an action for later execution
   */
  async queueAction(
    type: QueuedAction["type"],
    action: string,
    payload: Record<string, unknown>
  ): Promise<string> {
    const queuedAction: QueuedAction = {
      id: `${Date.now()}-${Math.random().toString(36).substring(2, 11)}`,
      type,
      action,
      payload,
      timestamp: Date.now(),
      retries: 0,
      maxRetries: this.maxRetries,
    };

    this.queuedActions.push(queuedAction);
    await this.saveQueuedActions();

    this.emit("actionQueued", queuedAction);

    // Try to sync immediately if online
    if (await this.isDeviceOnline()) {
      this.syncQueuedActions();
    }

    return queuedAction.id;
  }

  /**
   * Execute a queued action
   */
  private async executeQueuedAction(action: QueuedAction): Promise<boolean> {
    try {
      let success = false;

      switch (action.type) {
        case "trade":
          if (action.action === "create") {
            await api.createTrade(action.payload);
            success = true;
          }
          break;

        case "bot_action":
          if (action.action === "start") {
            await api.startBot(action.payload.botId as string);
            success = true;
          } else if (action.action === "stop") {
            await api.stopBot(action.payload.botId as string);
            success = true;
          }
          break;

        case "withdrawal":
          // Handle withdrawal (if endpoint exists)
          success = true;
          break;

        case "deposit":
          // Handle deposit (if endpoint exists)
          success = true;
          break;

        default:
          console.warn(`Unknown action type: ${action.type as string}`);
      }

      if (success) {
        // Remove from queue
        this.queuedActions = this.queuedActions.filter((a) => a.id !== action.id);
        await this.saveQueuedActions();
        this.emit("actionExecuted", action);
        return true;
      }

      return false;
    } catch (error) {
      console.error(`Error executing queued action ${action.id}:`, error);

      // Increment retry count
      action.retries += 1;

      if (action.retries >= (action.maxRetries ?? this.maxRetries)) {
        // Max retries reached, remove from queue
        this.queuedActions = this.queuedActions.filter((a) => a.id !== action.id);
        await this.saveQueuedActions();
        this.emit("actionFailed", action, error);
        return false;
      }

      // Save updated retry count
      await this.saveQueuedActions();
      return false;
    }
  }

  /**
   * Sync all queued actions
   */
  async syncQueuedActions(): Promise<void> {
    if (this.syncInProgress) {
      return;
    }

    const isOnline = await this.isDeviceOnline();
    if (!isOnline || this.queuedActions.length === 0) {
      return;
    }

    this.syncInProgress = true;
    this.emit("syncStarted");

    try {
      const actionsToSync = [...this.queuedActions];

      for (const action of actionsToSync) {
        const success = await this.executeQueuedAction(action);

        if (!success) {
          // Wait before retrying
          await new Promise((resolve) => setTimeout(() => resolve(true), this.retryDelay));
        }
      }

      await this.setLastSyncTime(Date.now());
      this.emit("syncCompleted", {
        synced: actionsToSync.length - this.queuedActions.length,
        failed: this.queuedActions.length,
      });
    } catch (error) {
      console.error("Error syncing queued actions:", error);
      this.emit("syncError", error);
    } finally {
      this.syncInProgress = false;
    }
  }

  /**
   * Start periodic sync
   */
  private startPeriodicSync(): void {
    // Sync every 30 seconds when online
    setInterval(async () => {
      const isOnline = await this.isDeviceOnline();
      if (isOnline && this.queuedActions.length > 0) {
        this.syncQueuedActions();
      }
    }, 30000);
  }

  /**
   * Clear all queued actions
   */
  async clearQueuedActions(): Promise<void> {
    this.queuedActions = [];
    await this.saveQueuedActions();
    this.emit("queueCleared");
  }

  /**
   * Get queued actions
   */
  getQueuedActions(): QueuedAction[] {
    return [...this.queuedActions];
  }

  /**
   * Remove a specific queued action
   */
  async removeQueuedAction(actionId: string): Promise<boolean> {
    const initialLength = this.queuedActions.length;
    this.queuedActions = this.queuedActions.filter((a) => a.id !== actionId);

    if (this.queuedActions.length < initialLength) {
      await this.saveQueuedActions();
      this.emit("actionRemoved", actionId);
      return true;
    }

    return false;
  }

  /**
   * Save queued actions to storage
   */
  private async saveQueuedActions(): Promise<void> {
    try {
      await AsyncStorage.setItem("offline_queued_actions", JSON.stringify(this.queuedActions));
    } catch (error) {
      console.error("Error saving queued actions:", error);
    }
  }

  /**
   * Load queued actions from storage
   */
  private async loadQueuedActions(): Promise<void> {
    try {
      const stored = await AsyncStorage.getItem("offline_queued_actions");
      if (stored) {
        this.queuedActions = JSON.parse(stored);
      }
    } catch (error) {
      console.error("Error loading queued actions:", error);
      this.queuedActions = [];
    }
  }

  /**
   * Get last sync time
   */
  private async getLastSyncTime(): Promise<number | null> {
    try {
      const stored = await AsyncStorage.getItem("offline_last_sync_time");
      return stored ? Number.parseInt(stored, 10) : null;
    } catch {
      return null;
    }
  }

  /**
   * Set last sync time
   */
  private async setLastSyncTime(timestamp: number): Promise<void> {
    try {
      await AsyncStorage.setItem("offline_last_sync_time", timestamp.toString());
    } catch (error) {
      console.error("Error setting last sync time:", error);
    }
  }

  /**
   * Cache data for offline access
   */
  async cacheData(key: string, data: unknown, ttl?: number): Promise<void> {
    try {
      const cacheEntry = {
        data,
        timestamp: Date.now(),
        ttl: ttl ?? 3600000, // Default 1 hour
      };

      await AsyncStorage.setItem(`cache_${key}`, JSON.stringify(cacheEntry));
    } catch (error) {
      console.error(`Error caching data for key ${key}:`, error);
    }
  }

  /**
   * Get cached data
   */
  async getCachedData<T>(key: string): Promise<T | null> {
    try {
      const stored = await AsyncStorage.getItem(`cache_${key}`);
      if (!stored) {
        return null;
      }

      const cacheEntry = JSON.parse(stored);
      const age = Date.now() - cacheEntry.timestamp;

      if (age > cacheEntry.ttl) {
        // Cache expired
        await AsyncStorage.removeItem(`cache_${key}`);
        return null;
      }

      return cacheEntry.data as T;
    } catch (error) {
      console.error(`Error getting cached data for key ${key}:`, error);
      return null;
    }
  }

  /**
   * Clear cached data
   */
  async clearCache(key?: string): Promise<void> {
    try {
      if (key) {
        await AsyncStorage.removeItem(`cache_${key}`);
      } else {
        // Clear all cache
        const keys = await AsyncStorage.getAllKeys();
        const cacheKeys = keys.filter((k) => k.startsWith("cache_"));
        await AsyncStorage.multiRemove(cacheKeys);
      }
    } catch (error) {
      console.error("Error clearing cache:", error);
    }
  }
}

export const offlineService = new OfflineService();
export default offlineService;
