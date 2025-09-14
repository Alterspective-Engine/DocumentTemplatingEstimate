import type { ConsentState } from './types';

export class PrivacyManager {
  private static readonly CONSENT_KEY = 'analytics_consent';
  private static readonly CONSENT_VERSION = '1.0.0';
  
  public async getConsent(): Promise<ConsentState> {
    try {
      const stored = localStorage.getItem(PrivacyManager.CONSENT_KEY);
      
      if (stored) {
        const consent = JSON.parse(stored) as ConsentState;
        
        // Check if consent version is current
        if (consent.version === PrivacyManager.CONSENT_VERSION) {
          return consent;
        }
      }
      
      // Return default consent (opt-in by default for better UX, but can be changed)
      return this.getDefaultConsent();
    } catch (error) {
      return this.getDefaultConsent();
    }
  }

  public async updateConsent(consent: Partial<ConsentState>): Promise<void> {
    try {
      const current = await this.getConsent();
      
      const updated: ConsentState = {
        ...current,
        ...consent,
        timestamp: Date.now(),
        version: PrivacyManager.CONSENT_VERSION
      };
      
      localStorage.setItem(PrivacyManager.CONSENT_KEY, JSON.stringify(updated));
      
      // Dispatch event for other components to react
      window.dispatchEvent(new CustomEvent('consentChanged', { detail: updated }));
    } catch (error) {
      console.error('Failed to update consent:', error);
    }
  }

  public async revokeConsent(): Promise<void> {
    await this.updateConsent({
      analytics: false,
      performance: false,
      functional: false
    });
  }

  public hasConsent(type: keyof Omit<ConsentState, 'timestamp' | 'version'>): boolean {
    try {
      const stored = localStorage.getItem(PrivacyManager.CONSENT_KEY);
      if (stored) {
        const consent = JSON.parse(stored) as ConsentState;
        return consent[type] === true;
      }
    } catch (error) {
      // Silent fail
    }
    return false;
  }

  private getDefaultConsent(): ConsentState {
    return {
      analytics: true, // Can be changed to false for opt-out by default
      performance: true,
      functional: true,
      timestamp: Date.now(),
      version: PrivacyManager.CONSENT_VERSION
    };
  }

  public clearAllData(): void {
    // Clear all analytics-related data
    const keysToRemove = [
      PrivacyManager.CONSENT_KEY,
      'visitorId',
      'session',
      'analytics_events'
    ];
    
    keysToRemove.forEach(key => {
      localStorage.removeItem(key);
      sessionStorage.removeItem(key);
    });
    
    // Clear IndexedDB if it exists
    if ('indexedDB' in window) {
      indexedDB.deleteDatabase('analytics_db');
    }
    
    // Clear cookies
    document.cookie.split(';').forEach(cookie => {
      const eqPos = cookie.indexOf('=');
      const name = eqPos > -1 ? cookie.substr(0, eqPos).trim() : cookie.trim();
      if (name.startsWith('analytics_') || name.startsWith('_ga')) {
        document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
      }
    });
  }

  public exportUserData(): Promise<any> {
    return new Promise((resolve) => {
      const data: any = {};
      
      // Collect from localStorage
      ['visitorId', 'session', PrivacyManager.CONSENT_KEY].forEach(key => {
        const value = localStorage.getItem(key);
        if (value) {
          try {
            data[key] = JSON.parse(value);
          } catch {
            data[key] = value;
          }
        }
      });
      
      // Collect from IndexedDB
      if ('indexedDB' in window) {
        const request = indexedDB.open('analytics_db');
        
        request.onsuccess = (event) => {
          const db = (event.target as IDBOpenDBRequest).result;
          const transaction = db.transaction(['events'], 'readonly');
          const store = transaction.objectStore('events');
          const getAllRequest = store.getAll();
          
          getAllRequest.onsuccess = () => {
            data.events = getAllRequest.result;
            resolve(data);
          };
          
          getAllRequest.onerror = () => {
            resolve(data);
          };
        };
        
        request.onerror = () => {
          resolve(data);
        };
      } else {
        resolve(data);
      }
    });
  }
}