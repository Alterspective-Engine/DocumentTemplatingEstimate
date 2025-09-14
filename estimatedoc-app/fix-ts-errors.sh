#!/bin/bash

echo "Fixing TypeScript compilation errors..."

# Fix type imports in analytics services
find src/services/analytics -name "*.ts" -exec sed -i '' 's/^import {/import type {/' {} \;

# Fix collectors
sed -i '' 's/import { DeviceInfo }/import type { DeviceInfo }/' src/services/analytics/collectors/DeviceCollector.ts
sed -i '' 's/import { NetworkInfo }/import type { NetworkInfo }/' src/services/analytics/collectors/NetworkCollector.ts
sed -i '' 's/import { LocationInfo }/import type { LocationInfo }/' src/services/analytics/collectors/LocationCollector.ts
sed -i '' 's/import { ConsentState }/import type { ConsentState }/' src/services/analytics/PrivacyManager.ts
sed -i '' 's/import { AnalyticsEvent, VisitorSession }/import type { AnalyticsEvent, VisitorSession }/' src/services/analytics/storage/StorageAdapter.ts

# Fix hooks
sed -i '' 's/import { UserAction }/import type { UserAction }/' src/hooks/useAnalytics.ts

# Fix 'action' type to 'click'
sed -i '' "s/type: 'action'/type: 'click'/g" src/services/analytics/AnalyticsService.ts
sed -i '' "s/type: 'action'/type: 'click'/g" src/hooks/useAnalytics.ts

# Fix localStorage.getItem null check
sed -i '' 's/const cachedDeviceInfo = /const cachedDeviceInfo = /' src/services/analytics/AnalyticsService.ts
sed -i '' '/if (cachedDeviceInfo)/i\
    const deviceInfoStr = localStorage.getItem("analytics_device_info");\
    const cachedDeviceInfo = deviceInfoStr ? JSON.parse(deviceInfoStr) : null;' src/services/analytics/AnalyticsService.ts

# Remove unused variables
sed -i '' '/const totalBatches =/d' src/store/documentStore.ts
sed -i '' '/const optimizedHistory =/d' src/components/DocumentCard/DocumentCard.tsx

# Fix calculatorStore undefined issue
sed -i '' 's/localStorage.getItem(key)/localStorage.getItem(key) || "{}"/g' src/store/calculatorStore.ts
sed -i '' 's/localStorage.getItem(key)/localStorage.getItem(key) || "{}"/g' src/store/calculatorStore.improved.ts

# Remove unused imports
sed -i '' '/^import.*Document.*from.*document.types/d' src/utils/dataVerification.ts

echo "TypeScript fixes applied!"