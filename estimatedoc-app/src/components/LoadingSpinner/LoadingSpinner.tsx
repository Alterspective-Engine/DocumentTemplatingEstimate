import React from 'react';
import './LoadingSpinner.css';

interface LoadingSpinnerProps {
  size?: 'small' | 'medium' | 'large';
  color?: string;
  text?: string;
}

export const LoadingSpinner: React.FC<LoadingSpinnerProps> = ({ 
  size = 'medium', 
  color = '#075156',
  text
}) => {
  const sizeMap = {
    small: 20,
    medium: 40,
    large: 60
  };

  return (
    <div className="loading-spinner-container">
      <div 
        className="loading-spinner"
        style={{
          width: sizeMap[size],
          height: sizeMap[size],
          borderColor: `${color}20`,
          borderTopColor: color
        }}
      />
      {text && <p className="loading-text">{text}</p>}
    </div>
  );
};