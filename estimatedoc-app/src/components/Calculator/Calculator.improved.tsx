import React, { useEffect, useCallback, useState } from 'react';
import { useCalculatorStore, CALCULATOR_PRESETS } from '../../store/calculatorStore.improved';
import { useDebounce } from '../../hooks/useDebounce';
import { useAnalytics } from '../../hooks/useAnalytics';
import { 
  X, Calculator as CalcIcon, RotateCcw, Save, 
  Undo, Redo, Download, Upload, AlertCircle, 
  TrendingDown, TrendingUp, Info, Zap, Shield, 
  Target, ChevronDown, BarChart2
} from 'lucide-react';
import { ProgressIndicator } from '../LoadingState/LoadingState';
import './Calculator.css';

// Tooltip component
const Tooltip: React.FC<{ text: string; children: React.ReactNode }> = ({ text, children }) => {
  const [show, setShow] = useState(false);
  
  return (
    <div className="tooltip-wrapper" 
         onMouseEnter={() => setShow(true)} 
         onMouseLeave={() => setShow(false)}>
      {children}
      {show && <div className="tooltip-content">{text}</div>}
    </div>
  );
};

// Validation error display
const ValidationErrors: React.FC<{ errors: string[] }> = ({ errors }) => {
  if (errors.length === 0) return null;
  
  return (
    <div className="validation-errors">
      <AlertCircle size={20} />
      <div className="error-list">
        {errors.map((error, i) => (
          <div key={i} className="error-item">{error}</div>
        ))}
      </div>
    </div>
  );
};

// Preset selector component
const PresetSelector: React.FC<{ onSelect: (preset: keyof typeof CALCULATOR_PRESETS) => void }> = ({ onSelect }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  return (
    <div className="preset-selector">
      <button 
        className="preset-button"
        onClick={() => setIsOpen(!isOpen)}
      >
        <Zap size={18} />
        Presets
        <ChevronDown size={16} className={isOpen ? 'rotate' : ''} />
      </button>
      
      {isOpen && (
        <div className="preset-dropdown">
          {Object.entries(CALCULATOR_PRESETS).map(([key, preset]) => (
            <button
              key={key}
              className="preset-option"
              onClick={() => {
                onSelect(key as keyof typeof CALCULATOR_PRESETS);
                setIsOpen(false);
              }}
            >
              <div className="preset-icon">
                {key === 'conservative' && <Shield size={16} />}
                {key === 'balanced' && <Target size={16} />}
                {key === 'aggressive' && <Zap size={16} />}
              </div>
              <div className="preset-info">
                <div className="preset-name">{preset.name}</div>
                <div className="preset-description">{preset.description}</div>
              </div>
            </button>
          ))}
        </div>
      )}
    </div>
  );
};

// Complexity breakdown chart
const ComplexityBreakdown: React.FC<{ breakdown?: any }> = ({ breakdown }) => {
  if (!breakdown) return null;
  
  const total = breakdown.simple.hours + breakdown.moderate.hours + breakdown.complex.hours;
  
  return (
    <div className="complexity-breakdown">
      <h4 className="breakdown-title">
        <BarChart2 size={16} />
        Complexity Distribution
      </h4>
      <div className="breakdown-bars">
        {['simple', 'moderate', 'complex'].map(level => {
          const data = breakdown[level];
          const percentage = total > 0 ? (data.hours / total) * 100 : 0;
          
          return (
            <div key={level} className="breakdown-item">
              <div className="breakdown-label">
                <span className={`complexity-badge ${level}`}>{level}</span>
                <span className="breakdown-count">{data.count} docs</span>
              </div>
              <div className="breakdown-bar">
                <div 
                  className={`breakdown-fill ${level}`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
              <div className="breakdown-hours">{Math.round(data.hours)} hrs</div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export const CalculatorImproved: React.FC = () => {
  const {
    settings,
    isOpen,
    previewImpact,
    isCalculating,
    calculationProgress,
    validationErrors,
    history,
    historyIndex,
    closeCalculator,
    updateFieldTime,
    updateComplexityThreshold,
    updateComplexityMultiplier,
    updateOptimization,
    resetToDefaults,
    applyPreset,
    applySettings,
    calculatePreviewImpact,
    undo,
    redo,
    exportSettings,
    importSettings
  } = useCalculatorStore();
  
  const { trackCalculatorUsage, trackClick } = useAnalytics();
  const [importDialogOpen, setImportDialogOpen] = useState(false);

  // Calculate preview on initial open
  useEffect(() => {
    if (isOpen) {
      calculatePreviewImpact();
      trackClick('calculator_open');
    }
  }, [isOpen, calculatePreviewImpact]);

  // Debounce settings for preview calculation
  const debouncedSettings = useDebounce(settings, 300);
  
  // Trigger preview calculation when settings change
  useEffect(() => {
    if (isOpen && debouncedSettings) {
      calculatePreviewImpact();
    }
  }, [debouncedSettings, isOpen, calculatePreviewImpact]);

  if (!isOpen) return null;

  const handleApply = () => {
    if (validationErrors.length === 0) {
      applySettings();
      trackCalculatorUsage(settings);
      closeCalculator();
    }
  };
  
  const handleReset = () => {
    resetToDefaults();
    trackClick('calculator_reset');
  };
  
  const handleExport = () => {
    const json = exportSettings();
    const blob = new Blob([json], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `calculator-settings-${new Date().toISOString().split('T')[0]}.json`;
    a.click();
    URL.revokeObjectURL(url);
    trackClick('calculator_export');
  };
  
  const handleImport = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      const reader = new FileReader();
      reader.onload = (e) => {
        const content = e.target?.result as string;
        if (importSettings(content)) {
          trackClick('calculator_import_success');
          setImportDialogOpen(false);
        } else {
          alert('Invalid settings file');
        }
      };
      reader.readAsText(file);
    }
  };
  
  const canUndo = historyIndex > 0;
  const canRedo = historyIndex < history.length - 1;

  return (
    <div className="calculator-overlay">
      <div className="calculator-panel glass-modal enhanced">
        <div className="calculator-header">
          <div className="header-title">
            <CalcIcon size={24} />
            <h2 className="headline-small">Effort Calculator Settings</h2>
            <div className="header-actions">
              <Tooltip text="Undo last change">
                <button 
                  className="icon-button" 
                  onClick={undo} 
                  disabled={!canUndo}
                >
                  <Undo size={18} />
                </button>
              </Tooltip>
              <Tooltip text="Redo change">
                <button 
                  className="icon-button" 
                  onClick={redo} 
                  disabled={!canRedo}
                >
                  <Redo size={18} />
                </button>
              </Tooltip>
              <Tooltip text="Export settings">
                <button className="icon-button" onClick={handleExport}>
                  <Download size={18} />
                </button>
              </Tooltip>
              <Tooltip text="Import settings">
                <button 
                  className="icon-button" 
                  onClick={() => setImportDialogOpen(true)}
                >
                  <Upload size={18} />
                </button>
              </Tooltip>
            </div>
          </div>
          <button className="close-button" onClick={closeCalculator}>
            <X size={24} />
          </button>
        </div>

        {/* Validation Errors */}
        <ValidationErrors errors={validationErrors} />

        {/* Preset Selector */}
        <div className="calculator-toolbar">
          <PresetSelector onSelect={applyPreset} />
        </div>

        {/* Live Preview Panel */}
        {previewImpact && (
          <div className="preview-impact-panel enhanced">
            <div className="preview-header">
              <h3 className="label-large">Live Impact Preview</h3>
              {previewImpact.confidenceLevel && previewImpact.confidenceLevel < 100 && (
                <span className="confidence-badge">
                  {previewImpact.confidenceLevel}% confidence
                  <Tooltip text="Based on sample of documents for performance">
                    <Info size={14} />
                  </Tooltip>
                </span>
              )}
            </div>
            
            {isCalculating ? (
              <ProgressIndicator 
                current={calculationProgress} 
                total={100} 
                message="Calculating impact..."
              />
            ) : (
              <>
                <div className="preview-metrics">
                  <div className="metric-card">
                    <span className="metric-label">Current Total</span>
                    <span className="metric-value">{previewImpact.totalHoursBefore.toLocaleString()} hrs</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">New Total</span>
                    <span className="metric-value highlight">{previewImpact.totalHoursAfter.toLocaleString()} hrs</span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Impact</span>
                    <span className={`metric-value ${previewImpact.percentChange < 0 ? 'positive' : 'negative'}`}>
                      {previewImpact.percentChange < 0 && <TrendingDown size={16} />}
                      {previewImpact.percentChange > 0 && <TrendingUp size={16} />}
                      {previewImpact.percentChange > 0 ? '+' : ''}{previewImpact.percentChange}%
                    </span>
                  </div>
                  <div className="metric-card">
                    <span className="metric-label">Difference</span>
                    <span className={`metric-value ${previewImpact.totalSavings > 0 ? 'positive' : 'negative'}`}>
                      {previewImpact.totalSavings > 0 ? '-' : '+'}{Math.abs(previewImpact.totalSavings).toLocaleString()} hrs
                    </span>
                  </div>
                </div>
                
                {previewImpact.complexityBreakdown && (
                  <ComplexityBreakdown breakdown={previewImpact.complexityBreakdown} />
                )}
              </>
            )}
          </div>
        )}

        <div className="calculator-content">
          {/* Field Time Estimates */}
          <section className="calculator-section">
            <h3 className="title-large">
              Field Time Estimates (minutes)
              <Tooltip text="Time in minutes to process each field type">
                <Info size={16} />
              </Tooltip>
            </h3>
            <div className="settings-grid">
              {Object.entries(settings.fieldTimeEstimates).map(([field, estimate]) => (
                <div key={field} className="setting-item">
                  <label className="label-medium">
                    {field.replace(/([A-Z])/g, ' $1').trim()}
                    <Tooltip text={`Estimate time for ${field} fields`}>
                      <Info size={14} />
                    </Tooltip>
                  </label>
                  <div className="slider-container">
                    <input
                      type="range"
                      min={estimate.min}
                      max={estimate.max}
                      value={estimate.current}
                      onChange={(e) => updateFieldTime(
                        field as keyof typeof settings.fieldTimeEstimates,
                        Number(e.target.value)
                      )}
                      className="slider"
                    />
                    <div className="slider-value">{estimate.current}</div>
                  </div>
                </div>
              ))

}
            </div>
          </section>

          {/* Complexity Thresholds */}
          <section className="calculator-section">
            <h3 className="title-large">
              Complexity Thresholds
              <Tooltip text="Define when documents are considered simple, moderate, or complex">
                <Info size={16} />
              </Tooltip>
            </h3>
            
            <div className="threshold-group">
              <h4 className="label-large">Simple Criteria</h4>
              <div className="threshold-inputs">
                <div className="input-group">
                  <label className="label-small">
                    Max Fields
                    <Tooltip text="Maximum fields for simple documents">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.simple.maxFields}
                    onChange={(e) => updateComplexityThreshold('simple', 'maxFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">
                    Max Scripts
                    <Tooltip text="Maximum scripts for simple documents">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.simple.maxScripts}
                    onChange={(e) => updateComplexityThreshold('simple', 'maxScripts', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">
                    Max IF Statements
                    <Tooltip text="Maximum IF statements for simple documents">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.simple.maxIfStatements}
                    onChange={(e) => updateComplexityThreshold('simple', 'maxIfStatements', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
              </div>
            </div>

            <div className="threshold-group">
              <h4 className="label-large">Moderate Criteria</h4>
              <div className="threshold-inputs">
                <div className="input-group">
                  <label className="label-small">
                    Min Fields
                    <Tooltip text="Minimum fields for moderate complexity">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.minFields}
                    onChange={(e) => updateComplexityThreshold('moderate', 'minFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">
                    Max Fields
                    <Tooltip text="Maximum fields for moderate complexity">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.maxFields}
                    onChange={(e) => updateComplexityThreshold('moderate', 'maxFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">
                    Max Scripts
                    <Tooltip text="Maximum scripts for moderate complexity">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.maxScripts}
                    onChange={(e) => updateComplexityThreshold('moderate', 'maxScripts', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">
                    Max IF Statements
                    <Tooltip text="Maximum IF statements for moderate complexity">
                      <Info size={12} />
                    </Tooltip>
                  </label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.maxIfStatements}
                    onChange={(e) => updateComplexityThreshold('moderate', 'maxIfStatements', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
              </div>
            </div>
          </section>

          {/* Complexity Multipliers */}
          <section className="calculator-section">
            <h3 className="title-large">
              Complexity Multipliers
              <Tooltip text="Multipliers applied based on document complexity">
                <Info size={16} />
              </Tooltip>
            </h3>
            <div className="settings-grid">
              {Object.entries(settings.complexityMultipliers).map(([complexity, multiplier]) => (
                <div key={complexity} className="setting-item">
                  <label className="label-medium">
                    {complexity.charAt(0).toUpperCase() + complexity.slice(1)}
                    <Tooltip text={`Multiplier for ${complexity} documents`}>
                      <Info size={14} />
                    </Tooltip>
                  </label>
                  <div className="slider-container">
                    <input
                      type="range"
                      min={multiplier.min * 10}
                      max={multiplier.max * 10}
                      value={multiplier.current * 10}
                      onChange={(e) => updateComplexityMultiplier(
                        complexity as 'simple' | 'moderate' | 'complex',
                        Number(e.target.value) / 10
                      )}
                      className="slider"
                    />
                    <div className="slider-value">{multiplier.current.toFixed(1)}x</div>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Optimization Settings */}
          <section className="calculator-section">
            <h3 className="title-large">
              Optimization Factors
              <Tooltip text="Factors that reduce effort through efficiency gains">
                <Info size={16} />
              </Tooltip>
            </h3>
            <div className="settings-grid">
              {Object.entries(settings.optimization).map(([key, setting]) => (
                <div key={key} className="setting-item">
                  <label className="label-medium">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
                    <Tooltip text={`${key} optimization percentage`}>
                      <Info size={14} />
                    </Tooltip>
                  </label>
                  <div className="slider-container">
                    <input
                      type="range"
                      min={setting.min}
                      max={setting.max}
                      value={setting.current}
                      onChange={(e) => updateOptimization(
                        key as keyof typeof settings.optimization,
                        Number(e.target.value)
                      )}
                      className="slider"
                    />
                    <div className="slider-value">{setting.current}%</div>
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>

        <div className="calculator-footer">
          <button className="button-secondary" onClick={handleReset}>
            <RotateCcw size={18} />
            Reset to Defaults
          </button>
          <button 
            className="button-primary" 
            onClick={handleApply}
            disabled={validationErrors.length > 0}
          >
            <Save size={18} />
            Apply Settings
          </button>
        </div>

        {/* Import Dialog */}
        {importDialogOpen && (
          <div className="import-dialog">
            <div className="dialog-content">
              <h3>Import Settings</h3>
              <input 
                type="file" 
                accept=".json"
                onChange={handleImport}
              />
              <button onClick={() => setImportDialogOpen(false)}>Cancel</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};