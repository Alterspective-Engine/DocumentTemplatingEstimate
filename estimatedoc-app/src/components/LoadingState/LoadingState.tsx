import React from 'react';
import { Loader2 } from 'lucide-react';
import './LoadingState.css';

interface LoadingStateProps {
  message?: string;
  size?: 'small' | 'medium' | 'large';
  fullScreen?: boolean;
  transparent?: boolean;
}

export const LoadingState: React.FC<LoadingStateProps> = ({
  message = 'Loading...',
  size = 'medium',
  fullScreen = false,
  transparent = false
}) => {
  const sizeClasses = {
    small: 'loading-small',
    medium: 'loading-medium',
    large: 'loading-large'
  };

  if (fullScreen) {
    return (
      <div className={`loading-fullscreen ${transparent ? 'loading-transparent' : ''}`}>
        <div className="loading-content">
          <Loader2 className={`loading-spinner ${sizeClasses[size]}`} />
          <p className="loading-message">{message}</p>
        </div>
      </div>
    );
  }

  return (
    <div className="loading-container">
      <Loader2 className={`loading-spinner ${sizeClasses[size]}`} />
      {message && <p className="loading-message">{message}</p>}
    </div>
  );
};

// Skeleton loader for cards
export const SkeletonCard: React.FC = () => {
  return (
    <div className="skeleton-card">
      <div className="skeleton-header">
        <div className="skeleton-title"></div>
        <div className="skeleton-badge"></div>
      </div>
      <div className="skeleton-content">
        <div className="skeleton-line"></div>
        <div className="skeleton-line skeleton-line-short"></div>
      </div>
      <div className="skeleton-footer">
        <div className="skeleton-stat"></div>
        <div className="skeleton-stat"></div>
        <div className="skeleton-stat"></div>
      </div>
    </div>
  );
};

// Skeleton loader for list items
export const SkeletonList: React.FC<{ count?: number }> = ({ count = 5 }) => {
  return (
    <div className="skeleton-list">
      {Array.from({ length: count }).map((_, index) => (
        <div key={index} className="skeleton-list-item">
          <div className="skeleton-list-icon"></div>
          <div className="skeleton-list-content">
            <div className="skeleton-line skeleton-line-title"></div>
            <div className="skeleton-line skeleton-line-subtitle"></div>
          </div>
        </div>
      ))}
    </div>
  );
};

// Skeleton loader for statistics/charts
export const SkeletonChart: React.FC = () => {
  return (
    <div className="skeleton-chart">
      <div className="skeleton-chart-header">
        <div className="skeleton-title"></div>
        <div className="skeleton-controls">
          <div className="skeleton-button"></div>
          <div className="skeleton-button"></div>
        </div>
      </div>
      <div className="skeleton-chart-body">
        <div className="skeleton-bar skeleton-bar-1"></div>
        <div className="skeleton-bar skeleton-bar-2"></div>
        <div className="skeleton-bar skeleton-bar-3"></div>
        <div className="skeleton-bar skeleton-bar-4"></div>
        <div className="skeleton-bar skeleton-bar-5"></div>
      </div>
    </div>
  );
};

// Progress indicator for multi-step processes
export const ProgressIndicator: React.FC<{
  current: number;
  total: number;
  message?: string;
}> = ({ current, total, message }) => {
  const percentage = (current / total) * 100;
  
  return (
    <div className="progress-indicator">
      <div className="progress-header">
        <span className="progress-message">{message || 'Processing...'}</span>
        <span className="progress-count">{current} / {total}</span>
      </div>
      <div className="progress-bar">
        <div 
          className="progress-fill" 
          style={{ width: `${percentage}%` }}
        />
      </div>
      <div className="progress-percentage">{Math.round(percentage)}%</div>
    </div>
  );
};

// Shimmer effect component
export const ShimmerEffect: React.FC = () => {
  return <div className="shimmer-effect" />;
};