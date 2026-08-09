/**
 * Navigation Component
 * 
 * Premium Enterprise-style navigation with:
 * - Full WCAG 2.1 AA accessibility compliance
 * - Emerald focus rings for keyboard navigation
 * - Responsive design
 * - Authentication-aware menu items
 * 
 * Accessibility Features:
 * - Skip link for keyboard users (WCAG 2.4.1)
 * - Proper ARIA roles and labels
 * - aria-current for active page indication
 * - Visible focus indicators
 */
import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import SkipLink from './SkipLink';

const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  
  const isActive = (path) => location.pathname === path;
  
  // Common link classes for focus rings - WCAG compliant
  const linkBaseClasses = "px-4 py-2 rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400";
  
  return (
    <>
      {/* Skip to main content link for keyboard users - WCAG 2.4.1 */}
      <SkipLink />
      
      <nav 
        className="bg-slate-900 border-b border-slate-800"
        role="navigation"
        aria-label="Main navigation"
      >
        <div className="container mx-auto px-6 py-4">
          <div className="flex justify-between items-center">
            {/* Logo */}
            <Link 
              to="/" 
              className="flex items-center space-x-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded-lg" 
              data-testid="nav-logo"
              aria-label="Auditly - Go to homepage"
            >
              <div 
                className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center" 
                aria-hidden="true"
              >
                <Shield className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <span className="text-xl font-bold text-white tracking-tight">Auditly</span>
                <span className="text-xs text-slate-400 block -mt-1">Accessibility Scanner</span>
              </div>
            </Link>
            
            {/* Navigation Links */}
            <div className="flex items-center space-x-1" role="menubar">
              {isAuthenticated ? (
                <>
                  <Link 
                    to="/" 
                    data-testid="nav-dashboard"
                    role="menuitem"
                    aria-current={isActive('/') ? 'page' : undefined}
                    className={`${linkBaseClasses} ${
                      isActive('/') 
                        ? 'bg-slate-800 text-white' 
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    Dashboard
                  </Link>
                  <Link 
                    to="/scan" 
                    data-testid="nav-new-scan"
                    role="menuitem"
                    aria-current={isActive('/scan') ? 'page' : undefined}
                    className={`${linkBaseClasses} ${
                      isActive('/scan') 
                        ? 'bg-slate-800 text-white' 
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    New Scan
                  </Link>
                  <Link 
                    to="/my-scans" 
                    data-testid="nav-my-scans"
                    role="menuitem"
                    aria-current={isActive('/my-scans') ? 'page' : undefined}
                    className={`${linkBaseClasses} ${
                      isActive('/my-scans') 
                        ? 'bg-slate-800 text-white' 
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    My Scans
                  </Link>
                  <Link 
                    to="/analytics" 
                    data-testid="nav-analytics"
                    role="menuitem"
                    aria-current={isActive('/analytics') ? 'page' : undefined}
                    className={`${linkBaseClasses} ${
                      isActive('/analytics') 
                        ? 'bg-slate-800 text-white' 
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    Analytics
                  </Link>
                  <Link 
                    to="/pricing" 
                    data-testid="nav-pricing"
                    role="menuitem"
                    aria-current={isActive('/pricing') ? 'page' : undefined}
                    className={`${linkBaseClasses} ${
                      isActive('/pricing') 
                        ? 'bg-slate-800 text-white' 
                        : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
                    }`}
                  >
                    Pricing
                  </Link>
                  
                  {/* User Menu */}
                  <div className="flex items-center ml-4 pl-4 border-l border-slate-700">
                    <div className="flex items-center space-x-3">
                      <div className="text-right">
                        <div className="text-sm font-medium text-white">
                          {user?.full_name || user?.email?.split('@')[0]}
                        </div>
                        <div className="flex items-center justify-end space-x-2">
                          <span 
                            className={`text-xs px-2 py-0.5 rounded-full ${
                              user?.plan === 'pro' 
                                ? 'bg-emerald-500/20 text-emerald-300' 
                                : 'bg-slate-700 text-slate-300'
                            }`}
                            aria-label={`Current plan: ${user?.plan}`}
                          >
                            {user?.plan?.toUpperCase()}
                          </span>
                          {user?.scans_remaining !== -1 && (
                            <span 
                              className="text-xs text-slate-400" 
                              aria-label={`${user?.scans_remaining} scans remaining`}
                            >
                              {user?.scans_remaining} left
                            </span>
                          )}
                        </div>
                      </div>
                      <button
                        onClick={logout}
                        data-testid="nav-logout"
                        aria-label="Log out of your account"
                        className="bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-3 py-2 rounded-lg text-sm font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                      >
                        Logout
                      </button>
                    </div>
                  </div>
                </>
              ) : (
                <>
                  <Link 
                    to="/pricing" 
                    data-testid="nav-pricing-guest"
                    role="menuitem"
                    className="px-4 py-2 text-slate-300 hover:text-white text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded-lg"
                  >
                    Pricing
                  </Link>
                  <Link 
                    to="/login" 
                    data-testid="nav-login"
                    role="menuitem"
                    className="px-4 py-2 text-slate-300 hover:text-white text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 rounded-lg"
                  >
                    Login
                  </Link>
                  <Link 
                    to="/signup" 
                    data-testid="nav-signup"
                    role="menuitem"
                    className="ml-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-5 py-2 rounded-lg text-sm font-semibold transition-all shadow-lg shadow-emerald-500/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900"
                  >
                    Start Free
                  </Link>
                </>
              )}
            </div>
          </div>
        </div>
      </nav>
    </>
  );
};

export default Navigation;
