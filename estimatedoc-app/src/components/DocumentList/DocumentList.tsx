import React, { useState } from 'react';
import { useDocumentStore } from '../../store/documentStore';
import { DocumentCard } from '../DocumentCard/DocumentCard';
import { DocumentDetail } from '../DocumentDetail/DocumentDetail';
import { Search, Filter, SortAsc, SortDesc, X } from 'lucide-react';
import './DocumentList.css';

export const DocumentList: React.FC = () => {
  const { 
    filteredDocuments, 
    selectedDocument,
    setSelectedDocument,
    filter,
    sort,
    setFilter,
    setSort,
    getStatistics
  } = useDocumentStore();

  const [searchTerm, setSearchTerm] = useState('');
  const [showFilters, setShowFilters] = useState(false);

  const stats = getStatistics();

  const handleSearch = (value: string) => {
    setSearchTerm(value);
    setFilter({ ...filter, searchTerm: value });
  };

  const handleComplexityFilter = (complexity: 'Simple' | 'Moderate' | 'Complex' | null) => {
    setFilter({ ...filter, complexity });
  };

  const handleSourceFilter = (source: 'SQL' | 'Estimated' | null) => {
    setFilter({ ...filter, source });
  };

  const handleSort = (field: typeof sort.field) => {
    if (sort.field === field) {
      setSort({ field, direction: sort.direction === 'asc' ? 'desc' : 'asc' });
    } else {
      setSort({ field, direction: 'asc' });
    }
  };

  const clearFilters = () => {
    setSearchTerm('');
    setFilter({});
  };

  return (
    <div className="document-list-container">
      {/* Header with Search and Filters */}
      <div className="list-header glass-panel">
        <div className="search-bar">
          <Search size={20} className="search-icon" />
          <input
            type="text"
            placeholder="Search documents..."
            value={searchTerm}
            onChange={(e) => handleSearch(e.target.value)}
            className="search-input body-large"
          />
          {searchTerm && (
            <button 
              onClick={() => handleSearch('')}
              className="clear-search"
              aria-label="Clear search"
            >
              <X size={16} />
            </button>
          )}
        </div>

        <button 
          className="filter-button"
          onClick={() => setShowFilters(!showFilters)}
          aria-expanded={showFilters}
        >
          <Filter size={20} />
          <span>Filters</span>
          {(filter.complexity || filter.source) && (
            <span className="filter-badge">Active</span>
          )}
        </button>
      </div>

      {/* Filter Panel */}
      {showFilters && (
        <div className="filter-panel glass-panel">
          <div className="filter-section">
            <h3 className="label-large">Complexity</h3>
            <div className="filter-chips">
              <button
                className={`chip ${filter.complexity === null ? 'active' : ''}`}
                onClick={() => handleComplexityFilter(null)}
              >
                All
              </button>
              <button
                className={`chip ${filter.complexity === 'Simple' ? 'active' : ''}`}
                onClick={() => handleComplexityFilter('Simple')}
              >
                Simple
              </button>
              <button
                className={`chip ${filter.complexity === 'Moderate' ? 'active' : ''}`}
                onClick={() => handleComplexityFilter('Moderate')}
              >
                Moderate
              </button>
              <button
                className={`chip ${filter.complexity === 'Complex' ? 'active' : ''}`}
                onClick={() => handleComplexityFilter('Complex')}
              >
                Complex
              </button>
            </div>
          </div>

          <div className="filter-section">
            <h3 className="label-large">Data Source</h3>
            <div className="filter-chips">
              <button
                className={`chip ${filter.source === null ? 'active' : ''}`}
                onClick={() => handleSourceFilter(null)}
              >
                All
              </button>
              <button
                className={`chip ${filter.source === 'SQL' ? 'active' : ''}`}
                onClick={() => handleSourceFilter('SQL')}
              >
                SQL Data
              </button>
              <button
                className={`chip ${filter.source === 'Estimated' ? 'active' : ''}`}
                onClick={() => handleSourceFilter('Estimated')}
              >
                Estimated
              </button>
            </div>
          </div>

          {(filter.complexity || filter.source || searchTerm) && (
            <button className="clear-filters-button" onClick={clearFilters}>
              Clear All Filters
            </button>
          )}
        </div>
      )}

      {/* Statistics Bar */}
      <div className="statistics-bar">
        <div className="stat-item">
          <span className="label-small">Documents</span>
          <span className="title-medium">{stats.total}</span>
        </div>
        <div className="stat-item">
          <span className="label-small">Total Effort</span>
          <span className="title-medium">{stats.totalEffort.toFixed(0)}h</span>
        </div>
        <div className="stat-item">
          <span className="label-small">Optimized</span>
          <span className="title-medium">{stats.totalOptimizedEffort.toFixed(0)}h</span>
        </div>
        <div className="stat-item">
          <span className="label-small">Avg Reusability</span>
          <span className="title-medium">{stats.averageReusability.toFixed(1)}%</span>
        </div>
      </div>

      {/* Sort Controls */}
      <div className="sort-controls">
        <span className="label-medium">Sort by:</span>
        <div className="sort-buttons">
          {(['name', 'complexity', 'effort', 'fields', 'reusability'] as const).map(field => (
            <button
              key={field}
              className={`sort-button ${sort.field === field ? 'active' : ''}`}
              onClick={() => handleSort(field)}
            >
              {field.charAt(0).toUpperCase() + field.slice(1)}
              {sort.field === field && (
                sort.direction === 'asc' ? <SortAsc size={14} /> : <SortDesc size={14} />
              )}
            </button>
          ))}
        </div>
      </div>

      {/* Document Grid */}
      <div className="document-grid">
        {filteredDocuments.map(document => (
          <DocumentCard
            key={document.id}
            document={document}
            onClick={setSelectedDocument}
            selected={selectedDocument?.id === document.id}
          />
        ))}
      </div>

      {/* Document Detail Modal */}
      {selectedDocument && (
        <DocumentDetail
          document={selectedDocument}
          onClose={() => setSelectedDocument(null)}
        />
      )}
    </div>
  );
};