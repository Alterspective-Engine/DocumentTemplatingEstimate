import { AnalyticsEvent, VisitorSession } from '../types';

export class StorageAdapter {
  private storageType: 'indexeddb' | 'localStorage' | 'memory';
  private memoryStore: Map<string, any> = new Map();
  private db: IDBDatabase | null = null;
  private readonly DB_NAME = 'analytics_db';
  private readonly DB_VERSION = 1;
  private readonly EVENTS_STORE = 'events';
  private readonly DATA_STORE = 'data';

  constructor(storageType: 'indexeddb' | 'localStorage' | 'memory') {
    this.storageType = storageType;
  }

  public async initialize(): Promise<void> {
    if (this.storageType === 'indexeddb') {
      await this.initIndexedDB();
    }
  }

  private async initIndexedDB(): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        const request = indexedDB.open(this.DB_NAME, this.DB_VERSION);

        request.onerror = () => {
          console.error('Failed to open IndexedDB, falling back to localStorage');
          this.storageType = 'localStorage';
          resolve();
        };

        request.onsuccess = (event) => {
          this.db = (event.target as IDBOpenDBRequest).result;
          resolve();
        };

        request.onupgradeneeded = (event) => {
          const db = (event.target as IDBOpenDBRequest).result;

          // Create events store
          if (!db.objectStoreNames.contains(this.EVENTS_STORE)) {
            const eventsStore = db.createObjectStore(this.EVENTS_STORE, { 
              keyPath: 'eventId',
              autoIncrement: false
            });
            eventsStore.createIndex('timestamp', 'timestamp', { unique: false });
            eventsStore.createIndex('sessionId', 'sessionId', { unique: false });
            eventsStore.createIndex('type', 'type', { unique: false });
          }

          // Create general data store
          if (!db.objectStoreNames.contains(this.DATA_STORE)) {
            db.createObjectStore(this.DATA_STORE);
          }
        };
      } catch (error) {
        console.error('IndexedDB not available, falling back to localStorage');
        this.storageType = 'localStorage';
        resolve();
      }
    });
  }

  public async set(key: string, value: any): Promise<void> {
    switch (this.storageType) {
      case 'indexeddb':
        return this.setIndexedDB(key, value);
      case 'localStorage':
        return this.setLocalStorage(key, value);
      case 'memory':
        this.memoryStore.set(key, value);
        return Promise.resolve();
    }
  }

  public async get(key: string): Promise<any> {
    switch (this.storageType) {
      case 'indexeddb':
        return this.getIndexedDB(key);
      case 'localStorage':
        return this.getLocalStorage(key);
      case 'memory':
        return Promise.resolve(this.memoryStore.get(key));
    }
  }

  private async setIndexedDB(key: string, value: any): Promise<void> {
    return new Promise((resolve, reject) => {
      if (!this.db) {
        this.setLocalStorage(key, value);
        resolve();
        return;
      }

      const transaction = this.db.transaction([this.DATA_STORE], 'readwrite');
      const store = transaction.objectStore(this.DATA_STORE);
      const request = store.put(value, key);

      request.onsuccess = () => resolve();
      request.onerror = () => {
        console.error('Failed to set in IndexedDB, falling back to localStorage');
        this.setLocalStorage(key, value);
        resolve();
      };
    });
  }

  private async getIndexedDB(key: string): Promise<any> {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve(this.getLocalStorage(key));
        return;
      }

      const transaction = this.db.transaction([this.DATA_STORE], 'readonly');
      const store = transaction.objectStore(this.DATA_STORE);
      const request = store.get(key);

      request.onsuccess = () => resolve(request.result);
      request.onerror = () => {
        console.error('Failed to get from IndexedDB, falling back to localStorage');
        resolve(this.getLocalStorage(key));
      };
    });
  }

  private setLocalStorage(key: string, value: any): void {
    try {
      localStorage.setItem(`analytics_${key}`, JSON.stringify(value));
    } catch (error) {
      // QuotaExceededError or other storage errors
      console.error('Failed to save to localStorage:', error);
      // Fall back to memory
      this.memoryStore.set(key, value);
    }
  }

  private getLocalStorage(key: string): any {
    try {
      const item = localStorage.getItem(`analytics_${key}`);
      return item ? JSON.parse(item) : null;
    } catch (error) {
      // Fallback to memory
      return this.memoryStore.get(key);
    }
  }

  public async addEvents(events: AnalyticsEvent[]): Promise<void> {
    switch (this.storageType) {
      case 'indexeddb':
        return this.addEventsIndexedDB(events);
      case 'localStorage':
        return this.addEventsLocalStorage(events);
      case 'memory':
        return this.addEventsMemory(events);
    }
  }

  private async addEventsIndexedDB(events: AnalyticsEvent[]): Promise<void> {
    return new Promise((resolve) => {
      if (!this.db) {
        this.addEventsLocalStorage(events);
        resolve();
        return;
      }

      const transaction = this.db.transaction([this.EVENTS_STORE], 'readwrite');
      const store = transaction.objectStore(this.EVENTS_STORE);

      events.forEach(event => {
        store.add(event).onerror = () => {
          // Ignore duplicate key errors
        };
      });

      transaction.oncomplete = () => {
        this.cleanupOldEvents();
        resolve();
      };

      transaction.onerror = () => {
        console.error('Failed to add events to IndexedDB, falling back to localStorage');
        this.addEventsLocalStorage(events);
        resolve();
      };
    });
  }

  private async addEventsLocalStorage(events: AnalyticsEvent[]): Promise<void> {
    try {
      const stored = localStorage.getItem('analytics_events');
      const existingEvents = stored ? JSON.parse(stored) : [];
      
      const allEvents = [...existingEvents, ...events];
      
      // Keep only last 1000 events to prevent storage overflow
      const trimmedEvents = allEvents.slice(-1000);
      
      localStorage.setItem('analytics_events', JSON.stringify(trimmedEvents));
    } catch (error) {
      // Fall back to memory
      this.addEventsMemory(events);
    }
  }

  private async addEventsMemory(events: AnalyticsEvent[]): Promise<void> {
    const existingEvents = this.memoryStore.get('events') || [];
    const allEvents = [...existingEvents, ...events];
    
    // Keep only last 500 events in memory
    const trimmedEvents = allEvents.slice(-500);
    
    this.memoryStore.set('events', trimmedEvents);
  }

  public async getEvents(limit?: number): Promise<AnalyticsEvent[]> {
    switch (this.storageType) {
      case 'indexeddb':
        return this.getEventsIndexedDB(limit);
      case 'localStorage':
        return this.getEventsLocalStorage(limit);
      case 'memory':
        return this.getEventsMemory(limit);
    }
  }

  private async getEventsIndexedDB(limit?: number): Promise<AnalyticsEvent[]> {
    return new Promise((resolve) => {
      if (!this.db) {
        resolve(this.getEventsLocalStorage(limit));
        return;
      }

      const transaction = this.db.transaction([this.EVENTS_STORE], 'readonly');
      const store = transaction.objectStore(this.EVENTS_STORE);
      const index = store.index('timestamp');
      
      const events: AnalyticsEvent[] = [];
      let count = 0;
      const maxCount = limit || Infinity;

      const request = index.openCursor(null, 'prev'); // Most recent first

      request.onsuccess = (event) => {
        const cursor = (event.target as IDBRequest).result;
        
        if (cursor && count < maxCount) {
          events.push(cursor.value);
          count++;
          cursor.continue();
        } else {
          resolve(events);
        }
      };

      request.onerror = () => {
        console.error('Failed to get events from IndexedDB');
        resolve(this.getEventsLocalStorage(limit));
      };
    });
  }

  private async getEventsLocalStorage(limit?: number): Promise<AnalyticsEvent[]> {
    try {
      const stored = localStorage.getItem('analytics_events');
      const events = stored ? JSON.parse(stored) : [];
      
      if (limit) {
        return events.slice(-limit).reverse();
      }
      
      return events;
    } catch (error) {
      return this.getEventsMemory(limit);
    }
  }

  private async getEventsMemory(limit?: number): Promise<AnalyticsEvent[]> {
    const events = this.memoryStore.get('events') || [];
    
    if (limit) {
      return events.slice(-limit).reverse();
    }
    
    return events;
  }

  private async cleanupOldEvents(): Promise<void> {
    if (!this.db) return;

    const retentionMs = 90 * 24 * 60 * 60 * 1000; // 90 days
    const cutoffTime = Date.now() - retentionMs;

    const transaction = this.db.transaction([this.EVENTS_STORE], 'readwrite');
    const store = transaction.objectStore(this.EVENTS_STORE);
    const index = store.index('timestamp');
    
    const range = IDBKeyRange.upperBound(cutoffTime);
    const request = index.openCursor(range);

    request.onsuccess = (event) => {
      const cursor = (event.target as IDBRequest).result;
      
      if (cursor) {
        store.delete(cursor.primaryKey);
        cursor.continue();
      }
    };
  }

  public async clear(): Promise<void> {
    switch (this.storageType) {
      case 'indexeddb':
        if (this.db) {
          const transaction = this.db.transaction([this.EVENTS_STORE, this.DATA_STORE], 'readwrite');
          transaction.objectStore(this.EVENTS_STORE).clear();
          transaction.objectStore(this.DATA_STORE).clear();
        }
        break;
      case 'localStorage':
        Object.keys(localStorage).forEach(key => {
          if (key.startsWith('analytics_')) {
            localStorage.removeItem(key);
          }
        });
        break;
      case 'memory':
        this.memoryStore.clear();
        break;
    }
  }
}