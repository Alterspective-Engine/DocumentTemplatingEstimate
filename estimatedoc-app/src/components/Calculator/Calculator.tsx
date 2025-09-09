import React from 'react';
import { useCalculatorStore } from '../../store/calculatorStore';
import { X, Calculator as CalcIcon, RotateCcw, Save } from 'lucide-react';
import './Calculator.css';

export const Calculator: React.FC = () => {
  const {
    settings,
    isOpen,
    closeCalculator,
    updateFieldTime,
    updateComplexityThreshold,
    updateComplexityMultiplier,
    updateOptimization,
    resetToDefaults,
    applySettings
  } = useCalculatorStore();

  if (!isOpen) return null;

  const handleApply = () => {
    applySettings();
    closeCalculator();
  };

  return (
    <div className="calculator-overlay">
      <div className="calculator-panel glass-modal">
        <div className="calculator-header">
          <div className="header-title">
            <CalcIcon size={24} />
            <h2 className="headline-small">Effort Calculator Settings</h2>
          </div>
          <button className="close-button" onClick={closeCalculator}>
            <X size={24} />
          </button>
        </div>

        <div className="calculator-content">
          {/* Field Time Estimates */}
          <section className="calculator-section">
            <h3 className="title-large">Field Time Estimates (minutes)</h3>
            <div className="settings-grid">
              {Object.entries(settings.fieldTimeEstimates).map(([field, estimate]) => (
                <div key={field} className="setting-item">
                  <label className="label-medium">
                    {field.replace(/([A-Z])/g, ' $1').trim()}
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
              ))}
            </div>
          </section>

          {/* Complexity Thresholds */}
          <section className="calculator-section">
            <h3 className="title-large">Complexity Thresholds</h3>
            
            <div className="threshold-group">
              <h4 className="label-large">Simple Criteria</h4>
              <div className="threshold-inputs">
                <div className="input-group">
                  <label className="label-small">Max Fields</label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.simple.maxFields}
                    onChange={(e) => updateComplexityThreshold('simple', 'maxFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">Max Scripts</label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.simple.maxScripts}
                    onChange={(e) => updateComplexityThreshold('simple', 'maxScripts', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">Max IF Statements</label>
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
                  <label className="label-small">Min Fields</label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.minFields}
                    onChange={(e) => updateComplexityThreshold('moderate', 'minFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">Max Fields</label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.maxFields}
                    onChange={(e) => updateComplexityThreshold('moderate', 'maxFields', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">Max Scripts</label>
                  <input
                    type="number"
                    value={settings.complexityThresholds.moderate.maxScripts}
                    onChange={(e) => updateComplexityThreshold('moderate', 'maxScripts', Number(e.target.value))}
                    className="number-input"
                  />
                </div>
                <div className="input-group">
                  <label className="label-small">Max IF Statements</label>
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
            <h3 className="title-large">Complexity Multipliers</h3>
            <div className="settings-grid">
              {Object.entries(settings.complexityMultipliers).map(([complexity, multiplier]) => (
                <div key={complexity} className="setting-item">
                  <label className="label-medium">
                    {complexity.charAt(0).toUpperCase() + complexity.slice(1)}
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
            <h3 className="title-large">Optimization Factors</h3>
            <div className="settings-grid">
              {Object.entries(settings.optimization).map(([key, setting]) => (
                <div key={key} className="setting-item">
                  <label className="label-medium">
                    {key.replace(/([A-Z])/g, ' $1').trim()}
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
          <button className="button-secondary" onClick={resetToDefaults}>
            <RotateCcw size={18} />
            Reset to Defaults
          </button>
          <button className="button-primary" onClick={handleApply}>
            <Save size={18} />
            Apply Settings
          </button>
        </div>
      </div>
    </div>
  );
};