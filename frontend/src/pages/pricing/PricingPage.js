/**
 * Pricing Page
 * 
 * Accessibility Features:
 * - Emerald focus rings for keyboard navigation
 * - Proper ARIA labels and roles
 * - Screen reader friendly feature lists
 */
import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { Check, X } from 'lucide-react';
import { useAuth } from '../../context/AuthContext';
import { subscriptionAPI } from '../../services/api';

const PricingPage = () => {
  const { user, isAuthenticated } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);

  const handleUpgrade = async () => {
    if (!isAuthenticated) {
      navigate('/signup');
      return;
    }

    setLoading(true);
    try {
      const data = await subscriptionAPI.createCheckoutSession();
      if (data.checkout_url) {
        window.location.href = data.checkout_url;
      }
    } catch (error) {
      alert(error.response?.data?.detail || 'Failed to start checkout. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  const plans = [
    {
      name: "Free",
      price: "$0",
      period: "forever",
      description: "Perfect for trying out Auditly",
      features: [
        { text: "2 scans per month", included: true },
        { text: "axe-core scanning engine", included: true },
        { text: "Visual evidence capture", included: true },
        { text: "JSON export", included: true },
        { text: "PDF reports", included: false },
        { text: "Priority support", included: false },
      ],
      cta: isAuthenticated && user?.plan === 'free' ? "Current Plan" : "Get Started",
      ctaDisabled: isAuthenticated && user?.plan === 'free',
      highlight: false,
    },
    {
      name: "Pro",
      price: "$19",
      period: "per month",
      description: "For professionals and teams",
      features: [
        { text: "Unlimited scans", included: true },
        { text: "All scanning engines", included: true },
        { text: "Visual evidence capture", included: true },
        { text: "JSON export", included: true },
        { text: "PDF reports", included: true },
        { text: "Priority support", included: true },
      ],
      cta: isAuthenticated && user?.plan === 'pro' ? "Current Plan" : "Upgrade to Pro",
      ctaDisabled: isAuthenticated && user?.plan === 'pro',
      highlight: true,
    },
  ];

  return (
    <div className="min-h-[calc(100vh-73px)] bg-slate-950 py-16 px-4">
      <main id="main-content" className="container mx-auto max-w-5xl" role="main" aria-labelledby="pricing-heading">
        <div className="text-center mb-12">
          <h1 id="pricing-heading" className="text-4xl font-bold text-white mb-4">Simple, Transparent Pricing</h1>
          <p className="text-slate-300 text-lg max-w-2xl mx-auto">
            Choose the plan that works best for you. Start free and upgrade when you need more.
          </p>
        </div>

        <div className="grid md:grid-cols-2 gap-8 max-w-3xl mx-auto">
          {plans.map((plan) => (
            <div
              key={plan.name}
              className={`bg-slate-900 border rounded-2xl p-8 relative ${
                plan.highlight 
                  ? 'border-emerald-500/50 shadow-lg shadow-emerald-500/10' 
                  : 'border-slate-800'
              }`}
            >
              {plan.highlight && (
                <div className="absolute -top-3 left-1/2 -translate-x-1/2">
                  <span className="bg-gradient-to-r from-emerald-500 to-teal-500 text-white text-xs font-semibold px-4 py-1 rounded-full">
                    Most Popular
                  </span>
                </div>
              )}
              
              <div className="text-center mb-6">
                <h2 className="text-xl font-bold text-white mb-2">{plan.name}</h2>
                <div className="flex items-baseline justify-center space-x-1">
                  <span className="text-4xl font-bold text-white">{plan.price}</span>
                  <span className="text-slate-400">/{plan.period}</span>
                </div>
                <p className="text-slate-400 text-sm mt-2">{plan.description}</p>
              </div>

              <ul className="space-y-3 mb-8" aria-label={`${plan.name} plan features`}>
                {plan.features.map((feature, idx) => (
                  <li key={idx} className="flex items-center space-x-3">
                    {feature.included ? (
                      <Check className="w-5 h-5 text-emerald-400 flex-shrink-0" aria-hidden="true" />
                    ) : (
                      <X className="w-5 h-5 text-slate-600 flex-shrink-0" aria-hidden="true" />
                    )}
                    <span className={feature.included ? 'text-slate-200' : 'text-slate-500'}>
                      {feature.text}
                    </span>
                  </li>
                ))}
              </ul>

              <button
                onClick={() => {
                  if (plan.name === 'Pro' && !plan.ctaDisabled) {
                    handleUpgrade();
                  } else if (plan.name === 'Free' && !isAuthenticated) {
                    navigate('/signup');
                  }
                }}
                disabled={plan.ctaDisabled || (plan.name === 'Pro' && loading)}
                className={`w-full py-3 px-6 rounded-xl font-semibold transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400 ${
                  plan.highlight
                    ? 'bg-gradient-to-r from-emerald-500 to-teal-500 hover:from-emerald-600 hover:to-teal-600 text-white shadow-lg shadow-emerald-500/25 disabled:from-slate-600 disabled:to-slate-600 disabled:shadow-none'
                    : 'bg-slate-800 hover:bg-slate-700 text-white disabled:bg-slate-800 disabled:text-slate-500'
                }`}
                aria-busy={plan.name === 'Pro' && loading}
              >
                {plan.name === 'Pro' && loading ? 'Loading...' : plan.cta}
              </button>
            </div>
          ))}
        </div>
      </main>
    </div>
  );
};

export default PricingPage;
