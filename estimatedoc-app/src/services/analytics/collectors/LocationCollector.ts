import { LocationInfo } from '../types';

export class LocationCollector {
  private static readonly IP_API_URL = 'https://ipapi.co/json/';
  
  public static async collect(anonymizeIp: boolean = true): Promise<LocationInfo> {
    try {
      const timezone = Intl.DateTimeFormat().resolvedOptions().timeZone;
      const language = navigator.language || 'en-US';
      
      // Try to get location from IP
      const ipLocation = await this.getIPLocation(anonymizeIp);
      
      return {
        ...ipLocation,
        timezone,
        language
      };
    } catch (error) {
      // Return minimal info on error
      return {
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone || 'UTC',
        language: navigator.language || 'en-US'
      };
    }
  }

  private static async getIPLocation(anonymizeIp: boolean): Promise<Partial<LocationInfo>> {
    try {
      // Use a free IP geolocation service
      const response = await fetch(this.IP_API_URL, {
        signal: AbortSignal.timeout(5000) // 5 second timeout
      });

      if (!response.ok) {
        throw new Error('Failed to fetch IP location');
      }

      const data = await response.json();
      
      return {
        country: data.country_name || undefined,
        region: data.region || undefined,
        city: data.city || undefined,
        ip: anonymizeIp ? this.anonymizeIP(data.ip) : data.ip
      };
    } catch (error) {
      // Try alternative method or return empty
      return {};
    }
  }

  private static anonymizeIP(ip: string): string {
    if (!ip) return '';
    
    // For IPv4, zero out last octet
    if (ip.includes('.')) {
      const parts = ip.split('.');
      if (parts.length === 4) {
        parts[3] = '0';
        return parts.join('.');
      }
    }
    
    // For IPv6, zero out last 80 bits
    if (ip.includes(':')) {
      const parts = ip.split(':');
      if (parts.length >= 4) {
        // Keep only first 3 segments
        return parts.slice(0, 3).join(':') + '::';
      }
    }
    
    return this.hashIP(ip);
  }

  private static hashIP(ip: string): string {
    // Simple hash function for IP
    let hash = 0;
    for (let i = 0; i < ip.length; i++) {
      const char = ip.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash; // Convert to 32bit integer
    }
    return `hashed_${Math.abs(hash).toString(36)}`;
  }

  public static async getTimezone(): Promise<string> {
    try {
      return Intl.DateTimeFormat().resolvedOptions().timeZone;
    } catch (error) {
      return 'UTC';
    }
  }

  public static getLanguages(): string[] {
    return navigator.languages ? [...navigator.languages] : [navigator.language || 'en-US'];
  }

  public static async estimateLocation(): Promise<Partial<LocationInfo>> {
    // Use timezone to estimate rough location
    const timezone = await this.getTimezone();
    const language = navigator.language;
    
    const locationMap: Record<string, Partial<LocationInfo>> = {
      'America/New_York': { country: 'United States', region: 'East Coast' },
      'America/Los_Angeles': { country: 'United States', region: 'West Coast' },
      'America/Chicago': { country: 'United States', region: 'Central' },
      'Europe/London': { country: 'United Kingdom', region: 'England' },
      'Europe/Paris': { country: 'France', region: 'Île-de-France' },
      'Europe/Berlin': { country: 'Germany', region: 'Berlin' },
      'Asia/Tokyo': { country: 'Japan', region: 'Kanto' },
      'Asia/Shanghai': { country: 'China', region: 'Shanghai' },
      'Australia/Sydney': { country: 'Australia', region: 'New South Wales' }
    };
    
    return locationMap[timezone] || {};
  }
}