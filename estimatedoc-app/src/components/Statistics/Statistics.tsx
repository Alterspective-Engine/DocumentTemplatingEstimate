import React from 'react';
import { useDocumentStore } from '../../store/documentStore';
import { useHistoryStore } from '../../store/historyStore';
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { FileText, Clock, TrendingUp, Layers } from 'lucide-react';
import { MiniGraph } from '../MiniGraph/MiniGraph';
import './Statistics.css';

export const Statistics: React.FC = () => {
  const { documents } = useDocumentStore();
  const { globalHistory } = useHistoryStore();
  
  // Get history for global metrics
  const effortHistory = globalHistory.totalEffort.map(h => h.value);
  const optimizedHistory = globalHistory.totalOptimized.map(h => h.value);
  const savingsHistory = globalHistory.totalSavings.map(h => h.value);
  const reusabilityHistory = globalHistory.averageReusability.map(h => h.value);

  // Calculate statistics
  const complexityData = [
    { name: 'Simple', value: documents.filter(d => d.complexity.level === 'Simple').length, color: '#7DFC8A' },
    { name: 'Moderate', value: documents.filter(d => d.complexity.level === 'Moderate').length, color: '#FFDEA5' },
    { name: 'Complex', value: documents.filter(d => d.complexity.level === 'Complex').length, color: '#FFDAD6' }
  ];

  const effortData = [
    { 
      name: 'Simple', 
      calculated: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Simple' || complexity === 'simple';
      }).reduce((sum, d) => sum + (d.effort?.calculated || 0), 0),
      optimized: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Simple' || complexity === 'simple';
      }).reduce((sum, d) => sum + (d.effort?.optimized || 0), 0)
    },
    { 
      name: 'Moderate', 
      calculated: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Moderate' || complexity === 'moderate';
      }).reduce((sum, d) => sum + (d.effort?.calculated || 0), 0),
      optimized: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Moderate' || complexity === 'moderate';
      }).reduce((sum, d) => sum + (d.effort?.optimized || 0), 0)
    },
    { 
      name: 'Complex', 
      calculated: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Complex' || complexity === 'complex';
      }).reduce((sum, d) => sum + (d.effort?.calculated || 0), 0),
      optimized: documents.filter(d => {
        const complexity = (d.complexity as any)?.level || d.complexity;
        return complexity === 'Complex' || complexity === 'complex';
      }).reduce((sum, d) => sum + (d.effort?.optimized || 0), 0)
    }
  ];

  const totalStats = {
    documents: documents.length,
    totalFields: documents.reduce((sum, d) => sum + (d.totals?.allFields || 0), 0),
    totalEffort: documents.reduce((sum, d) => sum + (d.effort?.calculated || 0), 0),
    totalOptimized: documents.reduce((sum, d) => sum + (d.effort?.optimized || 0), 0),
    totalSavings: documents.reduce((sum, d) => sum + (d.effort?.savings || 0), 0),
    avgReusability: documents.reduce((sum, d) => sum + (d.reusability || 0), 0) / (documents.length || 1)
  };

  const fieldTypeData = [
    { name: 'IF Statements', value: documents.reduce((sum, d) => {
      const fields = d.fields && typeof d.fields === 'object' ? d.fields : null;
      return sum + (fields?.if?.count || 0);
    }, 0) },
    { name: 'Scripts', value: documents.reduce((sum, d) => {
      const fields = d.fields && typeof d.fields === 'object' ? d.fields : null;
      return sum + (fields?.precedentScript?.count || 0) + (fields?.scripted?.count || 0) + (fields?.builtInScript?.count || 0);
    }, 0) },
    { name: 'Search', value: documents.reduce((sum, d) => {
      const fields = d.fields && typeof d.fields === 'object' ? d.fields : null;
      return sum + (fields?.search?.count || 0);
    }, 0) },
    { name: 'Reflection', value: documents.reduce((sum, d) => {
      const fields = d.fields && typeof d.fields === 'object' ? d.fields : null;
      return sum + (fields?.reflection?.count || 0);
    }, 0) },
    { name: 'Other', value: documents.reduce((sum, d) => {
      const fields = d.fields && typeof d.fields === 'object' ? d.fields : null;
      return sum + (fields?.unbound?.count || 0) + (fields?.extended?.count || 0);
    }, 0) }
  ];

  return (
    <div className="statistics-container">
      <div className="statistics-header">
        <h1 className="headline-large">Project Statistics</h1>
        <p className="body-large">Comprehensive analysis of all {totalStats.documents} documents</p>
      </div>

      {/* Overview Cards */}
      <div className="stats-grid">
        <div className="stat-card glass-card">
          <div className="stat-icon">
            <FileText size={24} />
          </div>
          <div className="stat-content">
            <span className="label-medium">Total Documents</span>
            <span className="display-small">{totalStats.documents}</span>
          </div>
        </div>

        <div className="stat-card glass-card">
          <div className="stat-icon">
            <Layers size={24} />
          </div>
          <div className="stat-content">
            <span className="label-medium">Total Fields</span>
            <span className="display-small">{totalStats.totalFields.toLocaleString()}</span>
          </div>
        </div>

        <div className="stat-card glass-card">
          <div className="stat-icon">
            <Clock size={24} />
          </div>
          <div className="stat-content">
            <span className="label-medium">Total Effort</span>
            <div className="stat-value-with-graph">
              <span className="display-small">{totalStats.totalEffort.toFixed(0)}h</span>
              {effortHistory.length > 1 && (
                <MiniGraph 
                  data={effortHistory} 
                  width={60} 
                  height={24}
                  color="#006494"
                  showTrend={true}
                />
              )}
            </div>
            <div className="stat-sub-value">
              <span className="label-small">Optimized: {totalStats.totalOptimized.toFixed(0)}h</span>
              {optimizedHistory.length > 1 && (
                <MiniGraph 
                  data={optimizedHistory} 
                  width={40} 
                  height={16}
                  color="#65558F"
                  showTrend={false}
                />
              )}
            </div>
          </div>
        </div>

        <div className="stat-card glass-card">
          <div className="stat-icon">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <span className="label-medium">Potential Savings</span>
            <div className="stat-value-with-graph">
              <span className="display-small">{totalStats.totalSavings.toFixed(0)}h</span>
              {savingsHistory.length > 1 && (
                <MiniGraph 
                  data={savingsHistory} 
                  width={60} 
                  height={24}
                  color="#ABDD65"
                  showTrend={true}
                />
              )}
            </div>
            <div className="stat-sub-value">
              <span className="label-small">Avg Reuse: {totalStats.avgReusability.toFixed(1)}%</span>
              {reusabilityHistory.length > 1 && (
                <MiniGraph 
                  data={reusabilityHistory} 
                  width={40} 
                  height={16}
                  color="#2C8248"
                  showTrend={false}
                />
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Charts */}
      <div className="charts-grid">
        {/* Complexity Distribution */}
        <div className="chart-card glass-card">
          <h2 className="title-large">Complexity Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={complexityData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value, percent }: any) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {complexityData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={entry.color} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Effort Comparison */}
        <div className="chart-card glass-card">
          <h2 className="title-large">Effort by Complexity</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={effortData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="calculated" fill="#006494" name="Calculated Hours" />
              <Bar dataKey="optimized" fill="#65558F" name="Optimized Hours" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Field Types Distribution */}
        <div className="chart-card glass-card full-width">
          <h2 className="title-large">Field Types Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={fieldTypeData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis />
              <Tooltip />
              <Bar dataKey="value" fill="#50606E" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Top Documents Table */}
      <div className="table-card glass-card">
        <h2 className="title-large">Top Complex Documents</h2>
        <table className="stats-table">
          <thead>
            <tr>
              <th>Document</th>
              <th>Fields</th>
              <th>Complexity</th>
              <th>Effort (hrs)</th>
              <th>Reusability</th>
            </tr>
          </thead>
          <tbody>
            {documents
              .sort((a, b) => (b.effort?.calculated || 0) - (a.effort?.calculated || 0))
              .slice(0, 10)
              .map(doc => (
                <tr key={doc.id}>
                  <td>{doc.name}</td>
                  <td>{doc.totals?.allFields || 0}</td>
                  <td>
                    <span className={`complexity-badge ${doc.complexity.level.toLowerCase()}`}>
                      {doc.complexity.level}
                    </span>
                  </td>
                  <td>{(doc.effort?.calculated || 0).toFixed(1)}</td>
                  <td>{doc.totals?.reuseRate || '0%'}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};