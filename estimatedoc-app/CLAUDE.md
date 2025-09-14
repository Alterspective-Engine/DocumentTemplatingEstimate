# CLAUDE.md - Development Rules for EstimateDoc

## 🔄 Version Management Rules

### MANDATORY: Update Version on Every Change
- **Rule**: Increment version in `package.json` after EVERY code change
- **Location**: `/estimatedoc-app/package.json` → `"version"` field
- **Format**: Semantic Versioning (MAJOR.MINOR.PATCH)
  - PATCH: Bug fixes, minor adjustments (0.0.1 → 0.0.2)
  - MINOR: New features, significant improvements (0.0.x → 0.1.0)
  - MAJOR: Breaking changes, major refactors (0.x.x → 1.0.0)

### Version Update Checklist
1. ✅ After any code modification
2. ✅ After fixing bugs
3. ✅ After adding features
4. ✅ After updating dependencies
5. ✅ After configuration changes

## 📊 Database Integration Rules

### Data Source Priority
1. **Primary**: SQLite database (`/src/database/estimatedoc_complete.db`)
2. **Fallback**: Extracted database documents (`/src/data/database-documents.ts`)
3. **Legacy**: Hardcoded data only if explicitly disabled

### Database Updates
- Run `node scripts/extract-db-data.js` after database schema changes
- Validate all 547 documents are loading
- Ensure field type mappings are correct

## 🎨 UI/UX Standards

### Brand Colors (Alterspective)
- Primary Green: `#075156`
- Secondary Green: `#2C8248`
- Accent: `#ABDD65`
- **NO** purple/blue gradients

### Calculator Settings
- All sliders MUST support 0 as minimum value
- Base template time: 0-120 minutes
- Field estimates: 0-max minutes
- Live recalculation on every change

## 🧪 Testing Requirements

### Before Committing
1. Run TypeScript check: `npx tsc --noEmit`
2. Test calculator functionality: `npx playwright test tests/calculator-functionality.spec.ts`
3. Verify database integration: `npx playwright test tests/database-integration.spec.ts`
4. Check slider functionality: `npx playwright test tests/slider-test.spec.ts`

### Critical Tests
- ✅ 547 documents must load from database
- ✅ All sliders must be interactive
- ✅ Calculations must update live
- ✅ No console errors

## 🔧 Calculator Configuration

### Field Time Estimates (8 types)
1. If Statement
2. Precedent Script
3. Reflection
4. Search
5. Unbound
6. Built-in Script
7. Extended
8. Scripted

### Calculation Formula
```
Effort = (Base_Template_Time + Field_Time) × Complexity_Multiplier
```

## 🚀 Deployment

### Azure Configuration
- Resource Group: `Alterspective Consulting Services`
- Container App: `estimatedoc-app`
- Domain: `template-discoveryandestimate-mb.alterspective.com.au`

### Pre-deployment Checklist
1. ✅ Update version in package.json
2. ✅ Run all tests
3. ✅ Build production: `npm run build`
4. ✅ Test production build locally
5. ✅ Deploy to Azure

## 📝 Code Standards

### Component Structure
- Use TypeScript for all new components
- Implement proper error boundaries
- Handle both database and legacy data formats
- Include loading states and error handling

### State Management
- Zustand for global state
- Local state for UI-only concerns
- Sync state changes with recalculations

## 🐛 Known Issues & Fixes

### Common Issues
1. **Slider stuck**: Ensure using local state + store update
2. **Documents not loading**: Check data verification service
3. **Calculations not updating**: Verify recalculateAllDocumentsLive is called

### Error Handling
- Always handle both database format (`fieldTypes`) and legacy format (`fields`)
- Provide fallbacks for missing data
- Use default values to prevent NaN errors

## 📋 Data Verification

### Field Count Validation
- Support both formats in `dataVerification.ts`
- Check totals only if they exist
- Allow for rounding differences

## 🔄 Version History Reference
- 0.0.0: Initial version
- 0.0.1: Database integration
- 0.0.2: Calculator fixes
- 0.0.3: Slider improvements
- [UPDATE THIS LIST WITH EACH VERSION]

---

**REMEMBER: Update version in package.json after EVERY change!**