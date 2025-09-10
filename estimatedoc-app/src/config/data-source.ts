// Data source configuration for EstimateDoc
// Allows switching between database and hardcoded data

export interface DataSourceConfig {
  type: 'database' | 'hardcoded';
  useDatabaseIfAvailable: boolean;
}

// Configuration - can be set via environment variable or manually
const config: DataSourceConfig = {
  // Set to 'database' to use SQLite, 'hardcoded' to use TypeScript file
  type: import.meta.env.VITE_DATA_SOURCE === 'database' ? 'database' : 'hardcoded',
  
  // If true, will try to use database first, fall back to hardcoded if DB not available
  useDatabaseIfAvailable: true
};

export default config;