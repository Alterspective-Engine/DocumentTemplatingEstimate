// Version configuration - automatically updated during build
export const APP_VERSION = {
  version: '0.4.0',
  buildTime: '2025-09-14T02:07:09.875Z',
  buildNumber: 'mfj21gkz', // Short unique identifier
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