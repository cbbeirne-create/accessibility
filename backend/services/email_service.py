"""
Email service for password reset and notifications.
Uses SendGrid for production email delivery.
"""
import logging
import secrets
from typing import Optional

from ..core.config import settings


def generate_password_reset_token() -> str:
    """Generate a cryptographically secure password reset token."""
    return secrets.token_urlsafe(32)


def generate_verification_token() -> str:
    """Generate a cryptographically secure email verification token."""
    return secrets.token_urlsafe(32)


def send_password_reset_email(email: str, reset_token: str, user_name: Optional[str] = None) -> bool:
    """
    Send password reset email via SendGrid.
    Returns True if email was sent successfully, False otherwise.
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    
    sendgrid_api_key = settings.SENDGRID_API_KEY
    sender_email = settings.SENDER_EMAIL
    frontend_url = settings.FRONTEND_URL
    
    # Check if SendGrid is configured
    if not sendgrid_api_key or sendgrid_api_key.startswith('your_'):
        logging.warning("SendGrid not configured - password reset email not sent")
        # In development, log the reset link for testing
        reset_link = f"{frontend_url}/reset-password?token={reset_token}"
        logging.info(f"[DEV] Password reset link for {email}: {reset_link}")
        return True  # Return True so the flow continues in development
    
    reset_link = f"{frontend_url}/reset-password?token={reset_token}"
    display_name = user_name or email.split('@')[0]
    
    # Branded HTML email template matching Auditly's Enterprise theme
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Reset Your Auditly Password</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, rgba(52, 211, 153, 0.1), rgba(20, 184, 166, 0.1));">
                                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #34d399, #14b8a6); border-radius: 16px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: white; font-size: 28px; font-weight: bold;">A</span>
                                </div>
                                <h1 style="color: #ffffff; font-size: 24px; margin: 0 0 8px; font-weight: 700;">Auditly</h1>
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">Website Accessibility Scanner</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <h2 style="color: #ffffff; font-size: 20px; margin: 0 0 16px; font-weight: 600;">Reset Your Password</h2>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    Hi {display_name},
                                </p>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    We received a request to reset your Auditly account password. Click the button below to create a new password:
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" style="width: 100%; margin: 32px 0;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{reset_link}" 
                                               style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #34d399, #14b8a6); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 12px; box-shadow: 0 4px 14px rgba(52, 211, 153, 0.25);">
                                                Reset Password
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    This link will expire in <strong style="color: #f59e0b;">1 hour</strong> for security reasons.
                                </p>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    If you didn't request this password reset, you can safely ignore this email. Your password won't be changed.
                                </p>
                                
                                <!-- Fallback Link -->
                                <div style="background-color: #0f172a; border-radius: 8px; padding: 16px; margin-top: 24px;">
                                    <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                        If the button doesn't work, copy and paste this link:
                                    </p>
                                    <p style="color: #34d399; font-size: 12px; margin: 0; word-break: break-all;">
                                        {reset_link}
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 40px; border-top: 1px solid #334155; text-align: center;">
                                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                    This email was sent by Auditly
                                </p>
                                <p style="color: #64748b; font-size: 12px; margin: 0;">
                                    WCAG 2.1 AA Compliant Accessibility Scanning
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain text fallback for accessibility
    plain_text = f"""
    Reset Your Auditly Password
    
    Hi {display_name},
    
    We received a request to reset your Auditly account password. 
    
    Click this link to reset your password:
    {reset_link}
    
    This link will expire in 1 hour for security reasons.
    
    If you didn't request this password reset, you can safely ignore this email.
    
    - The Auditly Team
    """
    
    try:
        message = Mail(
            from_email=Email(sender_email, "Auditly"),
            to_emails=To(email),
            subject="Reset Your Auditly Password",
            plain_text_content=Content("text/plain", plain_text),
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logging.info(f"Password reset email sent to {email}")
            return True
        else:
            logging.error(f"SendGrid returned status {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to send password reset email: {e}")
        return False


def send_verification_email(email: str, verification_token: str, user_name: Optional[str] = None) -> bool:
    """
    Send email verification email via SendGrid.
    Returns True if email was sent successfully, False otherwise.
    """
    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail, Email, To, Content
    
    sendgrid_api_key = settings.SENDGRID_API_KEY
    sender_email = settings.SENDER_EMAIL
    frontend_url = settings.FRONTEND_URL
    
    # Check if SendGrid is configured
    if not sendgrid_api_key or sendgrid_api_key.startswith('your_'):
        logging.warning("SendGrid not configured - verification email not sent")
        # In development, log the verification link for testing
        verify_link = f"{frontend_url}/verify-email?token={verification_token}"
        logging.info(f"[DEV] Email verification link for {email}: {verify_link}")
        return True  # Return True so the flow continues in development
    
    verify_link = f"{frontend_url}/verify-email?token={verification_token}"
    display_name = user_name or email.split('@')[0]
    
    # Branded HTML email template matching Auditly's Enterprise theme
    html_content = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Verify Your Auditly Email</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #0f172a; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;">
        <table role="presentation" style="width: 100%; border-collapse: collapse;">
            <tr>
                <td style="padding: 40px 20px;">
                    <table role="presentation" style="max-width: 600px; margin: 0 auto; background-color: #1e293b; border-radius: 16px; overflow: hidden;">
                        <!-- Header -->
                        <tr>
                            <td style="padding: 40px 40px 20px; text-align: center; background: linear-gradient(135deg, rgba(52, 211, 153, 0.1), rgba(20, 184, 166, 0.1));">
                                <div style="width: 60px; height: 60px; background: linear-gradient(135deg, #34d399, #14b8a6); border-radius: 16px; margin: 0 auto 20px; display: flex; align-items: center; justify-content: center;">
                                    <span style="color: white; font-size: 28px; font-weight: bold;">A</span>
                                </div>
                                <h1 style="color: #ffffff; font-size: 24px; margin: 0 0 8px; font-weight: 700;">Auditly</h1>
                                <p style="color: #94a3b8; font-size: 14px; margin: 0;">Website Accessibility Scanner</p>
                            </td>
                        </tr>
                        
                        <!-- Content -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <h2 style="color: #ffffff; font-size: 20px; margin: 0 0 16px; font-weight: 600;">Welcome to Auditly!</h2>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    Hi {display_name},
                                </p>
                                <p style="color: #cbd5e1; font-size: 15px; line-height: 1.6; margin: 0 0 24px;">
                                    Thank you for signing up! Please verify your email address to unlock all features of your Auditly account.
                                </p>
                                
                                <!-- CTA Button -->
                                <table role="presentation" style="width: 100%; margin: 32px 0;">
                                    <tr>
                                        <td style="text-align: center;">
                                            <a href="{verify_link}" 
                                               style="display: inline-block; padding: 16px 32px; background: linear-gradient(135deg, #34d399, #14b8a6); color: #ffffff; text-decoration: none; font-weight: 600; font-size: 16px; border-radius: 12px; box-shadow: 0 4px 14px rgba(52, 211, 153, 0.25);">
                                                Verify Email Address
                                            </a>
                                        </td>
                                    </tr>
                                </table>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    This link will expire in <strong style="color: #f59e0b;">24 hours</strong> for security reasons.
                                </p>
                                
                                <p style="color: #94a3b8; font-size: 13px; line-height: 1.6; margin: 0 0 16px;">
                                    If you didn't create an account with Auditly, you can safely ignore this email.
                                </p>
                                
                                <!-- Fallback Link -->
                                <div style="background-color: #0f172a; border-radius: 8px; padding: 16px; margin-top: 24px;">
                                    <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                        If the button doesn't work, copy and paste this link:
                                    </p>
                                    <p style="color: #34d399; font-size: 12px; margin: 0; word-break: break-all;">
                                        {verify_link}
                                    </p>
                                </div>
                            </td>
                        </tr>
                        
                        <!-- Footer -->
                        <tr>
                            <td style="padding: 24px 40px; border-top: 1px solid #334155; text-align: center;">
                                <p style="color: #64748b; font-size: 12px; margin: 0 0 8px;">
                                    This email was sent by Auditly
                                </p>
                                <p style="color: #64748b; font-size: 12px; margin: 0;">
                                    WCAG 2.1 AA Compliant Accessibility Scanning
                                </p>
                            </td>
                        </tr>
                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Plain text fallback for accessibility
    plain_text = f"""
    Welcome to Auditly!
    
    Hi {display_name},
    
    Thank you for signing up! Please verify your email address by clicking this link:
    {verify_link}
    
    This link will expire in 24 hours for security reasons.
    
    If you didn't create an account with Auditly, you can safely ignore this email.
    
    - The Auditly Team
    """
    
    try:
        message = Mail(
            from_email=Email(sender_email, "Auditly"),
            to_emails=To(email),
            subject="Verify Your Auditly Email Address",
            plain_text_content=Content("text/plain", plain_text),
            html_content=Content("text/html", html_content)
        )
        
        sg = SendGridAPIClient(sendgrid_api_key)
        response = sg.send(message)
        
        if response.status_code == 202:
            logging.info(f"Verification email sent to {email}")
            return True
        else:
            logging.error(f"SendGrid returned status {response.status_code}")
            return False
            
    except Exception as e:
        logging.error(f"Failed to send verification email: {e}")
        return False

            
    except Exception as e:
        logging.error(f"Failed to send password reset email: {e}")
        return False
