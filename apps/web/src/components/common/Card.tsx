'use client';

import React from 'react';

interface CardProps {
  children: React.ReactNode;
  className?: string;
  title?: string;
  subtitle?: string;
  noPadding?: boolean;
  clickable?: boolean;
  onClick?: () => void;
}

/**
 * Reusable Card component for dashboard sections
 */
export const Card: React.FC<CardProps> = ({
  children,
  className = '',
  title,
  subtitle,
  noPadding = false,
  clickable = false,
  onClick,
}) => {
  const baseClasses =
    'bg-gray-800/50 border border-gray-700 rounded-lg backdrop-blur-sm transition-all';
  const hoverClasses = clickable ? 'hover:bg-gray-700/50 hover:border-gray-600 cursor-pointer' : '';
  const paddingClasses = noPadding ? '' : 'p-6';

  return (
    <div
      className={`${baseClasses} ${hoverClasses} ${paddingClasses} ${className}`}
      onClick={onClick}
    >
      {(title || subtitle) && (
        <div className="mb-4 border-b border-gray-700 pb-4">
          {title && <h3 className="text-lg font-semibold text-white">{title}</h3>}
          {subtitle && <p className="text-sm text-gray-400 mt-1">{subtitle}</p>}
        </div>
      )}
      {children}
    </div>
  );
};
