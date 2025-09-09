# Complexity Analysis Report - New Rules

**Date:** September 2025
**Documents Analyzed:** 336
**Analysis Based On:** SQL field_analysis.json

---

## New Complexity Rules Applied

### Simple
- **Criteria:** Under 10 fields AND no scripted fields AND maximum 2 IF statements
- **Count:** 155 documents (46.1%)
- **Total Effort:** 168 hours

### Moderate
- **Criteria:** 10-20 fields (inclusive) AND fewer than 5 scripted fields AND maximum 20 IF statements
- **Count:** 41 documents (12.2%)
- **Total Effort:** 365 hours

### Complex
- **Criteria:** Everything else (>20 fields OR ≥5 scripted fields OR >20 IF statements)
- **Count:** 140 documents (41.7%)
- **Total Effort:** 9488 hours

---

## Key Statistics

### Overall Distribution

**Simple:**
- Documents: 155 (46.1%)
- Average Fields: 2.2
- Average IF Statements: 0.2
- Average Scripted Fields: 0.0
- Field Range: 0-9
- Total Hours: 168
- Average Hours: 1.08

**Moderate:**
- Documents: 41 (12.2%)
- Average Fields: 11.9
- Average IF Statements: 4.7
- Average Scripted Fields: 1.4
- Field Range: 10-19
- Total Hours: 365
- Average Hours: 8.91

**Complex:**
- Documents: 140 (41.7%)
- Average Fields: 54.2
- Average IF Statements: 28.2
- Average Scripted Fields: 15.3
- Field Range: 1-378
- Total Hours: 9488
- Average Hours: 67.77

---

## Total Project Effort

- **Total Estimated Hours:** 10020
- **Average Hours per Document:** 29.82

---

## Migration Strategy Based on Complexity

### Phase 1: Simple Documents (155 documents)
- Can be largely automated
- Minimal scripting required
- Focus on templates and patterns
- Estimated effort: 168 hours

### Phase 2: Moderate Documents (41 documents)
- Semi-automated approach
- Some custom scripting needed
- Reusable components applicable
- Estimated effort: 365 hours

### Phase 3: Complex Documents (140 documents)
- Requires manual review
- Significant custom development
- Individual testing needed
- Estimated effort: 9488 hours

---

## Files Generated

1. **Complexity_Analysis_New_Rules.xlsx** - Complete analysis with 8 sheets
2. **Complexity_Report_New_Rules.md** - This summary report

---

*Analysis complete*
