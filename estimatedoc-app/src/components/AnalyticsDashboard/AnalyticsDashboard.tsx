import React, { useState, useMemo } from 'react';
import { useDocumentStore } from '../../store/documentStore';
import { useCalculatorStore } from '../../store/calculatorStore';
import { 
  TrendingUp, Activity, 
  FileText, Clock, Layers, Download,
  ChevronUp, ChevronDown, Info, Target, Zap
} from 'lucide-react';
import './AnalyticsDashboard.css';

export const AnalyticsDashboard: React.FC = () => {
  const { filteredDocuments, getStatistics } = useDocumentStore();
  const { settings: calculatorSettings } = useCalculatorStore();
  const [activeView, setActiveView] = useState<'overview' | 'complexity' | 'efficiency' | 'fields'>('overview');
  const stats = getStatistics();

  // Calculate advanced analytics
  const analytics = useMemo(() => {
    // Field type distribution
    const fieldTypeDistribution = filteredDocuments.reduce((acc, doc) => {
      Object.entries(doc.fields).forEach(([type, field]) => {
        if (!acc[type]) acc[type] = { count: 0, percentage: 0 };
        acc[type].count += field.count;
      });
      return acc;
    }, {} as Record<string, { count: number; percentage: number }>);

    const totalFieldCount = Object.values(fieldTypeDistribution).reduce((sum, f) => sum + f.count, 0);
    Object.values(fieldTypeDistribution).forEach(field => {
      field.percentage = (field.count / totalFieldCount) * 100;
    });

    // Complexity trends
    const complexityTrends = {
      simple: stats.byComplexity['Simple'] || 0,
      moderate: stats.byComplexity['Moderate'] || 0,
      complex: stats.byComplexity['Complex'] || 0,
      simplePercentage: ((stats.byComplexity['Simple'] || 0) / stats.total) * 100,
      moderatePercentage: ((stats.byComplexity['Moderate'] || 0) / stats.total) * 100,
      complexPercentage: ((stats.byComplexity['Complex'] || 0) / stats.total) * 100
    };

    // Efficiency metrics
    const efficiencyMetrics = {
      totalSavings: stats.totalEffort - stats.totalOptimizedEffort,
      savingsPercentage: ((stats.totalEffort - stats.totalOptimizedEffort) / stats.totalEffort) * 100,
      averageEffortPerDoc: stats.totalEffort / stats.total,
      averageOptimizedPerDoc: stats.totalOptimizedEffort / stats.total,
      highReuseDocs: filteredDocuments.filter(d => parseFloat(d.totals.reuseRate) > 60).length,
      lowReuseDocs: filteredDocuments.filter(d => parseFloat(d.totals.reuseRate) < 30).length
    };

    // Top performers (most efficient documents)
    const topPerformers = [...filteredDocuments]
      .sort((a, b) => b.effort.savings - a.effort.savings)
      .slice(0, 5);

    // Field complexity analysis
    const fieldComplexity = filteredDocuments.reduce((acc, doc) => {
      const scriptCount = doc.fields.precedentScript.count + 
                         doc.fields.builtInScript.count + 
                         doc.fields.scripted.count;
      if (scriptCount === 0) acc.noScripts++;
      else if (scriptCount < 5) acc.fewScripts++;
      else acc.manyScripts++;
      return acc;
    }, { noScripts: 0, fewScripts: 0, manyScripts: 0 });

    return {
      fieldTypeDistribution,
      complexityTrends,
      efficiencyMetrics,
      topPerformers,
      fieldComplexity
    };
  }, [filteredDocuments, stats]);

  const formatHours = (hours: number) => {
    if (hours < 1) return `${Math.round(hours * 60)}m`;
    if (hours > 1000) return `${(hours / 1000).toFixed(1)}k hrs`;
    return `${hours.toFixed(1)}h`;
  };

  const formatPercentage = (value: number) => `${value.toFixed(1)}%`;

  const handleExport = () => {
    const exportData = {
      timestamp: new Date().toISOString(),
      summary: {
        totalDocuments: stats.total,
        totalEffortHours: stats.totalEffort.toFixed(2),
        totalOptimizedHours: stats.totalOptimizedEffort.toFixed(2),
        totalSavings: (stats.totalEffort - stats.totalOptimizedEffort).toFixed(2),
        averageReusability: `${stats.averageReusability.toFixed(1)}%`
      },
      complexityBreakdown: stats.byComplexity,
      documents: filteredDocuments.map(doc => ({
        name: doc.name,
        complexity: doc.complexity.level,
        fields: doc.totals.allFields,
        effort: doc.effort.calculated.toFixed(2),
        optimized: doc.effort.optimized.toFixed(2),
        savings: doc.effort.savings.toFixed(2),
        reusability: doc.totals.reuseRate,
        source: doc.evidence.source
      })),
      fieldAnalysis: analytics.fieldTypeDistribution,
      efficiencyMetrics: {
        totalSavings: analytics.efficiencyMetrics.totalSavings.toFixed(2),
        savingsPercentage: analytics.efficiencyMetrics.savingsPercentage.toFixed(1),
        highReuseDocs: analytics.efficiencyMetrics.highReuseDocs,
        lowReuseDocs: analytics.efficiencyMetrics.lowReuseDocs
      },
      calculatorSettings: {
        fieldTimeEstimates: Object.entries(calculatorSettings.fieldTimeEstimates).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: value.current
        }), {}),
        complexityThresholds: calculatorSettings.complexityThresholds,
        complexityMultipliers: Object.entries(calculatorSettings.complexityMultipliers).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: value.current
        }), {}),
        optimization: Object.entries(calculatorSettings.optimization).reduce((acc, [key, value]) => ({
          ...acc,
          [key]: value.current
        }), {})
      }
    };

    // Create and download JSON file
    const blob = new Blob([JSON.stringify(exportData, null, 2)], { type: 'application/json' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `estimatedoc-analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);

    // Also generate CSV for the documents
    const csvHeaders = ['Document Name', 'Complexity', 'Total Fields', 'Effort (hrs)', 'Optimized (hrs)', 'Savings (hrs)', 'Reusability (%)', 'Source'];
    const csvRows = filteredDocuments.map(doc => [
      doc.name,
      doc.complexity.level,
      doc.totals.allFields,
      doc.effort.calculated.toFixed(2),
      doc.effort.optimized.toFixed(2),
      doc.effort.savings.toFixed(2),
      doc.totals.reuseRate,
      doc.evidence.source
    ]);
    
    const csvContent = [
      csvHeaders.join(','),
      ...csvRows.map(row => row.map(cell => `"${cell}"`).join(','))
    ].join('\n');

    const csvBlob = new Blob([csvContent], { type: 'text/csv' });
    const csvUrl = URL.createObjectURL(csvBlob);
    const csvLink = document.createElement('a');
    csvLink.href = csvUrl;
    csvLink.download = `estimatedoc-documents-${new Date().toISOString().split('T')[0]}.csv`;
    document.body.appendChild(csvLink);
    csvLink.click();
    document.body.removeChild(csvLink);
    URL.revokeObjectURL(csvUrl);
  };

  return (
    <div className="analytics-dashboard glass-panel">
      {/* Dashboard Header */}
      <div className="dashboard-header">
        <h2 className="headline-medium">Analytics Dashboard</h2>
        <div className="view-tabs">
          <button 
            className={`tab-button ${activeView === 'overview' ? 'active' : ''}`}
            onClick={() => setActiveView('overview')}
          >
            <Activity size={18} />
            Overview
          </button>
          <button 
            className={`tab-button ${activeView === 'complexity' ? 'active' : ''}`}
            onClick={() => setActiveView('complexity')}
          >
            <Layers size={18} />
            Complexity
          </button>
          <button 
            className={`tab-button ${activeView === 'efficiency' ? 'active' : ''}`}
            onClick={() => setActiveView('efficiency')}
          >
            <TrendingUp size={18} />
            Efficiency
          </button>
          <button 
            className={`tab-button ${activeView === 'fields' ? 'active' : ''}`}
            onClick={() => setActiveView('fields')}
          >
            <FileText size={18} />
            Fields
          </button>
        </div>
      </div>

      {/* Overview Tab */}
      {activeView === 'overview' && (
        <div className="dashboard-content">
          {/* Key Metrics Cards */}
          <div className="metrics-grid">
            <div className="metric-card glass-card primary">
              <div className="metric-icon">
                <FileText size={24} />
              </div>
              <div className="metric-details">
                <span className="metric-value">{stats.total}</span>
                <span className="metric-label">Total Documents</span>
                <div className="metric-trend">
                  <ChevronUp size={16} />
                  <span>100% analyzed</span>
                </div>
              </div>
            </div>

            <div className="metric-card glass-card success">
              <div className="metric-icon">
                <Clock size={24} />
              </div>
              <div className="metric-details">
                <span className="metric-value">{formatHours(stats.totalEffort)}</span>
                <span className="metric-label">Total Effort</span>
                <div className="metric-trend">
                  <ChevronDown size={16} />
                  <span>{formatPercentage(analytics.efficiencyMetrics.savingsPercentage)} optimized</span>
                </div>
              </div>
            </div>

            <div className="metric-card glass-card warning">
              <div className="metric-icon">
                <Zap size={24} />
              </div>
              <div className="metric-details">
                <span className="metric-value">{formatHours(analytics.efficiencyMetrics.totalSavings)}</span>
                <span className="metric-label">Total Savings</span>
                <div className="metric-trend positive">
                  <TrendingUp size={16} />
                  <span>Efficiency gain</span>
                </div>
              </div>
            </div>

            <div className="metric-card glass-card info">
              <div className="metric-icon">
                <Target size={24} />
              </div>
              <div className="metric-details">
                <span className="metric-value">{formatPercentage(stats.averageReusability)}</span>
                <span className="metric-label">Avg Reusability</span>
                <div className="metric-trend">
                  <Info size={16} />
                  <span>Field reuse rate</span>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Stats */}
          <div className="quick-stats glass-card">
            <h3 className="title-large">Project Overview</h3>
            <div className="stats-grid">
              <div className="stat-item">
                <span className="stat-label">Simple Documents</span>
                <div className="stat-bar">
                  <div 
                    className="stat-fill simple"
                    style={{ width: `${analytics.complexityTrends.simplePercentage}%` }}
                  />
                </div>
                <span className="stat-value">{analytics.complexityTrends.simple}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Moderate Documents</span>
                <div className="stat-bar">
                  <div 
                    className="stat-fill moderate"
                    style={{ width: `${analytics.complexityTrends.moderatePercentage}%` }}
                  />
                </div>
                <span className="stat-value">{analytics.complexityTrends.moderate}</span>
              </div>
              <div className="stat-item">
                <span className="stat-label">Complex Documents</span>
                <div className="stat-bar">
                  <div 
                    className="stat-fill complex"
                    style={{ width: `${analytics.complexityTrends.complexPercentage}%` }}
                  />
                </div>
                <span className="stat-value">{analytics.complexityTrends.complex}</span>
              </div>
            </div>
          </div>

          {/* Top Performers */}
          <div className="top-performers glass-card">
            <h3 className="title-large">Top Efficiency Gains</h3>
            <div className="performers-list">
              {analytics.topPerformers.map((doc, index) => (
                <div key={doc.id} className="performer-item">
                  <span className="performer-rank">#{index + 1}</span>
                  <div className="performer-info">
                    <span className="performer-name">{doc.name}</span>
                    <span className="performer-savings">
                      Saves {formatHours(doc.effort.savings)}
                    </span>
                  </div>
                  <div className="performer-badge">
                    {formatPercentage((doc.effort.savings / doc.effort.calculated) * 100)}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Complexity Tab */}
      {activeView === 'complexity' && (
        <div className="dashboard-content">
          <div className="complexity-analysis glass-card">
            <h3 className="title-large">Complexity Distribution</h3>
            
            {/* Pie Chart Visualization */}
            <div className="chart-container">
              <div className="pie-chart">
                <svg viewBox="0 0 200 200" className="donut-chart">
                  <circle
                    cx="100"
                    cy="100"
                    r="80"
                    fill="none"
                    stroke="var(--alterspective-citrus)"
                    strokeWidth="30"
                    strokeDasharray={`${analytics.complexityTrends.simplePercentage * 5.03} 503`}
                    transform="rotate(-90 100 100)"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="80"
                    fill="none"
                    stroke="#FFC107"
                    strokeWidth="30"
                    strokeDasharray={`${analytics.complexityTrends.moderatePercentage * 5.03} 503`}
                    strokeDashoffset={`${-analytics.complexityTrends.simplePercentage * 5.03}`}
                    transform="rotate(-90 100 100)"
                  />
                  <circle
                    cx="100"
                    cy="100"
                    r="80"
                    fill="none"
                    stroke="var(--alterspective-marine)"
                    strokeWidth="30"
                    strokeDasharray={`${analytics.complexityTrends.complexPercentage * 5.03} 503`}
                    strokeDashoffset={`${-(analytics.complexityTrends.simplePercentage + analytics.complexityTrends.moderatePercentage) * 5.03}`}
                    transform="rotate(-90 100 100)"
                  />
                  <text x="100" y="100" textAnchor="middle" className="chart-center-text">
                    <tspan x="100" dy="-10" className="chart-value">{stats.total}</tspan>
                    <tspan x="100" dy="25" className="chart-label">Documents</tspan>
                  </text>
                </svg>
              </div>
              
              <div className="chart-legend">
                <div className="legend-item">
                  <span className="legend-color simple"></span>
                  <span className="legend-label">Simple</span>
                  <span className="legend-value">{formatPercentage(analytics.complexityTrends.simplePercentage)}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-color moderate"></span>
                  <span className="legend-label">Moderate</span>
                  <span className="legend-value">{formatPercentage(analytics.complexityTrends.moderatePercentage)}</span>
                </div>
                <div className="legend-item">
                  <span className="legend-color complex"></span>
                  <span className="legend-label">Complex</span>
                  <span className="legend-value">{formatPercentage(analytics.complexityTrends.complexPercentage)}</span>
                </div>
              </div>
            </div>

            {/* Script Analysis */}
            <div className="script-analysis">
              <h4 className="title-medium">Script Complexity</h4>
              <div className="script-bars">
                <div className="script-bar-item">
                  <span className="script-label">No Scripts</span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill success"
                      style={{ width: `${(analytics.fieldComplexity.noScripts / stats.total) * 100}%` }}
                    />
                  </div>
                  <span className="script-count">{analytics.fieldComplexity.noScripts}</span>
                </div>
                <div className="script-bar-item">
                  <span className="script-label">Few Scripts (1-4)</span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill warning"
                      style={{ width: `${(analytics.fieldComplexity.fewScripts / stats.total) * 100}%` }}
                    />
                  </div>
                  <span className="script-count">{analytics.fieldComplexity.fewScripts}</span>
                </div>
                <div className="script-bar-item">
                  <span className="script-label">Many Scripts (5+)</span>
                  <div className="progress-bar">
                    <div 
                      className="progress-fill error"
                      style={{ width: `${(analytics.fieldComplexity.manyScripts / stats.total) * 100}%` }}
                    />
                  </div>
                  <span className="script-count">{analytics.fieldComplexity.manyScripts}</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Efficiency Tab */}
      {activeView === 'efficiency' && (
        <div className="dashboard-content">
          <div className="efficiency-report glass-card">
            <h3 className="title-large">Efficiency Analysis</h3>
            
            <div className="efficiency-metrics">
              <div className="efficiency-card">
                <div className="efficiency-header">
                  <Clock size={20} />
                  <span>Time Analysis</span>
                </div>
                <div className="efficiency-stats">
                  <div className="efficiency-stat">
                    <span className="stat-label">Original Effort</span>
                    <span className="stat-value">{formatHours(stats.totalEffort)}</span>
                  </div>
                  <div className="efficiency-stat">
                    <span className="stat-label">Optimized Effort</span>
                    <span className="stat-value success">{formatHours(stats.totalOptimizedEffort)}</span>
                  </div>
                  <div className="efficiency-stat highlighted">
                    <span className="stat-label">Total Savings</span>
                    <span className="stat-value primary">{formatHours(analytics.efficiencyMetrics.totalSavings)}</span>
                  </div>
                </div>
              </div>

              <div className="efficiency-card">
                <div className="efficiency-header">
                  <TrendingUp size={20} />
                  <span>Reusability Impact</span>
                </div>
                <div className="efficiency-stats">
                  <div className="efficiency-stat">
                    <span className="stat-label">High Reuse Docs (&gt;60%)</span>
                    <span className="stat-value">{analytics.efficiencyMetrics.highReuseDocs}</span>
                  </div>
                  <div className="efficiency-stat">
                    <span className="stat-label">Low Reuse Docs (&lt;30%)</span>
                    <span className="stat-value">{analytics.efficiencyMetrics.lowReuseDocs}</span>
                  </div>
                  <div className="efficiency-stat">
                    <span className="stat-label">Average Reuse Rate</span>
                    <span className="stat-value">{formatPercentage(stats.averageReusability)}</span>
                  </div>
                </div>
              </div>
            </div>

            <div className="savings-visualization">
              <h4 className="title-medium">Savings Breakdown</h4>
              <div className="savings-chart">
                <div className="savings-bar original">
                  <span className="bar-label">Original</span>
                  <div className="bar-fill" style={{ width: '100%' }}>
                    <span className="bar-value">{formatHours(stats.totalEffort)}</span>
                  </div>
                </div>
                <div className="savings-bar optimized">
                  <span className="bar-label">Optimized</span>
                  <div 
                    className="bar-fill" 
                    style={{ width: `${(stats.totalOptimizedEffort / stats.totalEffort) * 100}%` }}
                  >
                    <span className="bar-value">{formatHours(stats.totalOptimizedEffort)}</span>
                  </div>
                </div>
                <div className="savings-indicator">
                  <Zap size={20} />
                  <span>{formatPercentage(analytics.efficiencyMetrics.savingsPercentage)} Reduction</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Fields Tab */}
      {activeView === 'fields' && (
        <div className="dashboard-content">
          <div className="fields-analysis glass-card">
            <h3 className="title-large">Field Type Distribution</h3>
            
            <div className="field-distribution">
              {Object.entries(analytics.fieldTypeDistribution).map(([type, data]) => (
                <div key={type} className="field-type-card">
                  <div className="field-type-header">
                    <Layers size={18} />
                    <span className="field-type-name">
                      {type.replace(/([A-Z])/g, ' $1').trim()}
                    </span>
                  </div>
                  <div className="field-type-stats">
                    <div className="field-count">{data.count.toLocaleString()}</div>
                    <div className="field-percentage">{formatPercentage(data.percentage)}</div>
                  </div>
                  <div className="field-bar">
                    <div 
                      className="field-bar-fill"
                      style={{ width: `${data.percentage}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Export Button */}
      <div className="dashboard-actions">
        <button className="export-button" onClick={handleExport}>
          <Download size={18} />
          Export Report
        </button>
      </div>
    </div>
  );
};