/**
 * Auditly - Website Accessibility Scanner
 * 
 * Main Application Component
 * 
 * This is a refactored version using modular architecture:
 * - /services/api.js - Centralized API client with JWT interceptor
 * - /context/AuthContext.js - Authentication state management
 * - /components/layout - Navigation, SkipLink
 * - /components/common - EmailVerificationBanner
 * - /pages - All page components
 * - /utils/wcag.js - WCAG remediation guidance
 * 
 * Accessibility: WCAG 2.1 AA Compliant
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Semantic HTML structure
 */
import React from "react";
import "./App.css";
import { BrowserRouter, Routes, Route } from "react-router-dom";

// Context & Layout
import { AuthProvider, ProtectedRoute } from "./context/AuthContext";
import { Navigation } from "./components/layout";
import { EmailVerificationBanner } from "./components/common";

// Page Components
import {
  LoginPage,
  SignupPage,
  ForgotPasswordPage,
  ResetPasswordPage,
  VerifyEmailPage,
  Dashboard,
  PricingPage,
  ScanPage,
  MyScansPage,
  ScanResultsPage,
  ScanAnalyticsPage,
  ScheduledScansPage,
} from "./pages";

// ============================================
// Main App Component
// ============================================

function App() {
  return (
    <AuthProvider>
      <div className="min-h-screen bg-slate-950">
        <BrowserRouter>
          <Navigation />
          <EmailVerificationBanner />
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Dashboard />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/signup" element={<SignupPage />} />
            <Route path="/pricing" element={<PricingPage />} />
            <Route path="/forgot-password" element={<ForgotPasswordPage />} />
            <Route path="/reset-password" element={<ResetPasswordPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            
            {/* Protected Routes */}
            <Route path="/scan" element={
              <ProtectedRoute>
                <ScanPage />
              </ProtectedRoute>
            } />
            <Route path="/my-scans" element={
              <ProtectedRoute>
                <MyScansPage />
              </ProtectedRoute>
            } />
            <Route path="/analytics" element={
              <ProtectedRoute>
                <ScanAnalyticsPage />
              </ProtectedRoute>
            } />
            <Route path="/scan-results/:id" element={
              <ProtectedRoute>
                <ScanResultsPage />
              </ProtectedRoute>
            } />
            <Route path="/scheduled-scans" element={
              <ProtectedRoute>
                <ScheduledScansPage />
              </ProtectedRoute>
            } />
          </Routes>
        </BrowserRouter>
      </div>
    </AuthProvider>
  );
}

export default App;
