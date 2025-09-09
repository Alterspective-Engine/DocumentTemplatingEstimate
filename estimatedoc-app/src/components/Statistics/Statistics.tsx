import React from 'react';
import { useDocumentStore } from '../../store/documentStore';
import { 
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, 
  CartesianGrid, Tooltip, Legend, ResponsiveContainer 
} from 'recharts';
import { FileText, Clock, TrendingUp, Layers } from 'lucide-react';
import './Statistics.css';

export const Statistics: React.FC = () => {
  const { documents } = useDocumentStore();

  // Calculate statistics
  const complexityData = [
    { name: 'Simple', value: documents.filter(d => d.complexity.level === 'Simple').length, color: '#7DFC8A' },
    { name: 'Moderate', value: documents.filter(d => d.complexity.level === 'Moderate').length, color: '#FFDEA5' },
    { name: 'Complex', value: documents.filter(d => d.complexity.level === 'Complex').length, color: '#FFDAD6' }
  ];

  const effortData = [
    { 
      name: 'Simple', 
      calculated: documents.filter(d => d.complexity.level === 'Simple').reduce((sum, d) => sum + d.effort.calculated, 0),
      optimized: documents.filter(d => d.complexity.level === 'Simple').reduce((sum, d) => sum + d.effort.optimized, 0)
    },
    { 
      name: 'Moderate', 
      calculated: documents.filter(d => d.complexity.level === 'Moderate').reduce((sum, d) => sum + d.effort.calculated, 0),
      optimized: documents.filter(d => d.complexity.level === 'Moderate').reduce((sum, d) => sum + d.effort.optimized, 0)
    },
    { 
      name: 'Complex', 
      calculated: documents.filter(d => d.complexity.level === 'Complex').reduce((sum, d) => sum + d.effort.calculated, 0),
      optimized: documents.filter(d => d.complexity.level === 'Complex').reduce((sum, d) => sum + d.effort.optimized, 0)
    }
  ];

  const totalStats = {
    documents: documents.length,
    totalFields: documents.reduce((sum, d) => sum + d.totals.allFields, 0),
    totalEffort: documents.reduce((sum, d) => sum + d.effort.calculated, 0),
    totalOptimized: documents.reduce((sum, d) => sum + d.effort.optimized, 0),
    totalSavings: documents.reduce((sum, d) => sum + d.effort.savings, 0),
    avgReusability: documents.reduce((sum, d) => sum + parseFloat(d.totals.reuseRate), 0) / documents.length
  };

  const fieldTypeData = [
    { name: 'IF Statements', value: documents.reduce((sum, d) => sum + d.fields.if.count, 0) },
    { name: 'Scripts', value: documents.reduce((sum, d) => sum + d.fields.precedentScript.count + d.fields.scripted.count + d.fields.builtInScript.count, 0) },
    { name: 'Search', value: documents.reduce((sum, d) => sum + d.fields.search.count, 0) },
    { name: 'Reflection', value: documents.reduce((sum, d) => sum + d.fields.reflection.count, 0) },
    { name: 'Other', value: documents.reduce((sum, d) => sum + d.fields.unbound.count + d.fields.extended.count, 0) }
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
            <span className="display-small">{totalStats.totalEffort.toFixed(0)}h</span>
            <span className="label-small">Optimized: {totalStats.totalOptimized.toFixed(0)}h</span>
          </div>
        </div>

        <div className="stat-card glass-card">
          <div className="stat-icon">
            <TrendingUp size={24} />
          </div>
          <div className="stat-content">
            <span className="label-medium">Potential Savings</span>
            <span className="display-small">{totalStats.totalSavings.toFixed(0)}h</span>
            <span className="label-small">Avg Reuse: {totalStats.avgReusability.toFixed(1)}%</span>
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
                label={({ name, value, percent }) => `${name}: ${value} (${(percent * 100).toFixed(0)}%)`}
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
              .sort((a, b) => b.effort.calculated - a.effort.calculated)
              .slice(0, 10)
              .map(doc => (
                <tr key={doc.id}>
                  <td>{doc.name}</td>
                  <td>{doc.totals.allFields}</td>
                  <td>
                    <span className={`complexity-badge ${doc.complexity.level.toLowerCase()}`}>
                      {doc.complexity.level}
                    </span>
                  </td>
                  <td>{doc.effort.calculated.toFixed(1)}</td>
                  <td>{doc.totals.reuseRate}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};