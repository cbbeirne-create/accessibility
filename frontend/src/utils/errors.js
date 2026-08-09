/**
 * Error normalization utility
 * Maps backend error responses to user-friendly messages and logs raw details.
 */

export function friendlyError(err, fallback = 'An unexpected error occurred. Please try again.') {
  try {
    // Log raw server error for debugging / telemetry
    // Do not expose full details to end users
    // Consumers can still log the raw error to a telemetry system if configured
    // eslint-disable-next-line no-console
    console.error('Server error:', err);

    if (!err) return fallback;

    // Axios-style error with response
    const resp = err.response;
    if (resp) {
      const status = resp.status;
      const data = resp.data || {};

      // Common HTTP status-based messages
      if (status === 400) return data.detail || data.message || 'Invalid request. Please check your input.';
      if (status === 401) return 'Your session has expired. Please sign in again.';
      if (status === 403) return 'You do not have permission to perform this action.';
      if (status === 404) return 'Requested resource not found.';
      if (status >= 500) return 'Server error. Please try again later.';

      // Application-specific codes/messages
      if (data && data.code) {
        switch (data.code) {
          case 'ORG_NOT_FOUND':
            return 'Team not found.';
          case 'INVITE_EXPIRED':
            return 'This invitation has expired.';
          case 'INVITE_INVALID':
            return 'Invalid invitation.';
          default:
            break;
        }
      }

      // Fallback to message/detail fields when present
      if (data.detail) return data.detail;
      if (data.message) return data.message;
    }

    // Fallback to error.message
    if (err.message) return err.message;
  } catch (e) {
    // ignore and use fallback
    // eslint-disable-next-line no-console
    console.error('Error while normalizing error:', e);
  }

  return fallback;
}
