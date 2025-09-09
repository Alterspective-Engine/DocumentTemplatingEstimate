# AI Agent Development Guidelines (Shared)

Reference Architecture: Agents must follow the system structure defined in `docs/ARCHITECTURE.md` (routing, integration, and no-orphaned-files policy).

This shared document consolidates the core standards for all AI agents (Claude, GPT, Copilot, etc.) working on the EstimateDoc project. Agent-specific prompt patterns may live in separate files (e.g., `CLAUDE.md`) but must adhere to these shared rules.

## 1. Code Quality Standards

### TypeScript Requirements
- MANDATORY: Use TypeScript for all new code (`.ts`, `.tsx`)
- NEVER use plain JavaScript except for essential config files
- ALWAYS define proper types and interfaces
- FORBIDDEN: Using `any` without explicit justification
- REQUIRED: Enable strict mode in `tsconfig.json`
- ALWAYS use explicit return types for functions
- MUST handle null/undefined with proper type guards

### Coding Best Practices

- SOLID principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, Dependency Inversion
- DRY: Extract duplicate code to functions/modules; create reusable components/utilities
- Clean code: Descriptive names; functions 20–30 lines max; 3–4 params max; max 3 nesting levels; self-documenting code; prefer early returns and guard clauses

### Code Organization Standards
- File naming: `kebab-case.ts`; React components: `PascalCase.tsx`
- Import order: external → internal → types → styles
- Group related functionality into modules; separate business logic from UI
- Use barrel exports for clean imports; one component per file
- Co-locate tests with source files

### Error Handling Requirements
- Use try-catch for all async operations; never suppress errors
- Provide meaningful user-facing error messages
- Use custom error classes for domain errors
- Log errors appropriately; use React error boundaries

### Performance Requirements
- Use `React.memo` for expensive renders
- Use `useMemo`/`useCallback` appropriately; prevent unnecessary re-renders
- Lazy load routes/components; code split where appropriate; monitor bundle size

### React/Component Standards
- Functional components with hooks only; pure components when possible
- Custom hooks for reusable logic; separate container/presentational components
- TypeScript interfaces for all props; PropTypes are forbidden
- Include error boundaries for fault tolerance

## 2. File Organization Rules

### CRITICAL: No Orphaned Files Policy
Every file created must be properly integrated into the application structure.

1) No Orphaned Files
- NEVER create standalone HTML/JS/CSS or other files not connected to the app
- Every new file must be imported, linked, or referenced by at least one other file
- Remove unused files immediately
- Test files must correspond to real implementation files

2) Clean Navigation Structure
- All pages must be reachable from the main application entry point (index)
- Navigation must be bidirectional (to a page and back)
- Implement proper routing with clear navigation paths
- Include breadcrumbs or back buttons where appropriate
- No dead-end pages

3) File Structure Verification (before completing any task)
- All new files are properly imported/linked
- All routes are accessible from main navigation
- No broken imports or missing dependencies
- No duplicate functionality across files
- Proper file naming conventions are followed

4) Navigation Testing Checklist
- [ ] Can reach this page from index/home?
- [ ] Can navigate back to previous page?
- [ ] Are all links on this page functional?
- [ ] Does the browser back button work correctly?
- [ ] Any console errors during navigation?

Example structure:
```
src/
├── index.tsx                 # Entry point - imports App
├── App.tsx                   # Main app - imports all routes
├── components/
│   ├── Navigation.tsx        # Imported by App.tsx
│   ├── Dashboard.tsx         # Imported by App.tsx routes
│   └── Reports.tsx           # Imported by App.tsx routes
├── pages/                    # All pages must be in router
│   ├── Home.tsx              # Linked in App router
│   ├── About.tsx             # Linked in App router
│   └── Settings.tsx          # Linked in App router
└── utils/                    # All utils must be used
    └── helpers.ts            # Imported by components that need it
```

## 3. Data Accuracy (Shared Rules)

- NO Mock or Fake Data: Never use placeholder data in calculations; require real, verified data. If data is missing, stop and ask.
- NO Hard-Coded Values: Do not hard-code numerical values/rates; make configurable (env, config, parameters, DB/API). Exceptions: mathematical constants (π, e) and universally true values.
- NO Assumptions or Guessing: Do not assume business logic or formulas; ask for clarification; document sources of formulas and methods.
- Input Validation: Validate types, ranges, null/undefined, and units; do not proceed if validation fails.
- Calculation Transparency: Show steps and intermediate results; include units; round appropriately and document rules; provide audit trails for complex logic.
- Error Handling: Implement comprehensive error handling; never fail silently; log with full context; provide meaningful messages.

Double-Check Protocol (after every task):
- Data Source Check: Verified sources, no hard-coded values, inputs validated
- Calculation Review: Correct steps, consistent units, consistent/documented rounding, edge cases handled
- Assumption Audit: Zero unconfirmed assumptions; business rules explicit; no guessed values/relationships
- Output Verification: Include units/precision; transparent methodology; appropriate error scenarios

## 4. Database and Data Integrity
- Never use mock or placeholder data in production code
- Validate all data before processing; maintain referential integrity

## 5. Testing Requirements
- Write unit tests for new functionality; ensure existing tests pass
- Test edge cases and error scenarios; verify UI components render correctly

## 6. Documentation
- Document complex logic with clear comments
- Update README files when adding features
- Include JSDoc comments for functions/components; keep API docs up to date

## 7. Security Best Practices
- Never commit sensitive data or credentials
- Validate and sanitize all user inputs
- Use environment variables for configuration
- Follow OWASP web security guidelines

## 8. Performance Considerations
- Optimize database queries and implement caching when appropriate
- Lazy load components as needed; monitor and optimize bundle sizes

## 9. Version Control
- Make atomic commits with clear messages
- Never commit broken code to main
- Test thoroughly before pushing; follow the project git workflow

## 10. Communication and Reporting
- Report discovered issues; document assumptions and decisions
- Communicate blockers immediately; provide clear status updates

## 11. File Cleanup Protocol

- Before Starting Work: Scan for orphaned files; check for broken imports; verify navigation structure
- During Development: Wire up new files immediately; update navigation for new pages; remove unused files
- Before Completing Task: Run build; verify all files reachable; test navigation end-to-end; clean temporary/test files

## 12. Quality Checklist

Code Quality
- [ ] TypeScript only; no `.js` (except essential config)
- [ ] No `any` types without justification
- [ ] Explicit return types for all functions
- [ ] Proper error handling with try-catch
- [ ] Functions under 30 lines; <= 3 levels nesting
- [ ] Descriptive names; SOLID; DRY

File Organization
- [ ] All files integrated; navigation works both ways
- [ ] No unused imports/variables; no orphaned files
- [ ] Proper naming conventions; imports organized

Testing & Build
- [ ] Tests passing; edge cases covered
- [ ] Build succeeds without warnings
- [ ] TypeScript compiles without errors; ESLint clean
- [ ] Bundle size monitored/optimized

Runtime Quality
- [ ] No console errors; full app navigation
- [ ] Error boundaries catch failures
- [ ] Performance optimized; loading states handled

Documentation
- [ ] Code self-documenting; complex logic commented
- [ ] README updated if needed; interfaces documented
- [ ] API changes documented

---

Always leave the code better than you found it.

