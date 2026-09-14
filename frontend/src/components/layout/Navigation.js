/**
 * Navigation Component
 *
 * Responsive, authentication-aware navigation with visible focus states,
 * skip navigation and a compact mobile menu.
 */
import React, { useEffect, useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Shield, Clock, Users, Menu, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import SkipLink from './SkipLink';
import { NotificationBell } from '../common';

const Navigation = () => {
  const { user, logout, isAuthenticated } = useAuth();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  useEffect(() => {
    setMobileOpen(false);
  }, [location.pathname]);

  const isActive = (path) => location.pathname === path;
  const linkBaseClasses = "px-4 py-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400";

  const authenticatedLinks = [
    { to: '/', label: 'Dashboard', testId: 'nav-dashboard' },
    { to: '/scan', label: 'New Scan', testId: 'nav-new-scan' },
    { to: '/my-scans', label: 'My Scans', testId: 'nav-my-scans' },
    { to: '/analytics', label: 'Analytics', testId: 'nav-analytics' },
    { to: '/scheduled-scans', label: 'Scheduled', testId: 'nav-scheduled', icon: Clock },
    { to: '/team', label: 'Team', testId: 'nav-team', icon: Users },
    { to: '/pricing', label: 'Pricing', testId: 'nav-pricing' },
  ];

  const renderAuthLink = ({ to, label, testId, icon: Icon }, mobile = false) => (
    <Link
      key={to}
      to={to}
      data-testid={mobile ? `${testId}-mobile` : testId}
      aria-current={isActive(to) ? 'page' : undefined}
      className={`${linkBaseClasses} ${mobile ? 'w-full flex items-center gap-2' : 'inline-flex items-center gap-1'} ${
        isActive(to)
          ? 'bg-slate-800 text-white'
          : 'text-slate-300 hover:text-white hover:bg-slate-800/50'
      }`}
    >
      {Icon && <Icon className="w-4 h-4 shrink-0" aria-hidden="true" />}
      <span>{label}</span>
    </Link>
  );

  return (
    <>
      <SkipLink />

      <nav className="bg-slate-900 border-b border-slate-800" aria-label="Main navigation">
        <div className="container mx-auto px-4 sm:px-6 py-3 sm:py-4">
          <div className="flex justify-between items-center gap-4">
            <Link
              to="/"
              className="flex items-center space-x-3 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900 rounded-lg"
              data-testid="nav-logo"
              aria-label="Auditly - Go to homepage"
            >
              <div className="w-10 h-10 bg-gradient-to-br from-emerald-400 to-teal-500 rounded-xl flex items-center justify-center" aria-hidden="true">
                <Shield className="w-6 h-6 text-white" aria-hidden="true" />
              </div>
              <div>
                <span className="text-xl font-bold text-white tracking-tight">Auditly</span>
                <span className="text-xs text-slate-400 block -mt-1">Accessibility Scanner</span>
              </div>
            </Link>

            <div className="hidden lg:flex items-center gap-1">
              {isAuthenticated ? (
                <>
                  {authenticatedLinks.map((item) => renderAuthLink(item))}
                  <div className="flex items-center ml-3 pl-3 border-l border-slate-700">
                    <NotificationBell />
                    <div className="text-right ml-3">
                      <div className="text-sm font-medium text-white max-w-32 truncate">
                        {user?.full_name || user?.email?.split('@')[0]}
                      </div>
                      <div className="flex items-center justify-end gap-2">
                        <span
                          className={`text-xs px-2 py-0.5 rounded-full ${user?.plan === 'pro' ? 'bg-emerald-500/20 text-emerald-300' : 'bg-slate-700 text-slate-300'}`}
                          aria-label={`Current plan: ${user?.plan}`}
                        >
                          {user?.plan?.toUpperCase()}
                        </span>
                        {user?.scans_remaining !== -1 && (
                          <span className="text-xs text-slate-400" aria-label={`${user?.scans_remaining} scans remaining`}>
                            {user?.scans_remaining} left
                          </span>
                        )}
                      </div>
                    </div>
                    <button
                      onClick={logout}
                      data-testid="nav-logout"
                      className="ml-3 bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white px-3 py-2 rounded-lg text-sm font-medium transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                    >
                      Log out
                    </button>
                  </div>
                </>
              ) : (
                <>
                  <Link to="/pricing" data-testid="nav-pricing-guest" className={`${linkBaseClasses} text-slate-300 hover:text-white`}>Pricing</Link>
                  <Link to="/login" data-testid="nav-login" className={`${linkBaseClasses} text-slate-300 hover:text-white`}>Log in</Link>
                  <Link to="/signup" data-testid="nav-signup" className="ml-2 bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white px-5 py-2 rounded-lg text-sm font-semibold transition-colors shadow-lg shadow-emerald-500/25 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 focus-visible:ring-offset-2 focus-visible:ring-offset-slate-900">
                    Start Free
                  </Link>
                </>
              )}
            </div>

            <div className="flex lg:hidden items-center gap-2">
              {isAuthenticated && <NotificationBell />}
              <button
                type="button"
                data-testid="nav-mobile-menu"
                onClick={() => setMobileOpen((open) => !open)}
                aria-expanded={mobileOpen}
                aria-controls="mobile-navigation"
                aria-label={mobileOpen ? 'Close navigation menu' : 'Open navigation menu'}
                className="w-11 h-11 inline-flex items-center justify-center rounded-lg bg-slate-800 text-slate-200 hover:bg-slate-700 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
              >
                {mobileOpen ? <X className="w-5 h-5" aria-hidden="true" /> : <Menu className="w-5 h-5" aria-hidden="true" />}
              </button>
            </div>
          </div>

          {mobileOpen && (
            <div id="mobile-navigation" className="lg:hidden mt-4 pt-4 border-t border-slate-800">
              {isAuthenticated ? (
                <div className="space-y-1">
                  {authenticatedLinks.map((item) => renderAuthLink(item, true))}
                  <div className="mt-4 pt-4 border-t border-slate-800 flex items-center justify-between gap-4">
                    <div className="min-w-0">
                      <p className="text-sm font-medium text-white truncate">{user?.full_name || user?.email?.split('@')[0]}</p>
                      <p className="text-xs text-slate-400 mt-1">
                        {user?.plan?.toUpperCase()}{user?.scans_remaining !== -1 ? ` · ${user?.scans_remaining} scans left` : ' · Unlimited scans'}
                      </p>
                    </div>
                    <button
                      onClick={logout}
                      data-testid="nav-logout-mobile"
                      className="min-h-11 px-4 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 hover:text-white text-sm font-medium focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400"
                    >
                      Log out
                    </button>
                  </div>
                </div>
              ) : (
                <div className="space-y-2">
                  <Link to="/pricing" className={`${linkBaseClasses} block w-full text-slate-300 hover:text-white hover:bg-slate-800/50`}>Pricing</Link>
                  <Link to="/login" className={`${linkBaseClasses} block w-full text-slate-300 hover:text-white hover:bg-slate-800/50`}>Log in</Link>
                  <Link to="/signup" className="min-h-11 flex items-center justify-center w-full bg-gradient-to-r from-emerald-500 to-teal-500 text-white px-5 py-3 rounded-lg text-sm font-semibold focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400">Start Free</Link>
                </div>
              )}
            </div>
          )}
        </div>
      </nav>
    </>
  );
};

export default Navigation;
