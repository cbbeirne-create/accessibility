/**
 * WCAG Remediation Guidance Dictionary
 * 
 * Maps WCAG criteria and axe-core rule IDs to user-friendly
 * remediation guidance. Used in scan results to help developers
 * understand how to fix accessibility issues.
 */

export const WCAG_REMEDIATION = {
  // 1.1 Text Alternatives
  "1.1.1": "Add descriptive alt text to all meaningful images using the `alt` attribute. For decorative images, use an empty alt attribute (`alt=\"\"`).",
  "wcag111": "Add descriptive alt text to all meaningful images using the `alt` attribute. For decorative images, use an empty alt attribute (`alt=\"\"`).",
  
  // 1.3 Adaptable
  "1.3.1": "Use proper HTML semantic elements (headings, lists, tables) and ARIA roles to convey content structure and relationships.",
  "wcag131": "Use proper HTML semantic elements (headings, lists, tables) and ARIA roles to convey content structure and relationships.",
  
  // 1.4 Distinguishable
  "1.4.1": "Ensure information is not conveyed by color alone. Use text, icons, or patterns in addition to color.",
  "1.4.3": "Increase color contrast ratio to at least 4.5:1 for normal text and 3:1 for large text against the background.",
  "1.4.6": "Increase color contrast ratio to at least 7:1 for normal text and 4.5:1 for large text (enhanced contrast).",
  "wcag141": "Ensure information is not conveyed by color alone. Use text, icons, or patterns in addition to color.",
  "wcag143": "Increase color contrast ratio to at least 4.5:1 for normal text and 3:1 for large text against the background.",
  
  // 2.1 Keyboard Accessible
  "2.1.1": "Ensure all interactive elements are keyboard accessible using Tab, Enter, Space, and arrow keys.",
  "2.1.2": "Ensure users can exit any keyboard trap using standard navigation methods.",
  "wcag211": "Ensure all interactive elements are keyboard accessible using Tab, Enter, Space, and arrow keys.",
  "wcag212": "Ensure users can exit any keyboard trap using standard navigation methods.",
  
  // 2.4 Navigable
  "2.4.1": "Provide a 'Skip to main content' link and other skip navigation options for keyboard users.",
  "2.4.2": "Add a descriptive and unique `<title>` element to each page that describes the page topic or purpose.",
  "2.4.3": "Ensure the tab order follows a logical sequence that preserves meaning and operability.",
  "2.4.4": "Write clear, descriptive link text that makes sense out of context. Avoid generic text like 'click here' or 'read more'.",
  "2.4.6": "Use clear, descriptive headings and labels that describe the topic or purpose of content sections.",
  "2.4.7": "Ensure keyboard focus indicators are clearly visible with sufficient contrast and size.",
  "wcag241": "Provide a 'Skip to main content' link and other skip navigation options for keyboard users.",
  "wcag242": "Add a descriptive and unique `<title>` element to each page that describes the page topic or purpose.",
  "wcag243": "Ensure the tab order follows a logical sequence that preserves meaning and operability.",
  "wcag244": "Write clear, descriptive link text that makes sense out of context. Avoid generic text like 'click here' or 'read more'.",
  "wcag246": "Use clear, descriptive headings and labels that describe the topic or purpose of content sections.",
  "wcag247": "Ensure keyboard focus indicators are clearly visible with sufficient contrast and size.",
  
  // 3.1 Readable
  "3.1.1": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "3.1.2": "Use the `lang` attribute on elements where the language changes from the page default.",
  "wcag311": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "wcag312": "Use the `lang` attribute on elements where the language changes from the page default.",
  
  // 3.2 Predictable
  "3.2.1": "Ensure receiving focus does not trigger unexpected context changes like form submission or page navigation.",
  "3.2.2": "Ensure changing form controls does not automatically trigger unexpected context changes.",
  "wcag321": "Ensure receiving focus does not trigger unexpected context changes like form submission or page navigation.",
  "wcag322": "Ensure changing form controls does not automatically trigger unexpected context changes.",
  
  // 4.1 Compatible
  "4.1.1": "Fix HTML validation errors, especially duplicate IDs, improper nesting, and missing required attributes.",
  "4.1.2": "Ensure all UI components have accessible names and roles, and programmatically convey their state.",
  "4.1.3": "Ensure status messages are programmatically determinable through ARIA live regions or role attributes.",
  "wcag411": "Fix HTML validation errors, especially duplicate IDs, improper nesting, and missing required attributes.",
  "wcag412": "Ensure all UI components have accessible names and roles, and programmatically convey their state.",
  "wcag413": "Ensure status messages are programmatically determinable through ARIA live regions or role attributes.",
  
  // Common axe-core rule IDs
  "html-has-lang": "Add a `lang` attribute to the `<html>` element to specify the page language (e.g., `<html lang=\"en\">`).",
  "color-contrast": "Increase the color contrast ratio between text and background to meet WCAG standards (4.5:1 for normal text).",
  "image-alt": "Add descriptive alt text to images using the `alt` attribute. Use empty alt (`alt=\"\"`) for decorative images.",
  "link-name": "Ensure all links have accessible names through link text, aria-label, or aria-labelledby attributes.",
  "button-name": "Ensure all buttons have accessible names through button text, aria-label, or aria-labelledby attributes.",
  "form-field-multiple-labels": "Ensure form fields have exactly one properly associated label using the `for` attribute or implicit labeling.",
  "heading-order": "Use heading elements (h1-h6) in hierarchical order without skipping levels (h1 → h2 → h3).",
  "landmark-one-main": "Include exactly one `main` landmark on each page to identify the primary content area.",
  "page-has-heading-one": "Include exactly one h1 element on each page to provide a main heading for the content.",
  "region": "Ensure all content is contained within landmark regions (main, nav, aside, etc.) for screen reader navigation.",
  "skip-link": "Provide a 'Skip to main content' link as the first focusable element on the page.",
  "focus-order-semantics": "Ensure the focus order follows the logical reading order and maintains semantic meaning.",
  "aria-allowed-attr": "Remove ARIA attributes that are not allowed for the element's role, or change the element's role.",
  "aria-required-attr": "Add the required ARIA attributes for the element's role (e.g., aria-expanded for buttons).",
  "duplicate-id": "Ensure all ID attributes are unique within the page. Duplicate IDs can break form labels and ARIA references."
};

/**
 * Get remediation guidance for an accessibility issue
 * @param {Object} issue - The accessibility issue object
 * @returns {string|null} - Remediation guidance or null if not found
 */
export const getRemediationGuidance = (issue) => {
  if (!issue.wcag || !Array.isArray(issue.wcag)) {
    // Also check the issue ID itself (for axe-core rules)
    if (issue.id && WCAG_REMEDIATION[issue.id]) {
      return WCAG_REMEDIATION[issue.id];
    }
    return null;
  }
  
  // Try to find remediation guidance by checking various WCAG references
  for (const wcagRef of issue.wcag) {
    const guidance = WCAG_REMEDIATION[wcagRef];
    if (guidance) {
      return guidance;
    }
  }
  
  // Fallback: check the issue ID
  if (issue.id && WCAG_REMEDIATION[issue.id]) {
    return WCAG_REMEDIATION[issue.id];
  }
  
  return null;
};

/**
 * User Manager Utility
 * Manages anonymous user identification for unauthenticated users
 */
export const UserManager = {
  getUserId: () => {
    let userId = localStorage.getItem('accessibility_scanner_user_id');
    if (!userId) {
      userId = 'user_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('accessibility_scanner_user_id', userId);
    }
    return userId;
  },
  
  clearUser: () => {
    localStorage.removeItem('accessibility_scanner_user_id');
  }
};

/**
 * Format date for display
 * @param {string|Date} date 
 * @returns {string}
 */
export const formatDate = (date) => {
  if (!date) return 'N/A';
  const d = new Date(date);
  return d.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit'
  });
};

/**
 * Get score color class based on accessibility score
 * @param {number} score 
 * @returns {string} - Tailwind color classes
 */
export const getScoreColorClass = (score) => {
  if (score >= 80) return 'text-emerald-400';
  if (score >= 60) return 'text-amber-400';
  return 'text-red-400';
};

/**
 * Get score background class based on accessibility score
 * @param {number} score 
 * @returns {string} - Tailwind background classes
 */
export const getScoreBgClass = (score) => {
  if (score >= 80) return 'bg-emerald-500/20';
  if (score >= 60) return 'bg-amber-500/20';
  return 'bg-red-500/20';
};

/**
 * Get impact color class
 * @param {string} impact - critical, serious, moderate, minor
 * @returns {string} - Tailwind color classes
 */
export const getImpactColorClass = (impact) => {
  switch (impact?.toLowerCase()) {
    case 'critical':
      return 'text-red-400 bg-red-500/20';
    case 'serious':
      return 'text-orange-400 bg-orange-500/20';
    case 'moderate':
      return 'text-amber-400 bg-amber-500/20';
    case 'minor':
      return 'text-blue-400 bg-blue-500/20';
    default:
      return 'text-slate-400 bg-slate-500/20';
  }
};
