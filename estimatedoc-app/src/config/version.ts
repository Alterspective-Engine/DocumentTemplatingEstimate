// Version configuration - automatically updated during build
export const APP_VERSION = {
  version: '0.2.0',
  buildTime: '2025-09-13T02:36:53.316Z',
  buildNumber: 'mfhnnu10', // Short unique identifier
};

// Function to format version string
export const getVersionString = () => {
  const date = new Date(APP_VERSION.buildTime);
  const dateStr = date.toLocaleDateString('en-US', { 
    month: 'short', 
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
  return `v${APP_VERSION.version}-${APP_VERSION.buildNumber} (${dateStr})`;
};

// Short version for display
export const getShortVersion = () => {
  return `v${APP_VERSION.version}-${APP_VERSION.buildNumber}`;
};