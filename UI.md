# EstimateDoc UI Design System

## Material Design 3 Implementation Guide

This document defines the comprehensive UI/UX design system for EstimateDoc, combining Material Design 3 principles with Alterspective brand identity for document analysis, insights generation, and estimate presentation.

---

## 1. Design Principles

### Core Philosophy
- **Clarity**: Information hierarchy that guides users through complex document analysis
- **Confidence**: Professional presentation that builds trust in estimates
- **Efficiency**: Streamlined workflows for document processing
- **Transparency**: Clear visibility into analysis methods and calculations

### Material Design 3 Foundations
- **Dynamic Color**: Adaptive color system responding to content and context
- **Elevation**: Layered surfaces using shadow and light
- **Motion**: Purposeful animations guiding attention
- **Shape**: Rounded corners with strategic emphasis

---

## 2. Color System

### Primary Brand Colors
```css
:root {
  /* Alterspective Brand Colors */
  --primary-orange: #FF6B35;      /* Alterspective signature orange */
  --primary-dark: #1A1A2E;        /* Deep navy for professional contrast */
  --primary-charcoal: #2D2D2D;    /* Charcoal for text and headers */
  
  /* Material Design 3 Surface Colors */
  --surface-1: #FFFFFF;
  --surface-2: #F8F9FA;
  --surface-3: #F1F3F5;
  --surface-variant: #E9ECEF;
  
  /* Semantic Colors */
  --success: #28A745;
  --warning: #FFC107;
  --error: #DC3545;
  --info: #17A2B8;
  
  /* Transparency Layers */
  --overlay-light: rgba(255, 255, 255, 0.92);
  --overlay-medium: rgba(255, 255, 255, 0.85);
  --overlay-dark: rgba(26, 26, 46, 0.95);
  --glass-effect: rgba(255, 255, 255, 0.72);
}
```

### Dark Mode Support
```css
@media (prefers-color-scheme: dark) {
  :root {
    --surface-1: #1A1A2E;
    --surface-2: #232340;
    --surface-3: #2C2C4A;
    --text-primary: #FFFFFF;
    --text-secondary: #B8BCC8;
  }
}
```

---

## 3. Typography

### Font Hierarchy
```css
/* Display & Headers - Chronicle Display */
.display-large {
  font-family: 'Chronicle Display', serif;
  font-size: 57px;
  line-height: 64px;
  font-weight: 400;
  letter-spacing: -0.25px;
}

.headline-large {
  font-family: 'Chronicle Display', serif;
  font-size: 32px;
  line-height: 40px;
  font-weight: 400;
}

/* Body & UI Text - Montserrat */
.body-large {
  font-family: 'Montserrat', sans-serif;
  font-size: 16px;
  line-height: 24px;
  font-weight: 400;
  letter-spacing: 0.5px;
}

.label-large {
  font-family: 'Montserrat', sans-serif;
  font-size: 14px;
  line-height: 20px;
  font-weight: 500;
  letter-spacing: 0.1px;
}
```

---

## 4. Components & Patterns

### 4.1 Header Component
```tsx
interface HeaderProps {
  transparent?: boolean;
  elevated?: boolean;
}

/* Implementation Pattern */
.app-header {
  position: fixed;
  top: 0;
  width: 100%;
  height: 80px;
  backdrop-filter: blur(20px);
  background: var(--overlay-light);
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  z-index: 1000;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.app-header.scrolled {
  height: 64px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.08);
}

/* Logo Usage */
.header-logo {
  height: 40px;
  width: auto;
  /* Use Alterspective_Logo_FA.png for light backgrounds */
  /* Use Alterspective_Logo_reversed_FA.png for dark backgrounds */
}
```

### 4.2 Navigation Patterns
```css
.nav-primary {
  display: flex;
  gap: 32px;
  align-items: center;
}

.nav-item {
  position: relative;
  padding: 8px 16px;
  border-radius: 24px;
  transition: all 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 107, 53, 0.08);
}

.nav-item.active::after {
  content: '';
  position: absolute;
  bottom: -2px;
  left: 16px;
  right: 16px;
  height: 3px;
  background: var(--primary-orange);
  border-radius: 3px;
}
```

### 4.3 Card Components
```css
.card {
  background: var(--surface-1);
  border-radius: 16px;
  padding: 24px;
  transition: all 0.3s ease;
  border: 1px solid var(--surface-variant);
}

.card-elevated {
  box-shadow: 
    0 1px 2px rgba(0, 0, 0, 0.04),
    0 2px 8px rgba(0, 0, 0, 0.08);
}

.card-interactive:hover {
  transform: translateY(-2px);
  box-shadow: 
    0 4px 12px rgba(0, 0, 0, 0.08),
    0 8px 24px rgba(0, 0, 0, 0.12);
}

/* Glass Morphism Card */
.card-glass {
  background: var(--glass-effect);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}
```

### 4.4 Document Analysis Components
```css
/* Document Upload Area */
.upload-zone {
  border: 2px dashed var(--primary-orange);
  border-radius: 16px;
  padding: 48px;
  text-align: center;
  background: linear-gradient(135deg, 
    rgba(255, 107, 53, 0.05) 0%, 
    rgba(255, 107, 53, 0.02) 100%);
  transition: all 0.3s ease;
}

.upload-zone.drag-over {
  background: rgba(255, 107, 53, 0.1);
  border-color: var(--primary-orange);
  transform: scale(1.02);
}

/* Analysis Progress */
.analysis-progress {
  position: relative;
  height: 8px;
  background: var(--surface-3);
  border-radius: 8px;
  overflow: hidden;
}

.analysis-progress-bar {
  height: 100%;
  background: linear-gradient(90deg, 
    var(--primary-orange) 0%, 
    #FF8C61 100%);
  border-radius: 8px;
  transition: width 0.3s ease;
}
```

### 4.5 Estimate Presentation
```css
/* Estimate Summary Card */
.estimate-summary {
  background: linear-gradient(135deg, 
    var(--primary-dark) 0%, 
    #2A2A4E 100%);
  color: white;
  border-radius: 24px;
  padding: 32px;
  position: relative;
  overflow: hidden;
}

.estimate-summary::before {
  content: '';
  position: absolute;
  top: -50%;
  right: -50%;
  width: 200%;
  height: 200%;
  background: url('/assets/alterspective-pattern.svg');
  opacity: 0.05;
  transform: rotate(45deg);
}

.estimate-value {
  font-family: 'Chronicle Display', serif;
  font-size: 48px;
  font-weight: 600;
  margin: 16px 0;
}

.estimate-confidence {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 16px;
  background: rgba(255, 255, 255, 0.1);
  border-radius: 20px;
  font-size: 14px;
}
```

---

## 5. Visual Effects & Interactions

### 5.1 Transparency & Blur Effects
```css
/* Glassmorphism Base */
.glass-surface {
  background: rgba(255, 255, 255, 0.72);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.18);
}

/* Frosted Glass Overlay */
.frosted-overlay {
  background: linear-gradient(
    135deg,
    rgba(255, 255, 255, 0.9) 0%,
    rgba(255, 255, 255, 0.7) 100%
  );
  backdrop-filter: blur(10px);
}
```

### 5.2 Micro-interactions
```css
/* Ripple Effect */
.ripple {
  position: relative;
  overflow: hidden;
}

.ripple::after {
  content: '';
  position: absolute;
  top: 50%;
  left: 50%;
  width: 0;
  height: 0;
  border-radius: 50%;
  background: rgba(255, 107, 53, 0.3);
  transform: translate(-50%, -50%);
  transition: width 0.6s, height 0.6s;
}

.ripple:active::after {
  width: 300px;
  height: 300px;
}

/* Hover Elevation */
.elevate-on-hover {
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

.elevate-on-hover:hover {
  transform: translateY(-4px);
  box-shadow: 
    0 8px 16px rgba(0, 0, 0, 0.1),
    0 16px 32px rgba(0, 0, 0, 0.08);
}
```

---

## 6. Layout System

### 6.1 Grid Structure
```css
.container {
  max-width: 1440px;
  margin: 0 auto;
  padding: 0 24px;
}

.grid {
  display: grid;
  gap: 24px;
}

.grid-cols-12 {
  grid-template-columns: repeat(12, 1fr);
}

/* Responsive Breakpoints */
@media (max-width: 1024px) {
  .grid-cols-12 {
    grid-template-columns: repeat(8, 1fr);
  }
}

@media (max-width: 768px) {
  .grid-cols-12 {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

### 6.2 Spacing System
```css
/* Material Design 3 Spacing Scale */
.spacing-xs: 4px;
.spacing-sm: 8px;
.spacing-md: 16px;
.spacing-lg: 24px;
.spacing-xl: 32px;
.spacing-2xl: 48px;
.spacing-3xl: 64px;
```

---

## 7. Page Templates

### 7.1 Dashboard Layout
```html
<div class="dashboard-layout">
  <!-- Fixed Header with Glass Effect -->
  <header class="app-header glass-surface">
    <img src="/assets/logos/Alterspective_Logo_FA.png" class="header-logo" />
    <nav class="nav-primary">
      <a class="nav-item active">Dashboard</a>
      <a class="nav-item">Documents</a>
      <a class="nav-item">Analytics</a>
      <a class="nav-item">Estimates</a>
    </nav>
  </header>
  
  <!-- Main Content Area -->
  <main class="dashboard-main">
    <!-- Hero Section with Background Pattern -->
    <section class="hero-section">
      <div class="hero-background">
        <!-- Subtle geometric pattern overlay -->
      </div>
      <h1 class="display-large">Document Intelligence Platform</h1>
    </section>
    
    <!-- Content Grid -->
    <div class="container">
      <div class="grid grid-cols-12">
        <!-- Widgets and cards -->
      </div>
    </div>
  </main>
  
  <!-- Footer -->
  <footer class="app-footer">
    <img src="/assets/logos/Alterspective_Symbol_FA.png" class="footer-logo" />
  </footer>
</div>
```

### 7.2 Document Analysis View
```html
<div class="analysis-view">
  <!-- Progress Indicator -->
  <div class="analysis-header glass-surface">
    <div class="progress-steps">
      <div class="step active">Upload</div>
      <div class="step active">Analyze</div>
      <div class="step">Review</div>
      <div class="step">Estimate</div>
    </div>
  </div>
  
  <!-- Analysis Results -->
  <div class="analysis-results">
    <div class="card card-glass">
      <h2>Document Insights</h2>
      <!-- Charts and metrics -->
    </div>
  </div>
</div>
```

---

## 8. Icon System

### Process Icons Usage
Utilize Alterspective's custom icons for process visualization:

```css
.process-icon {
  width: 48px;
  height: 48px;
  padding: 12px;
  background: var(--surface-2);
  border-radius: 12px;
}

.process-icon.discover { /* Use Alterspective Icon FA (discover).png */ }
.process-icon.design   { /* Use Alterspective Icon FA (design).png */ }
.process-icon.validate { /* Use Alterspective Icon FA (validate).png */ }
.process-icon.build    { /* Use Alterspective Icon FA (build).png */ }
.process-icon.deploy   { /* Use Alterspective Icon FA (deploy).png */ }
.process-icon.sustain  { /* Use Alterspective Icon FA (sustain).png */ }
```

---

## 9. Animation Guidelines

### Motion Principles
```css
/* Standard Easing Functions */
--ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
--ease-decelerate: cubic-bezier(0, 0, 0.2, 1);
--ease-accelerate: cubic-bezier(0.4, 0, 1, 1);

/* Duration Scale */
--duration-short: 150ms;
--duration-medium: 300ms;
--duration-long: 500ms;

/* Page Transitions */
.page-enter {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp var(--duration-medium) var(--ease-standard);
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
```

---

## 10. Accessibility Guidelines

### Focus States
```css
/* Visible Focus Indicators */
:focus-visible {
  outline: 2px solid var(--primary-orange);
  outline-offset: 2px;
  border-radius: 4px;
}

/* Skip Links */
.skip-link {
  position: absolute;
  top: -40px;
  left: 0;
  background: var(--primary-dark);
  color: white;
  padding: 8px 16px;
  text-decoration: none;
  border-radius: 0 0 8px 0;
}

.skip-link:focus {
  top: 0;
}
```

### Color Contrast
- Ensure minimum WCAG AA compliance (4.5:1 for normal text, 3:1 for large text)
- Primary orange (#FF6B35) on white: 3.42:1 (use for large text only)
- Primary dark (#1A1A2E) on white: 15.89:1 (excellent contrast)

---

## 11. Implementation Checklist

### Initial Setup
- [ ] Install Material Design 3 CSS framework or custom implementation
- [ ] Configure Chronicle Display and Montserrat fonts
- [ ] Set up color variables in CSS/SCSS
- [ ] Import Alterspective logos and icons
- [ ] Configure responsive breakpoints

### Component Development
- [ ] Build reusable header component with transparency
- [ ] Create card system with elevation variants
- [ ] Implement upload zone with drag-and-drop
- [ ] Design estimate presentation components
- [ ] Build analysis progress indicators

### Visual Polish
- [ ] Apply glassmorphism effects to appropriate surfaces
- [ ] Implement micro-interactions and hover states
- [ ] Add loading and transition animations
- [ ] Ensure consistent spacing throughout
- [ ] Test dark mode implementation

### Quality Assurance
- [ ] Verify accessibility compliance
- [ ] Test responsive behavior on all breakpoints
- [ ] Validate color contrast ratios
- [ ] Check performance of blur effects
- [ ] Ensure smooth animations (60fps)

---

## 12. File Organization

```
/src
  /assets
    /logos
      - Alterspective_Logo_FA.png
      - Alterspective_Logo_reversed_FA.png
      - Alterspective_Symbol_FA.png
    /icons
      - [Process icons from AlterspectiveAssets]
    /patterns
      - alterspective-pattern.svg (create from brand guidelines)
  /styles
    - variables.css (color and spacing tokens)
    - typography.css (font definitions)
    - components.css (reusable components)
    - effects.css (glassmorphism, animations)
    - layout.css (grid and structure)
  /components
    /ui
      - Header.tsx
      - Footer.tsx
      - Card.tsx
      - Button.tsx
      - ProgressBar.tsx
    /features
      - DocumentUpload.tsx
      - AnalysisDisplay.tsx
      - EstimateCard.tsx
```

---

## 13. Performance Considerations

### Optimization Guidelines
1. **Lazy load images**: Use `loading="lazy"` for below-fold images
2. **Optimize blur effects**: Limit backdrop-filter usage to critical UI elements
3. **Reduce paint areas**: Use `will-change` sparingly for animated elements
4. **Font loading**: Use `font-display: swap` for web fonts
5. **CSS containment**: Apply `contain: layout` to independent components

### Performance Metrics
- First Contentful Paint: < 1.8s
- Largest Contentful Paint: < 2.5s
- Cumulative Layout Shift: < 0.1
- First Input Delay: < 100ms

---

## References

- [Material Design 3 Guidelines](https://m3.material.io/)
- [Alterspective Brand Assets](/AlterspectiveAssets)
- [WCAG 2.1 Accessibility Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [Web Performance Best Practices](https://web.dev/performance/)

---

## Version History

- **v1.0.0** (2024-09-09): Initial design system documentation
- Incorporates Material Design 3 principles
- Defines Alterspective brand integration
- Establishes component library foundation