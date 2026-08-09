/**
 * Skip Link Component
 * 
 * WCAG 2.4.1: Bypass Blocks
 * Provides keyboard users a way to skip repetitive navigation
 * and jump directly to main content.
 * 
 * Accessibility Features:
 * - Visually hidden until focused
 * - High contrast emerald theme for visibility
 * - Proper focus ring styling
 */
import React from 'react';

const SkipLink = ({ targetId = 'main-content', children = 'Skip to main content' }) => {
  return (
    <a 
      href={`#${targetId}`}
      className="skip-link"
      data-testid="skip-link"
    >
      {children}
    </a>
  );
};

export default SkipLink;
