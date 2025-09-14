import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

// Read current version
const versionFile = path.join(__dirname, '..', 'src', 'config', 'version.ts');
const packageFile = path.join(__dirname, '..', 'package.json');

// Get version from package.json
const packageJson = JSON.parse(fs.readFileSync(packageFile, 'utf8'));
const version = packageJson.version || '1.0.0';

// Increment build number
const buildNumber = Date.now().toString(36);
const buildTime = new Date().toISOString();

// Update version file
const versionContent = `// Version configuration - automatically updated during build
export const APP_VERSION = {
  version: '${version}',
  buildTime: '${buildTime}',
  buildNumber: '${buildNumber}', // Short unique identifier
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
  return \`v\${APP_VERSION.version}-\${APP_VERSION.buildNumber} (\${dateStr})\`;
};

// Short version for display
export const getShortVersion = () => {
  return \`v\${APP_VERSION.version}-\${APP_VERSION.buildNumber}\`;
};`;

fs.writeFileSync(versionFile, versionContent);
console.log(`✅ Version updated: v${version}-${buildNumber}`);