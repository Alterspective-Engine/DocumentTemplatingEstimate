import { NetworkInfo } from '../types';

export class NetworkCollector {
  public static async collect(): Promise<NetworkInfo> {
    try {
      const connection = (navigator as any).connection || 
                        (navigator as any).mozConnection || 
                        (navigator as any).webkitConnection;

      if (connection) {
        return {
          type: this.getConnectionType(connection),
          downlink: connection.downlink || 0,
          rtt: connection.rtt || 0,
          saveData: connection.saveData || false,
          effectiveType: connection.effectiveType || 'unknown'
        };
      }

      // Fallback: estimate based on performance
      return this.estimateNetworkInfo();
    } catch (error) {
      return {
        type: 'unknown',
        downlink: 0,
        rtt: 0,
        saveData: false,
        effectiveType: 'unknown'
      };
    }
  }

  private static getConnectionType(connection: any): NetworkInfo['type'] {
    const type = connection.type;
    
    if (type === 'wifi') return 'wifi';
    if (type === 'ethernet') return 'ethernet';
    if (type === 'cellular') {
      const effectiveType = connection.effectiveType;
      if (effectiveType === '4g') return '4g';
      if (effectiveType === '3g') return '3g';
      if (effectiveType === '2g') return '2g';
      return '3g'; // Default cellular
    }
    
    // Try to infer from effectiveType
    const effectiveType = connection.effectiveType;
    if (effectiveType === '4g') return '4g';
    if (effectiveType === '3g') return '3g';
    if (effectiveType === '2g') return '2g';
    
    return 'unknown';
  }

  private static async estimateNetworkInfo(): Promise<NetworkInfo> {
    try {
      // Measure connection speed with a small request
      const startTime = performance.now();
      const testUrl = '/favicon.ico'; // Small file that should be cached
      
      await fetch(testUrl, { 
        method: 'HEAD',
        cache: 'no-cache'
      });
      
      const endTime = performance.now();
      const rtt = Math.round(endTime - startTime);

      // Estimate connection type based on RTT
      let type: NetworkInfo['type'] = 'unknown';
      let effectiveType = 'unknown';
      let downlink = 0;

      if (rtt < 50) {
        type = 'ethernet';
        effectiveType = '4g';
        downlink = 10; // Mbps
      } else if (rtt < 150) {
        type = 'wifi';
        effectiveType = '4g';
        downlink = 5;
      } else if (rtt < 300) {
        type = '4g';
        effectiveType = '4g';
        downlink = 2;
      } else if (rtt < 600) {
        type = '3g';
        effectiveType = '3g';
        downlink = 0.5;
      } else {
        type = '2g';
        effectiveType = '2g';
        downlink = 0.1;
      }

      return {
        type,
        downlink,
        rtt,
        saveData: false,
        effectiveType
      };
    } catch (error) {
      return {
        type: 'unknown',
        downlink: 0,
        rtt: 0,
        saveData: false,
        effectiveType: 'unknown'
      };
    }
  }

  public static async measureBandwidth(): Promise<number> {
    try {
      // Create a blob of known size (1MB)
      const size = 1024 * 1024; // 1MB
      const data = new Uint8Array(size);
      const blob = new Blob([data]);
      const url = URL.createObjectURL(blob);

      const startTime = performance.now();
      
      // Simulate download
      await fetch(url);
      
      const endTime = performance.now();
      const duration = (endTime - startTime) / 1000; // Convert to seconds
      
      URL.revokeObjectURL(url);
      
      // Calculate bandwidth in Mbps
      const bandwidth = (size * 8) / (duration * 1000000);
      
      return Math.round(bandwidth * 100) / 100;
    } catch (error) {
      return 0;
    }
  }
}