import { DeviceInfo } from '../types';

export class DeviceCollector {
  public static async collect(): Promise<DeviceInfo> {
    try {
      const userAgent = navigator.userAgent;
      const platform = navigator.platform;
      
      return {
        type: this.getDeviceType(),
        screen: {
          width: window.screen.width,
          height: window.screen.height,
          pixelRatio: window.devicePixelRatio || 1
        },
        browser: this.getBrowserInfo(userAgent),
        os: this.getOSInfo(userAgent, platform),
        hardware: {
          cpuCores: navigator.hardwareConcurrency || 1,
          memory: (navigator as any).deviceMemory || 0,
          platform: platform
        }
      };
    } catch (error) {
      // Return minimal info on error
      return {
        type: 'unknown',
        screen: {
          width: window.innerWidth,
          height: window.innerHeight,
          pixelRatio: 1
        },
        browser: {
          name: 'unknown',
          version: 'unknown',
          engine: 'unknown'
        },
        os: {
          name: 'unknown',
          version: 'unknown'
        },
        hardware: {
          cpuCores: 1,
          memory: 0,
          platform: 'unknown'
        }
      };
    }
  }

  private static getDeviceType(): DeviceInfo['type'] {
    const width = window.innerWidth;
    const userAgent = navigator.userAgent.toLowerCase();

    // Check for mobile devices
    if (/mobile|android|iphone|ipod|blackberry|iemobile|opera mini/i.test(userAgent)) {
      return 'mobile';
    }

    // Check for tablets
    if (/ipad|tablet|playbook|silk/i.test(userAgent) || 
        (width >= 768 && width <= 1024 && 'ontouchstart' in window)) {
      return 'tablet';
    }

    // Desktop
    if (width > 1024) {
      return 'desktop';
    }

    return 'unknown';
  }

  private static getBrowserInfo(userAgent: string): DeviceInfo['browser'] {
    let name = 'unknown';
    let version = 'unknown';
    let engine = 'unknown';

    // Detect browser name and version
    if (userAgent.includes('Firefox/')) {
      name = 'Firefox';
      version = this.extractVersion(userAgent, 'Firefox/');
      engine = 'Gecko';
    } else if (userAgent.includes('Edg/')) {
      name = 'Edge';
      version = this.extractVersion(userAgent, 'Edg/');
      engine = 'Blink';
    } else if (userAgent.includes('Chrome/')) {
      name = 'Chrome';
      version = this.extractVersion(userAgent, 'Chrome/');
      engine = 'Blink';
    } else if (userAgent.includes('Safari/') && !userAgent.includes('Chrome')) {
      name = 'Safari';
      version = this.extractVersion(userAgent, 'Version/');
      engine = 'WebKit';
    } else if (userAgent.includes('Opera/') || userAgent.includes('OPR/')) {
      name = 'Opera';
      version = this.extractVersion(userAgent, userAgent.includes('OPR/') ? 'OPR/' : 'Opera/');
      engine = 'Blink';
    }

    return { name, version, engine };
  }

  private static getOSInfo(userAgent: string, platform: string): DeviceInfo['os'] {
    let name = 'unknown';
    let version = 'unknown';

    if (platform.startsWith('Win')) {
      name = 'Windows';
      if (userAgent.includes('Windows NT 10.0')) version = '10';
      else if (userAgent.includes('Windows NT 6.3')) version = '8.1';
      else if (userAgent.includes('Windows NT 6.2')) version = '8';
      else if (userAgent.includes('Windows NT 6.1')) version = '7';
    } else if (platform.startsWith('Mac')) {
      name = 'macOS';
      const match = userAgent.match(/Mac OS X ([\d_]+)/);
      if (match) {
        version = match[1].replace(/_/g, '.');
      }
    } else if (/Android/.test(userAgent)) {
      name = 'Android';
      const match = userAgent.match(/Android ([\d.]+)/);
      if (match) version = match[1];
    } else if (/iPhone|iPad|iPod/.test(userAgent)) {
      name = 'iOS';
      const match = userAgent.match(/OS ([\d_]+)/);
      if (match) {
        version = match[1].replace(/_/g, '.');
      }
    } else if (/Linux/.test(platform)) {
      name = 'Linux';
    }

    return { name, version };
  }

  private static extractVersion(userAgent: string, searchString: string): string {
    const index = userAgent.indexOf(searchString);
    if (index === -1) return 'unknown';
    
    const version = userAgent.substring(index + searchString.length).split(/[ ;)]/)[0];
    return version || 'unknown';
  }
}