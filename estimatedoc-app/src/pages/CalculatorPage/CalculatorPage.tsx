import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Calculator as CalcIcon, ArrowLeft, Users, Calendar, 
  Clock, TrendingUp, BarChart3, Settings, Save, Download,
  Info, Zap, ChevronRight, Activity
} from 'lucide-react';
import { useCalculatorStore } from '../../store/calculatorStore';
import { useDocumentStore } from '../../store/documentStore';
import './CalculatorPage.css';

// World-class calculator rubric categories
const CALCULATOR_SECTIONS = {
  BASE_CONFIG: 'Base Configuration',
  FIELD_ESTIMATES: 'Field Time Estimates',
  COMPLEXITY: 'Complexity Settings',
  OPTIMIZATION: 'Optimization Factors',
  RESOURCES: 'Resource Planning',
  TIMELINE: 'Implementation Timeline'
};

interface ResourceConfig {
  fteCount: number;
  hoursPerDay: number;
  daysPerWeek: number;
  utilizationRate: number; // Percentage of time actually working
  vacationDays: number; // Annual vacation days
}

interface TimelineData {
  totalDays: number;
  totalWeeks: number;
  totalMonths: number;
  startDate: Date;
  endDate: Date;
  milestones: {
    phase: string;
    duration: number;
    completion: number;
  }[];
}

export const CalculatorPage: React.FC = () => {
  const navigate = useNavigate();
  const { 
    settings, 
    updateFieldTime,
    applyPreset,
    resetToDefaults,
    updateSettings
  } = useCalculatorStore();
  
  const { documents, recalculateAllDocumentsLive } = useDocumentStore();
  
  // Base template time (in minutes) - use local state synced with settings
  const [baseTemplateTime, setBaseTemplateTimeState] = useState(settings.baseTemplateTime !== undefined ? settings.baseTemplateTime : 40);
  const [searchTerm, setSearchTerm] = useState('');
  
  const setBaseTemplateTime = (value: number) => {
    setBaseTemplateTimeState(value); // Update local state for immediate UI response
    // Note: updateSettings method needs to be implemented in calculatorStore
    // updateSettings({ ...settings, baseTemplateTime: value });
    // Trigger recalculation when base time changes
    setTimeout(() => recalculateAllDocumentsLive({ ...settings, baseTemplateTime: value }), 100);
  };
  
  // Resource configuration
  const [resourceConfig, setResourceConfig] = useState<ResourceConfig>({
    fteCount: 2,
    hoursPerDay: 8,
    daysPerWeek: 5,
    utilizationRate: 80,
    vacationDays: 20
  });
  
  // Calculate implementation timeline
  const calculateTimeline = (): TimelineData => {
    const totalEffortHours = calculateTotalEffort();
    
    // Return default values if no effort
    if (totalEffortHours === 0 || !totalEffortHours) {
      const startDate = new Date();
      return {
        totalDays: 0,
        totalWeeks: 0,
        totalMonths: 0,
        startDate,
        endDate: startDate,
        milestones: [
          { phase: 'Planning & Setup', duration: 0, completion: 15 },
          { phase: 'Initial Migration', duration: 0, completion: 40 },
          { phase: 'Core Implementation', duration: 0, completion: 75 },
          { phase: 'Testing & Validation', duration: 0, completion: 90 },
          { phase: 'Deployment & Handover', duration: 0, completion: 100 }
        ]
      };
    }
    
    const effectiveHoursPerDay = resourceConfig.hoursPerDay * (resourceConfig.utilizationRate / 100);
    const effectiveDaysPerWeek = resourceConfig.daysPerWeek;
    const effectiveHoursPerWeek = effectiveHoursPerDay * effectiveDaysPerWeek;
    const totalFTEHours = effectiveHoursPerWeek * resourceConfig.fteCount;
    
    // Account for vacation days (assuming 52 weeks per year)
    const vacationWeeks = resourceConfig.vacationDays / effectiveDaysPerWeek;
    const workingWeeksPerYear = 52 - vacationWeeks;
    const adjustmentFactor = workingWeeksPerYear / 52;
    
    const adjustedFTEHours = totalFTEHours * adjustmentFactor;
    
    const totalWeeks = adjustedFTEHours > 0 ? Math.ceil(totalEffortHours / adjustedFTEHours) : 0;
    const totalDays = Math.ceil(totalWeeks * effectiveDaysPerWeek);
    const totalMonths = Math.ceil(totalWeeks / 4.33);
    
    const startDate = new Date();
    const endDate = new Date();
    endDate.setDate(endDate.getDate() + (totalWeeks * 7));
    
    // Create milestone phases
    const milestones = [
      { phase: 'Planning & Setup', duration: Math.ceil(totalWeeks * 0.15) || 0, completion: 15 },
      { phase: 'Initial Migration', duration: Math.ceil(totalWeeks * 0.25) || 0, completion: 40 },
      { phase: 'Core Implementation', duration: Math.ceil(totalWeeks * 0.35) || 0, completion: 75 },
      { phase: 'Testing & Validation', duration: Math.ceil(totalWeeks * 0.15) || 0, completion: 90 },
      { phase: 'Deployment & Handover', duration: Math.ceil(totalWeeks * 0.10) || 0, completion: 100 }
    ];
    
    return {
      totalDays: totalDays || 0,
      totalWeeks: totalWeeks || 0,
      totalMonths: totalMonths || 0,
      startDate,
      endDate,
      milestones
    };
  };
  
  const calculateTotalEffort = () => {
    // Calculate total effort based on all documents and settings
    const templateCount = documents.length || 0;
    if (templateCount === 0) return 0;
    
    const baseMinutes = templateCount * baseTemplateTime;
    const baseHours = baseMinutes / 60;
    
    // Apply field time estimates and complexity factors
    let totalHours = baseHours;
    
    // Add field-specific time
    documents.forEach(doc => {
      const fieldCount = typeof doc.fields === 'number' ? doc.fields : 0;
      let complexityLevel: string;
      if (typeof doc.complexity === 'object' && doc.complexity?.level) {
        complexityLevel = doc.complexity.level.toLowerCase();
      } else if (typeof doc.complexity === 'string') {
        complexityLevel = doc.complexity.toLowerCase();
      } else {
        complexityLevel = 'simple';
      }
      const multiplierKey = complexityLevel as 'simple' | 'moderate' | 'complex';
      const multiplier = settings?.complexityMultipliers?.[multiplierKey]?.current || 1;
      
      // Calculate additional time based on fields
      // Use average of all field time estimates
      const avgFieldTime = Object.values(settings?.fieldTimeEstimates || {})
        .reduce((sum, est) => sum + (est?.current || 0), 0) / 
        Math.max(Object.keys(settings?.fieldTimeEstimates || {}).length, 1);
      
      const fieldTime = fieldCount * (avgFieldTime !== undefined ? avgFieldTime : 10) / 60;
      totalHours += fieldTime * multiplier;
    });
    
    // Apply optimization factors
    const reuseReduction = totalHours * (settings?.optimization?.reuseEfficiency?.current || 0) / 100;
    const learningReduction = totalHours * (settings?.optimization?.learningCurve?.current || 0) / 100;
    const automationReduction = totalHours * (settings?.optimization?.automationPotential?.current || 0) / 100;
    
    totalHours -= (reuseReduction + learningReduction + automationReduction);
    
    return Math.max(totalHours, 0);
  };
  
  const timeline = calculateTimeline();
  const totalEffort = calculateTotalEffort();

  return (
    <div className="calculator-page">
      {/* Header */}
      <header className="calculator-header-bar">
        <div className="header-content">
          <button className="back-button" onClick={() => navigate('/')}>
            <ArrowLeft size={20} />
            Back to Documents
          </button>
          
          <div className="header-title">
            <CalcIcon size={32} />
            <div>
              <h1>Effort Estimation Calculator</h1>
              <p>World-class project estimation and resource planning</p>
            </div>
          </div>
          
          <div className="header-actions">
            <button className="preset-button" onClick={() => {
              applyPreset('conservative');
              setTimeout(() => recalculateAllDocumentsLive(settings), 100);
            }}>
              <Zap size={18} />
              Conservative
            </button>
            <button className="preset-button" onClick={() => {
              applyPreset('balanced');
              setTimeout(() => recalculateAllDocumentsLive(settings), 100);
            }}>
              <Zap size={18} />
              Balanced
            </button>
            <button className="preset-button" onClick={() => {
              applyPreset('aggressive');
              setTimeout(() => recalculateAllDocumentsLive(settings), 100);
            }}>
              <Zap size={18} />
              Aggressive
            </button>
            <button className="save-button" onClick={() => {
              resetToDefaults();
              setBaseTemplateTimeState(40);
              setTimeout(() => recalculateAllDocumentsLive(settings), 100);
            }}>
              <Save size={18} />
              Reset All
            </button>
            <button className="export-button" onClick={() => {
              const exportData = {
                settings,
                documents: documents.slice(0, 10), // Export first 10 as sample
                timestamp: new Date().toISOString(),
                version: '0.1.2'
              };
              const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
              const url = URL.createObjectURL(blob);
              const a = document.createElement('a');
              a.href = url;
              a.download = `estimatedoc-settings-${Date.now()}.json`;
              a.click();
              URL.revokeObjectURL(url);
            }}>
              <Download size={18} />
              Export
            </button>
          </div>
        </div>
      </header>

      {/* Main Content Grid */}
      <div className="calculator-content-grid">
        
        {/* Left Column - Configuration */}
        <div className="config-column">
          
          {/* Base Configuration Card */}
          <div className="config-card">
            <div className="card-header">
              <h2>
                <Settings size={20} />
                {CALCULATOR_SECTIONS.BASE_CONFIG}
              </h2>
              <Info size={16} className="info-icon" />
            </div>
            
            <div className="card-content">
              <div className="config-item">
                <label>
                  Base Template Time
                  <span className="unit">(minutes per template)</span>
                </label>
                <div className="input-group">
                  <input
                    type="range"
                    min="0"
                    max="120"
                    value={baseTemplateTime}
                    onChange={(e) => setBaseTemplateTime(Number(e.target.value))}
                    className="slider base-slider"
                  />
                  <span className="value">{baseTemplateTime} min</span>
                </div>
                <div className="help-text">
                  Default time allocation for each template before field-specific adjustments
                </div>
              </div>
              
              <div className="quick-stats">
                <div className="stat">
                  <span className="stat-label">Total Templates</span>
                  <span className="stat-value">{documents.length}</span>
                </div>
                <div className="stat">
                  <span className="stat-label">Base Hours</span>
                  <span className="stat-value">{(documents.length * baseTemplateTime / 60).toFixed(1)}h</span>
                </div>
              </div>
            </div>
          </div>

          {/* Field Time Estimates Card */}
          <div className="config-card">
            <div className="card-header">
              <h2>
                <Clock size={20} />
                {CALCULATOR_SECTIONS.FIELD_ESTIMATES}
              </h2>
              <div style={{ display: 'flex', gap: '8px' }}>
                <button 
                  onClick={() => {
                    Object.keys(settings.fieldTimeEstimates).forEach(field => {
                      updateFieldTime(field as any, 0);
                    });
                    setTimeout(() => recalculateAllDocumentsLive(settings), 100);
                  }}
                  style={{ 
                    padding: '4px 8px', 
                    fontSize: '12px', 
                    background: '#fff', 
                    border: '1px solid #ddd',
                    borderRadius: '4px',
                    cursor: 'pointer'
                  }}
                >
                  All to 0
                </button>
              </div>
            </div>
            
            <div className="card-content">
              <div className="estimates-grid">
                {Object.entries(settings.fieldTimeEstimates).map(([field, estimate]) => (
                  <div key={field} className="estimate-item">
                    <label>{field.replace(/([A-Z])/g, ' $1').trim()}</label>
                    <div className="slider-group">
                      <input
                        type="range"
                        min={estimate.min}
                        max={estimate.max}
                        value={estimate.current}
                        onChange={(e) => {
                          updateFieldTime(field as any, Number(e.target.value));
                          // Trigger live recalculation of all documents
                          setTimeout(() => recalculateAllDocumentsLive(settings), 100);
                        }}
                        className="slider field-slider"
                      />
                      <input
                        type="number"
                        min={estimate.min || 0}
                        max={estimate.max || 100}
                        value={estimate.current}
                        onChange={(e) => {
                          const inputValue = Number(e.target.value);
                          const minVal = estimate.min !== undefined ? estimate.min : 0;
                          const maxVal = estimate.max !== undefined ? estimate.max : 100;
                          // Allow 0 explicitly, don't use || operator which would convert 0 to falsy
                          const val = Math.max(minVal, Math.min(maxVal, isNaN(inputValue) ? minVal : inputValue));
                          updateFieldTime(field as any, val);
                          setTimeout(() => recalculateAllDocumentsLive(settings), 100);
                        }}
                        className={`value-input ${estimate.current === 0 ? 'zero-value' : ''}`}
                        style={{ width: '60px', marginLeft: '10px' }}
                      />
                      <span className={`value ${estimate.current === 0 ? 'zero-value' : ''}`}>{estimate.current}m</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Resource Planning Card */}
          <div className="config-card">
            <div className="card-header">
              <h2>
                <Users size={20} />
                {CALCULATOR_SECTIONS.RESOURCES}
              </h2>
            </div>
            
            <div className="card-content">
              <div className="resource-grid">
                <div className="resource-item">
                  <label>Team Size (FTE)</label>
                  <input
                    type="number"
                    min="1"
                    max="20"
                    value={resourceConfig.fteCount}
                    onChange={(e) => setResourceConfig({
                      ...resourceConfig,
                      fteCount: Number(e.target.value)
                    })}
                    className="number-input"
                  />
                </div>
                
                <div className="resource-item">
                  <label>Hours per Day</label>
                  <input
                    type="number"
                    min="4"
                    max="12"
                    value={resourceConfig.hoursPerDay}
                    onChange={(e) => setResourceConfig({
                      ...resourceConfig,
                      hoursPerDay: Number(e.target.value)
                    })}
                    className="number-input"
                  />
                </div>
                
                <div className="resource-item">
                  <label>Days per Week</label>
                  <input
                    type="number"
                    min="3"
                    max="7"
                    value={resourceConfig.daysPerWeek}
                    onChange={(e) => setResourceConfig({
                      ...resourceConfig,
                      daysPerWeek: Number(e.target.value)
                    })}
                    className="number-input"
                  />
                </div>
                
                <div className="resource-item">
                  <label>Utilization Rate (%)</label>
                  <input
                    type="number"
                    min="50"
                    max="100"
                    value={resourceConfig.utilizationRate}
                    onChange={(e) => setResourceConfig({
                      ...resourceConfig,
                      utilizationRate: Number(e.target.value)
                    })}
                    className="number-input"
                  />
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Column - Results & Timeline */}
        <div className="results-column">
          
          {/* Live Impact Dashboard */}
          <div className="dashboard-card">
            <div className="card-header">
              <h2>
                <Activity size={20} />
                Live Impact Dashboard
              </h2>
            </div>
            
            <div className="dashboard-content">
              <div className="metrics-grid">
                <div className="metric-card primary">
                  <div className="metric-label">Total Effort</div>
                  <div className="metric-value">{isNaN(totalEffort) ? 0 : totalEffort.toFixed(0)} hours</div>
                  <div className="metric-subtext">{isNaN(totalEffort) ? 0 : (totalEffort / 8).toFixed(0)} person-days</div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-label">Duration</div>
                  <div className="metric-value">{timeline.totalWeeks || 0} weeks</div>
                  <div className="metric-subtext">{timeline.totalMonths || 0} months</div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-label">Team Velocity</div>
                  <div className="metric-value">
                    {(resourceConfig.fteCount * resourceConfig.hoursPerDay * resourceConfig.daysPerWeek * (resourceConfig.utilizationRate / 100)).toFixed(0)} hrs/week
                  </div>
                  <div className="metric-subtext">{resourceConfig.fteCount} FTE @ {resourceConfig.utilizationRate}%</div>
                </div>
                
                <div className="metric-card">
                  <div className="metric-label">Completion Date</div>
                  <div className="metric-value">
                    {timeline.endDate ? timeline.endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }) : 'TBD'}
                  </div>
                  <div className="metric-subtext">
                    {timeline.endDate ? timeline.endDate.toLocaleDateString('en-US', { year: 'numeric' }) : 'Pending'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Implementation Timeline */}
          <div className="timeline-card">
            <div className="card-header">
              <h2>
                <Calendar size={20} />
                {CALCULATOR_SECTIONS.TIMELINE}
              </h2>
            </div>
            
            <div className="timeline-content">
              <div className="timeline-header">
                <div className="timeline-dates">
                  <span className="start-date">
                    {timeline.startDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                  <ChevronRight size={16} />
                  <span className="end-date">
                    {timeline.endDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}
                  </span>
                </div>
              </div>
              
              <div className="milestones">
                {timeline.milestones.map((milestone, index) => (
                  <div key={index} className="milestone">
                    <div className="milestone-info">
                      <span className="milestone-phase">{milestone.phase}</span>
                      <span className="milestone-duration">{milestone.duration} weeks</span>
                    </div>
                    <div className="milestone-progress">
                      <div 
                        className="progress-bar"
                        style={{ width: `${milestone.completion}%` }}
                      />
                    </div>
                    <span className="milestone-percentage">{milestone.completion}%</span>
                  </div>
                ))}
              </div>
              
              <div className="timeline-summary">
                <div className="summary-item">
                  <BarChart3 size={16} />
                  <span>Average velocity: {timeline.totalWeeks > 0 ? (totalEffort / timeline.totalWeeks).toFixed(0) : 0} hrs/week</span>
                </div>
                <div className="summary-item">
                  <TrendingUp size={16} />
                  <span>Peak capacity: {(resourceConfig.fteCount * 40)} hrs/week</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};