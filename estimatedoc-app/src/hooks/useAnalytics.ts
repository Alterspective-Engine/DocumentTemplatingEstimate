import { useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { AnalyticsService } from '../services/analytics/AnalyticsService';
import { UserAction } from '../services/analytics/types';

// Initialize analytics service singleton
const analytics = AnalyticsService.getInstance();

// Initialize analytics on app start
let isInitialized = false;
const initPromise = (async () => {
  if (!isInitialized) {
    await analytics.initialize({
      debugMode: import.meta.env.DEV,
      samplingRate: import.meta.env.DEV ? 1.0 : 0.5,
      respectDoNotTrack: true,
      anonymizeIp: true
    });
    isInitialized = true;
  }
})();

export function useAnalytics() {
  const location = useLocation();
  const previousPath = useRef<string>('');

  // Track page views on route change
  useEffect(() => {
    const currentPath = location.pathname + location.search;
    
    if (currentPath !== previousPath.current) {
      previousPath.current = currentPath;
      
      initPromise.then(() => {
        analytics.trackPageView(window.location.href);
      });
    }
  }, [location]);

  const trackAction = useCallback((action: UserAction) => {
    initPromise.then(() => {
      analytics.trackAction(action);
    });
  }, []);

  const trackClick = useCallback((target: string, context?: any) => {
    trackAction({
      type: 'click',
      target,
      timestamp: Date.now(),
      context
    });
  }, [trackAction]);

  const trackSearch = useCallback((query: string, resultCount: number) => {
    initPromise.then(() => {
      analytics.trackSearch(query, resultCount);
    });
  }, []);

  const trackDocumentView = useCallback((documentId: string, documentName: string) => {
    initPromise.then(() => {
      analytics.trackDocumentView(documentId, documentName);
    });
  }, []);

  const trackCalculatorUsage = useCallback((settings: any) => {
    initPromise.then(() => {
      analytics.trackCalculatorUsage(settings);
    });
  }, []);

  const trackFilter = useCallback((filterType: string, value: any) => {
    trackAction({
      type: 'filter',
      target: filterType,
      value,
      timestamp: Date.now()
    });
  }, [trackAction]);

  const trackSort = useCallback((sortField: string, direction: string) => {
    trackAction({
      type: 'sort',
      target: sortField,
      value: direction,
      timestamp: Date.now()
    });
  }, [trackAction]);

  const trackExport = useCallback((format: string, count: number) => {
    trackAction({
      type: 'export',
      target: format,
      value: { count },
      timestamp: Date.now()
    });
  }, [trackAction]);

  const setUser = useCallback(async (userId: string, properties?: Record<string, any>) => {
    await initPromise;
    await analytics.setUser(userId, properties);
  }, []);

  const clearUser = useCallback(async () => {
    await initPromise;
    await analytics.clearUser();
  }, []);

  return {
    trackAction,
    trackClick,
    trackSearch,
    trackDocumentView,
    trackCalculatorUsage,
    trackFilter,
    trackSort,
    trackExport,
    setUser,
    clearUser
  };
}

// Hook for tracking component visibility
export function useTrackVisibility(
  ref: React.RefObject<HTMLElement>,
  componentName: string,
  threshold = 0.5
) {
  const hasBeenVisible = useRef(false);
  const { trackAction } = useAnalytics();

  useEffect(() => {
    if (!ref.current) return;

    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting && !hasBeenVisible.current) {
            hasBeenVisible.current = true;
            
            trackAction({
              type: 'action',
              target: `${componentName}_visible`,
              timestamp: Date.now(),
              context: {
                intersectionRatio: entry.intersectionRatio
              }
            });
          }
        });
      },
      { threshold }
    );

    observer.observe(ref.current);

    return () => {
      observer.disconnect();
    };
  }, [ref, componentName, threshold, trackAction]);
}

// Hook for tracking time spent
export function useTimeTracking(componentName: string) {
  const startTime = useRef<number>(Date.now());
  const { trackAction } = useAnalytics();

  useEffect(() => {
    startTime.current = Date.now();

    return () => {
      const timeSpent = Date.now() - startTime.current;
      
      if (timeSpent > 1000) { // Only track if more than 1 second
        trackAction({
          type: 'action',
          target: `${componentName}_time_spent`,
          value: timeSpent,
          timestamp: Date.now()
        });
      }
    };
  }, [componentName, trackAction]);
}

// Hook for tracking errors
export function useErrorTracking() {
  useEffect(() => {
    const handleError = (event: ErrorEvent) => {
      // The analytics service already handles this globally
      // This hook is for component-specific error handling
    };

    const handleUnhandledRejection = (event: PromiseRejectionEvent) => {
      initPromise.then(() => {
        const errorData = {
          message: event.reason?.message || String(event.reason),
          stack: event.reason?.stack,
          url: window.location.href,
          userAgent: navigator.userAgent
        };

        analytics['addEvent']('error', errorData);
      });
    };

    window.addEventListener('unhandledrejection', handleUnhandledRejection);

    return () => {
      window.removeEventListener('unhandledrejection', handleUnhandledRejection);
    };
  }, []);
}

// Hook for tracking performance metrics
export function usePerformanceTracking() {
  useEffect(() => {
    // Track Core Web Vitals when they become available
    if ('PerformanceObserver' in window) {
      try {
        // First Contentful Paint
        const paintObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (entry.name === 'first-contentful-paint') {
              initPromise.then(() => {
                analytics['trackPerformance']('FCP', entry.startTime);
              });
            }
          });
        });
        paintObserver.observe({ entryTypes: ['paint'] });

        // Time to First Byte
        const navigationObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry: any) => {
            if (entry.responseStart) {
              const ttfb = entry.responseStart - entry.requestStart;
              initPromise.then(() => {
                analytics['trackPerformance']('TTFB', ttfb);
              });
            }
          });
        });
        navigationObserver.observe({ entryTypes: ['navigation'] });

        return () => {
          paintObserver.disconnect();
          navigationObserver.disconnect();
        };
      } catch (error) {
        // Performance API not fully supported
      }
    }
  }, []);
}