/**
 * Pages Index
 * 
 * Centralized exports for all page components
 */

// Auth Pages
export { 
  LoginPage, 
  SignupPage, 
  ForgotPasswordPage, 
  ResetPasswordPage, 
  VerifyEmailPage 
} from './auth';

// Dashboard
export { Dashboard } from './dashboard';

// Pricing
export { PricingPage } from './pricing';

// Scanner
export { 
  ScanPage, 
  MyScansPage, 
  ScanResultsPage, 
  ScanAnalyticsPage,
  ScheduledScansPage
} from './scanner';

// Team
export { TeamPage } from './team';
