export interface VisitorSession {
  sessionId: string;
  visitorId: string;
  startTime: number;
  lastActivity: number;
  pageViews: number;
  isAuthenticated: boolean;
  userId?: string;
}

export interface DeviceInfo {
  type: 'mobile' | 'tablet' | 'desktop' | 'unknown';
  screen: {
    width: number;
    height: number;
    pixelRatio: number;
  };
  browser: {
    name: string;
    version: string;
    engine: string;
  };
  os: {
    name: string;
    version: string;
  };
  hardware: {
    cpuCores: number;
    memory: number;
    platform: string;
  };
}

export interface NetworkInfo {
  type: 'wifi' | '4g' | '3g' | '2g' | 'ethernet' | 'unknown';
  downlink: number;
  rtt: number;
  saveData: boolean;
  effectiveType: string;
}

export interface LocationInfo {
  country?: string;
  region?: string;
  city?: string;
  timezone: string;
  language: string;
  ip?: string; // Will be hashed
}

export interface PageView {
  url: string;
  title: string;
  timestamp: number;
  duration: number;
  scrollDepth: number;
  referrer: string;
  exitType: 'navigation' | 'close' | 'external' | 'timeout';
}

export interface UserAction {
  type: 'click' | 'search' | 'filter' | 'sort' | 'calculator' | 'document_view' | 'export';
  target: string;
  value?: any;
  timestamp: number;
  context?: Record<string, any>;
}

export interface AnalyticsEvent {
  eventId: string;
  sessionId: string;
  visitorId: string;
  timestamp: number;
  type: 'pageview' | 'action' | 'error' | 'performance';
  data: PageView | UserAction | ErrorEvent | PerformanceEvent;
  device?: DeviceInfo;
  network?: NetworkInfo;
  location?: LocationInfo;
}

export interface ErrorEvent {
  message: string;
  stack?: string;
  url: string;
  line?: number;
  column?: number;
  userAgent: string;
}

export interface PerformanceEvent {
  metric: 'FCP' | 'LCP' | 'FID' | 'CLS' | 'TTFB';
  value: number;
  rating: 'good' | 'needs-improvement' | 'poor';
}

export interface ConsentState {
  analytics: boolean;
  performance: boolean;
  functional: boolean;
  timestamp: number;
  version: string;
}

export interface AnalyticsConfig {
  enabled: boolean;
  debugMode: boolean;
  samplingRate: number;
  batchSize: number;
  flushInterval: number;
  sessionTimeout: number;
  storageType: 'indexeddb' | 'localStorage' | 'memory';
  apiEndpoint?: string;
  respectDoNotTrack: boolean;
  anonymizeIp: boolean;
  retentionDays: number;
}