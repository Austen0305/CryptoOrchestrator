/**
 * Offline Storage Utilities
 * Provides IndexedDB wrapper for storing data offline and syncing when online.
 */

interface OfflineAction {
  id: string;
  type: string;
  payload: any;
  timestamp: number;
  retries: number;
}

class OfflineStorage {
  private dbName = 'cryptoorchestrator-offline';
  private version = 1;
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(this.dbName, this.version);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;

        // Pending actions store
        if (!db.objectStoreNames.contains('pendingActions')) {
          const actionsStore = db.createObjectStore('pendingActions', {
            keyPath: 'id',
          });
          actionsStore.createIndex('timestamp', 'timestamp', { unique: false });
          actionsStore.createIndex('type', 'type', { unique: false });
        }

        // Cache data store
        if (!db.objectStoreNames.contains('cacheData')) {
          const cacheStore = db.createObjectStore('cacheData', {
            keyPath: 'key',
          });
          cacheStore.createIndex('timestamp', 'timestamp', { unique: false });
        }

        // Offline trades store
        if (!db.objectStoreNames.contains('offlineTrades')) {
          const tradesStore = db.createObjectStore('offlineTrades', {
            keyPath: 'id',
          });
          tradesStore.createIndex('timestamp', 'timestamp', { unique: false });
          tradesStore.createIndex('synced', 'synced', { unique: false });
        }
      };
    });
  }

  async addPendingAction(action: Omit<OfflineAction, 'id' | 'timestamp' | 'retries'>): Promise<string> {
    if (!this.db) await this.init();

    const fullAction: OfflineAction = {
      ...action,
      id: crypto.randomUUID(),
      timestamp: Date.now(),
      retries: 0,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');
      const request = store.add(fullAction);

      request.onsuccess = () => resolve(fullAction.id);
      request.onerror = () => reject(request.error);
    });
  }

  async getPendingActions(): Promise<OfflineAction[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readonly');
      const store = transaction.objectStore('pendingActions');
      const request = store.getAll();

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async removePendingAction(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');
      const request = store.delete(id);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async incrementRetry(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['pendingActions'], 'readwrite');
      const store = transaction.objectStore('pendingActions');
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const action = getRequest.result;
        if (action) {
          action.retries += 1;
          const putRequest = store.put(action);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        } else {
          resolve();
        }
      };
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  async saveOfflineTrade(trade: any): Promise<string> {
    if (!this.db) await this.init();

    const tradeData = {
      ...trade,
      id: trade.id || crypto.randomUUID(),
      timestamp: Date.now(),
      synced: false,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['offlineTrades'], 'readwrite');
      const store = transaction.objectStore('offlineTrades');
      const request = store.put(tradeData);

      request.onsuccess = () => resolve(tradeData.id);
      request.onerror = () => reject(request.error);
    });
  }

  async getOfflineTrades(): Promise<any[]> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['offlineTrades'], 'readonly');
      const store = transaction.objectStore('offlineTrades');
      const index = store.index('synced');
      const request = index.getAll(null); // Get unsynced trades (null = false in IndexedDB boolean index)

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => reject(request.error);
    });
  }

  async markTradeSynced(id: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['offlineTrades'], 'readwrite');
      const store = transaction.objectStore('offlineTrades');
      const getRequest = store.get(id);

      getRequest.onsuccess = () => {
        const trade = getRequest.result;
        if (trade) {
          trade.synced = true;
          const putRequest = store.put(trade);
          putRequest.onsuccess = () => resolve();
          putRequest.onerror = () => reject(putRequest.error);
        } else {
          resolve();
        }
      };
      getRequest.onerror = () => reject(getRequest.error);
    });
  }

  async cacheData(key: string, data: any, ttl?: number): Promise<void> {
    if (!this.db) await this.init();

    const cacheEntry = {
      key,
      data,
      timestamp: Date.now(),
      expiresAt: ttl ? Date.now() + ttl : null,
    };

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cacheData'], 'readwrite');
      const store = transaction.objectStore('cacheData');
      const request = store.put(cacheEntry);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getCachedData(key: string): Promise<any | null> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cacheData'], 'readonly');
      const store = transaction.objectStore('cacheData');
      const request = store.get(key);

      request.onsuccess = () => {
        const entry = request.result;
        if (!entry) {
          resolve(null);
          return;
        }

        // Check expiration
        if (entry.expiresAt && Date.now() > entry.expiresAt) {
          // Expired, remove and return null
          this.removeCachedData(key);
          resolve(null);
          return;
        }

        resolve(entry.data);
      };
      request.onerror = () => reject(request.error);
    });
  }

  async removeCachedData(key: string): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cacheData'], 'readwrite');
      const store = transaction.objectStore('cacheData');
      const request = store.delete(key);

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async clearExpiredCache(): Promise<number> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction(['cacheData'], 'readwrite');
      const store = transaction.objectStore('cacheData');
      const index = store.index('timestamp');
      const request = index.openCursor();

      let deletedCount = 0;

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest<IDBCursorWithValue>).result;
        if (cursor) {
          const entry = cursor.value;
          if (entry.expiresAt && Date.now() > entry.expiresAt) {
            cursor.delete();
            deletedCount++;
          }
          cursor.continue();
        } else {
          resolve(deletedCount);
        }
      };
      request.onerror = () => reject(request.error);
    });
  }
}

export const offlineStorage = new OfflineStorage();
