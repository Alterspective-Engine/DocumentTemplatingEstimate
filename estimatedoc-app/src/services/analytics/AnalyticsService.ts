import { 
  AnalyticsEvent, 
  VisitorSession, 
  DeviceInfo, 
  NetworkInfo, 
  LocationInfo,
  PageView,
  UserAction,
  AnalyticsConfig,
  ConsentState
} from './types';
import { DeviceCollector } from './collectors/DeviceCollector';
import { NetworkCollector } from './collectors/NetworkCollector';
import { LocationCollector } from './collectors/LocationCollector';
import { PrivacyManager } from './PrivacyManager';
import { StorageAdapter } from './storage/StorageAdapter';

export class AnalyticsService {
  private static instance: AnalyticsService;
  private config: AnalyticsConfig;
  private session: VisitorSession | null = null;
  private eventQueue: AnalyticsEvent[] = [];
  private flushTimer: NodeJS.Timeout | null = null;
  private privacyManager: PrivacyManager;
  private storage: StorageAdapter;
  private deviceInfo: DeviceInfo | null = null;
  private networkInfo: NetworkInfo | null = null;
  private locationInfo: LocationInfo | null = null;
  private pageStartTime: number = 0;
  private currentPageUrl: string = '';
  private isInitialized: boolean = false;

  private constructor() {
    this.config = {
      enabled: true,
      debugMode: false,
      samplingRate: 1.0,
      batchSize: 10,
      flushInterval: 30000, // 30 seconds
      sessionTimeout: 1800000, // 30 minutes
      storageType: 'indexeddb',
      apiEndpoint: import.meta.env.VITE_ANALYTICS_API_URL || 'http://localhost:3001/api/analytics/events',
      respectDoNotTrack: true,
      anonymizeIp: true,
      retentionDays: 90
    };

    this.privacyManager = new PrivacyManager();
    this.storage = new StorageAdapter(this.config.storageType);
  }

  public static getInstance(): AnalyticsService {
    if (!AnalyticsService.instance) {
      AnalyticsService.instance = new AnalyticsService();
    }
    return AnalyticsService.instance;
  }

  public async initialize(config?: Partial<AnalyticsConfig>): Promise<void> {
    try {
      // Merge config
      if (config) {
        this.config = { ...this.config, ...config };
      }

      // Check Do Not Track
      if (this.config.respectDoNotTrack && this.isDoNotTrackEnabled()) {
        this.config.enabled = false;
        console.log('Analytics disabled: Do Not Track is enabled');
        return;
      }

      // Check consent
      const consent = await this.privacyManager.getConsent();
      if (!consent.analytics) {
        this.config.enabled = false;
        console.log('Analytics disabled: User consent not given');
        return;
      }

      // Initialize storage
      await this.storage.initialize();

      // Collect device info (once per session)
      this.deviceInfo = await DeviceCollector.collect();

      // Collect network info (updates periodically)
      this.networkInfo = await NetworkCollector.collect();
      this.startNetworkMonitoring();

      // Collect location info (once per session)
      this.locationInfo = await LocationCollector.collect(this.config.anonymizeIp);

      // Initialize or restore session
      await this.initializeSession();

      // Start flush timer
      this.startFlushTimer();

      // Add event listeners
      this.attachEventListeners();

      // Track initial page view
      this.trackPageView();

      this.isInitialized = true;
      
      if (this.config.debugMode) {
        console.log('Analytics initialized', {
          session: this.session,
          device: this.deviceInfo,
          network: this.networkInfo,
          location: this.locationInfo
        });
      }
    } catch (error) {
      console.error('Failed to initialize analytics:', error);
      // Fail silently, don't break the app
      this.config.enabled = false;
    }
  }

  private isDoNotTrackEnabled(): boolean {
    return navigator.doNotTrack === '1' || 
           (window as any).doNotTrack === '1' ||
           navigator.doNotTrack === 'yes';
  }

  private async initializeSession(): Promise<void> {
    // Try to restore existing session
    const storedSession = await this.storage.get('session');
    
    if (storedSession && this.isSessionValid(storedSession)) {
      this.session = storedSession;
      this.session.lastActivity = Date.now();
    } else {
      // Create new session
      this.session = {
        sessionId: this.generateId(),
        visitorId: await this.getOrCreateVisitorId(),
        startTime: Date.now(),
        lastActivity: Date.now(),
        pageViews: 0,
        isAuthenticated: false
      };
    }

    await this.storage.set('session', this.session);
  }

  private isSessionValid(session: VisitorSession): boolean {
    const now = Date.now();
    return (now - session.lastActivity) < this.config.sessionTimeout;
  }

  private async getOrCreateVisitorId(): Promise<string> {
    let visitorId = await this.storage.get('visitorId');
    
    if (!visitorId) {
      visitorId = this.generateId();
      await this.storage.set('visitorId', visitorId);
    }
    
    return visitorId;
  }

  private generateId(): string {
    return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
  }

  private startNetworkMonitoring(): void {
    // Update network info every 60 seconds
    setInterval(async () => {
      if (this.config.enabled) {
        this.networkInfo = await NetworkCollector.collect();
      }
    }, 60000);
  }

  private startFlushTimer(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }

    this.flushTimer = setInterval(() => {
      this.flush();
    }, this.config.flushInterval);
  }

  private attachEventListeners(): void {
    // Page visibility change
    document.addEventListener('visibilitychange', () => {
      if (document.hidden) {
        this.trackPageExit('close');
        this.flush();
      }
    });

    // Before unload
    window.addEventListener('beforeunload', () => {
      this.trackPageExit('close');
      this.flush();
    });

    // Error tracking
    window.addEventListener('error', (event) => {
      this.trackError(event);
    });

    // Performance tracking
    if ('PerformanceObserver' in window) {
      this.observePerformance();
    }

    // Click tracking
    document.addEventListener('click', (event) => {
      this.trackClick(event);
    }, true);
  }

  private observePerformance(): void {
    try {
      // Largest Contentful Paint
      const lcpObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        const lastEntry = entries[entries.length - 1];
        this.trackPerformance('LCP', lastEntry.startTime);
      });
      lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });

      // First Input Delay
      const fidObserver = new PerformanceObserver((list) => {
        const entries = list.getEntries();
        entries.forEach((entry: any) => {
          this.trackPerformance('FID', entry.processingStart - entry.startTime);
        });
      });
      fidObserver.observe({ entryTypes: ['first-input'] });

      // Cumulative Layout Shift
      let clsValue = 0;
      const clsObserver = new PerformanceObserver((list) => {
        for (const entry of list.getEntries()) {
          if (!(entry as any).hadRecentInput) {
            clsValue += (entry as any).value;
          }
        }
        this.trackPerformance('CLS', clsValue);
      });
      clsObserver.observe({ entryTypes: ['layout-shift'] });
    } catch (error) {
      // Performance API not fully supported
    }
  }

  public trackPageView(url?: string): void {
    if (!this.config.enabled || !this.session) return;

    // Track exit of previous page
    if (this.currentPageUrl) {
      this.trackPageExit('navigation');
    }

    const pageUrl = url || window.location.href;
    this.currentPageUrl = pageUrl;
    this.pageStartTime = Date.now();

    if (this.session) {
      this.session.pageViews++;
      this.session.lastActivity = Date.now();
    }

    const pageView: PageView = {
      url: pageUrl,
      title: document.title,
      timestamp: Date.now(),
      duration: 0,
      scrollDepth: 0,
      referrer: document.referrer,
      exitType: 'navigation'
    };

    this.addEvent('pageview', pageView);
  }

  private trackPageExit(exitType: PageView['exitType']): void {
    if (!this.pageStartTime) return;

    const duration = Date.now() - this.pageStartTime;
    const scrollDepth = this.calculateScrollDepth();

    // Update the last pageview event with exit data
    const lastPageView = this.eventQueue
      .filter(e => e.type === 'pageview')
      .pop();

    if (lastPageView && lastPageView.data) {
      (lastPageView.data as PageView).duration = duration;
      (lastPageView.data as PageView).scrollDepth = scrollDepth;
      (lastPageView.data as PageView).exitType = exitType;
    }
  }

  private calculateScrollDepth(): number {
    const windowHeight = window.innerHeight;
    const documentHeight = document.documentElement.scrollHeight;
    const scrollTop = window.pageYOffset || document.documentElement.scrollTop;
    const scrollableHeight = documentHeight - windowHeight;
    
    if (scrollableHeight <= 0) return 100;
    
    return Math.min(100, Math.round((scrollTop / scrollableHeight) * 100));
  }

  public trackAction(action: UserAction): void {
    if (!this.config.enabled || !this.session) return;

    if (this.session) {
      this.session.lastActivity = Date.now();
    }

    this.addEvent('action', action);
  }

  private trackClick(event: MouseEvent): void {
    if (!this.config.enabled) return;

    const target = event.target as HTMLElement;
    if (!target) return;

    // Get meaningful identifiers
    const id = target.id;
    const className = target.className;
    const tagName = target.tagName;
    const text = target.textContent?.substring(0, 50);
    
    // Determine if this is a significant click
    const isSignificant = 
      tagName === 'BUTTON' ||
      tagName === 'A' ||
      target.onclick ||
      id?.includes('button') ||
      className?.includes('button') ||
      className?.includes('link');

    if (isSignificant) {
      const action: UserAction = {
        type: 'click',
        target: id || className || `${tagName}:${text}`,
        timestamp: Date.now(),
        context: {
          tagName,
          id,
          className,
          href: (target as HTMLAnchorElement).href
        }
      };

      this.trackAction(action);
    }
  }

  private trackError(event: ErrorEvent): void {
    if (!this.config.enabled) return;

    const errorData = {
      message: event.message,
      stack: event.error?.stack,
      url: event.filename,
      line: event.lineno,
      column: event.colno,
      userAgent: navigator.userAgent
    };

    this.addEvent('error', errorData);
    this.flush(); // Flush errors immediately
  }

  private trackPerformance(metric: string, value: number): void {
    if (!this.config.enabled) return;

    let rating: 'good' | 'needs-improvement' | 'poor' = 'good';
    
    // Define thresholds based on Web Vitals
    switch (metric) {
      case 'LCP':
        rating = value <= 2500 ? 'good' : value <= 4000 ? 'needs-improvement' : 'poor';
        break;
      case 'FID':
        rating = value <= 100 ? 'good' : value <= 300 ? 'needs-improvement' : 'poor';
        break;
      case 'CLS':
        rating = value <= 0.1 ? 'good' : value <= 0.25 ? 'needs-improvement' : 'poor';
        break;
    }

    const perfData = {
      metric,
      value,
      rating
    };

    this.addEvent('performance', perfData);
  }

  public trackSearch(query: string, resultCount: number): void {
    const action: UserAction = {
      type: 'search',
      target: 'search_bar',
      value: { query: this.anonymizeSearchQuery(query), resultCount },
      timestamp: Date.now()
    };
    
    this.trackAction(action);
  }

  private anonymizeSearchQuery(query: string): string {
    // Remove potential PII from search queries
    return query.length > 50 ? query.substring(0, 50) + '...' : query;
  }

  public trackDocumentView(documentId: string, documentName: string): void {
    const action: UserAction = {
      type: 'document_view',
      target: documentId,
      value: { name: documentName },
      timestamp: Date.now()
    };
    
    this.trackAction(action);
  }

  public trackCalculatorUsage(settings: any): void {
    const action: UserAction = {
      type: 'calculator',
      target: 'calculator',
      value: { settingsChanged: true },
      timestamp: Date.now()
    };
    
    this.trackAction(action);
  }

  private addEvent(type: AnalyticsEvent['type'], data: any): void {
    if (!this.session) return;

    // Apply sampling
    if (Math.random() > this.config.samplingRate) return;

    const event: AnalyticsEvent = {
      eventId: this.generateId(),
      sessionId: this.session.sessionId,
      visitorId: this.session.visitorId,
      timestamp: Date.now(),
      type,
      data,
      device: this.deviceInfo || undefined,
      network: this.networkInfo || undefined,
      location: this.locationInfo || undefined
    };

    this.eventQueue.push(event);

    if (this.config.debugMode) {
      console.log('Analytics event:', event);
    }

    // Flush if queue is full
    if (this.eventQueue.length >= this.config.batchSize) {
      this.flush();
    }
  }

  public async flush(): Promise<void> {
    if (this.eventQueue.length === 0) return;

    const events = [...this.eventQueue];
    this.eventQueue = [];

    try {
      // Store events locally
      await this.storage.addEvents(events);

      // If API endpoint is configured, send to server
      if (this.config.apiEndpoint) {
        await this.sendToServer(events);
      }
    } catch (error) {
      // Re-queue events on failure
      this.eventQueue.unshift(...events);
      console.error('Failed to flush analytics:', error);
    }
  }

  private async sendToServer(events: AnalyticsEvent[]): Promise<void> {
    if (!this.config.apiEndpoint) return;

    try {
      const response = await fetch(this.config.apiEndpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ events })
      });

      if (!response.ok) {
        throw new Error(`Server returned ${response.status}`);
      }

      // Also update session on server
      if (this.session) {
        await fetch(this.config.apiEndpoint.replace('/events', '/session'), {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json'
          },
          body: JSON.stringify(this.session)
        });
      }
    } catch (error) {
      // Fail silently, events are still stored locally
      console.error('Failed to send analytics to server:', error);
    }
  }

  public async setUser(userId: string, properties?: Record<string, any>): Promise<void> {
    if (!this.session) return;

    this.session.isAuthenticated = true;
    this.session.userId = userId;
    
    await this.storage.set('session', this.session);

    const action: UserAction = {
      type: 'action',
      target: 'user_login',
      value: { userId, properties },
      timestamp: Date.now()
    };

    this.trackAction(action);
  }

  public async clearUser(): Promise<void> {
    if (!this.session) return;

    this.session.isAuthenticated = false;
    delete this.session.userId;
    
    await this.storage.set('session', this.session);
  }

  public async updateConsent(consent: ConsentState): Promise<void> {
    await this.privacyManager.updateConsent(consent);
    
    if (!consent.analytics) {
      // Disable tracking
      this.config.enabled = false;
      this.flush();
      
      // Clear stored data if requested
      if (!consent.functional) {
        await this.storage.clear();
      }
    } else {
      // Re-enable tracking
      this.config.enabled = true;
      await this.initialize();
    }
  }

  public async getStoredEvents(): Promise<AnalyticsEvent[]> {
    return await this.storage.getEvents();
  }

  public async clearStoredData(): Promise<void> {
    await this.storage.clear();
  }

  public destroy(): void {
    if (this.flushTimer) {
      clearInterval(this.flushTimer);
    }
    this.flush();
  }
}