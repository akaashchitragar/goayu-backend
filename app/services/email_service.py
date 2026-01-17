"""
Email service for sending OTP codes using Resend
"""
import logging
import resend
from app.core.config import settings

logger = logging.getLogger(__name__)

# Configure Resend
resend.api_key = settings.RESEND_API_KEY


class EmailService:
    """Service for sending emails"""
    
    @staticmethod
    def get_otp_email_html(otp: str) -> str:
        """Generate beautiful HTML template for OTP email"""
        return f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Your Ayushya OTP Code</title>
</head>
<body style="margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; background: linear-gradient(135deg, #f0fdf4 0%, #ffffff 50%, #fef3c7 100%); min-height: 100vh;">
    <table width="100%" cellpadding="0" cellspacing="0" style="min-height: 100vh; padding: 40px 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="max-width: 600px; background: white; border-radius: 24px; box-shadow: 0 20px 60px rgba(0, 0, 0, 0.1); overflow: hidden;">
                    <!-- Header with Gradient -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #16a34a 0%, #15803d 100%); padding: 40px 40px 60px; text-align: center; position: relative;">
                            <!-- Decorative Pattern -->
                            <div style="position: absolute; top: 0; left: 0; right: 0; bottom: 0; opacity: 0.1; background-image: radial-gradient(circle, white 1px, transparent 1px); background-size: 20px 20px;"></div>
                            
                            <!-- Logo -->
                            <div style="position: relative; z-index: 1;">
                                <div style="display: inline-block; background: rgba(255, 255, 255, 0.2); backdrop-filter: blur(10px); padding: 16px; border-radius: 16px; margin-bottom: 20px;">
                                    <svg width="48" height="48" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
                                        <path d="M12 2L2 7L12 12L22 7L12 2Z" fill="white"/>
                                        <path d="M2 17L12 22L22 17" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                        <path d="M2 12L12 17L22 12" stroke="white" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>
                                    </svg>
                                </div>
                                <h1 style="margin: 0; color: white; font-size: 32px; font-weight: 700; letter-spacing: -0.5px;">Ayushya</h1>
                                <p style="margin: 8px 0 0; color: rgba(255, 255, 255, 0.9); font-size: 14px; font-weight: 500;">आयुष्य - Life & Longevity</p>
                            </div>
                        </td>
                    </tr>
                    
                    <!-- Content -->
                    <tr>
                        <td style="padding: 50px 40px;">
                            <h2 style="margin: 0 0 16px; color: #1f2937; font-size: 24px; font-weight: 700; text-align: center;">Your One-Time Password</h2>
                            <p style="margin: 0 0 32px; color: #6b7280; font-size: 16px; line-height: 1.6; text-align: center;">
                                Use this code to complete your authentication. This code will expire in <strong style="color: #16a34a;">10 minutes</strong>.
                            </p>
                            
                            <!-- OTP Box -->
                            <div style="background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%); border: 2px solid #16a34a; border-radius: 16px; padding: 32px; margin: 0 0 32px; text-align: center;">
                                <div style="font-size: 48px; font-weight: 800; letter-spacing: 12px; color: #16a34a; font-family: 'Courier New', monospace; text-shadow: 0 2px 4px rgba(22, 163, 74, 0.1);">
                                    {otp}
                                </div>
                            </div>
                            
                            <!-- Security Notice -->
                            <div style="background: #fef3c7; border-left: 4px solid #f59e0b; border-radius: 8px; padding: 16px 20px; margin: 0 0 32px;">
                                <p style="margin: 0; color: #92400e; font-size: 14px; line-height: 1.6;">
                                    <strong>🔒 Security Notice:</strong> Never share this code with anyone. Ayushya will never ask for your OTP via phone or email.
                                </p>
                            </div>
                            
                            <!-- Info Text -->
                            <p style="margin: 0; color: #9ca3af; font-size: 14px; line-height: 1.6; text-align: center;">
                                If you didn't request this code, please ignore this email or contact our support team if you have concerns.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background: #f9fafb; padding: 32px 40px; text-align: center; border-top: 1px solid #e5e7eb;">
                            <p style="margin: 0 0 12px; color: #6b7280; font-size: 14px;">
                                Experience personalized Ayurvedic consultations powered by AI
                            </p>
                            <p style="margin: 0 0 20px; color: #9ca3af; font-size: 12px;">
                                Ancient Wisdom, Modern Technology
                            </p>
                            
                            <!-- Sanskrit Quote -->
                            <div style="border-top: 1px solid #e5e7eb; padding-top: 20px; margin-top: 20px;">
                                <p style="margin: 0 0 8px; color: #16a34a; font-size: 13px; font-style: italic;">
                                    "स्वस्थस्य स्वास्थ्य रक्षणं आतुरस्य विकार प्रशमनं च"
                                </p>
                                <p style="margin: 0; color: #9ca3af; font-size: 11px;">
                                    To maintain the health of the healthy and to cure the diseases of the diseased
                                </p>
                                <p style="margin: 8px 0 0; color: #6b7280; font-size: 11px; font-weight: 600;">
                                    — Charaka Samhita
                                </p>
                            </div>
                            
                            <p style="margin: 24px 0 0; color: #9ca3af; font-size: 12px;">
                                © 2026 Ayushya. All rights reserved.
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
    
    @staticmethod
    async def send_otp_email(email: str, otp: str) -> bool:
        """
        Send OTP code to email address using Resend
        
        Args:
            email: Recipient email address
            otp: 6-digit OTP code
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # Get HTML template
            html_content = EmailService.get_otp_email_html(otp)
            
            # Send email via Resend
            params = {
                "from": "Ayushya <otp@app.goayu.life>",
                "to": [email],
                "subject": f"Your Ayushya OTP Code: {otp}",
                "html": html_content,
            }
            
            response = resend.Emails.send(params)
            
            logger.info(f"OTP email sent successfully to {email}. Email ID: {response.get('id')}")
            print(f"\n✅ OTP email sent to {email} - Code: {otp}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send OTP email to {email}: {e}")
            print(f"\n❌ Failed to send OTP email: {e}")
            print(f"📧 OTP for {email}: {otp}\n")
            return False
    
    @staticmethod
    async def send_welcome_email(email: str, first_name: str = None) -> bool:
        """
        Send welcome email to new user
        
        Args:
            email: Recipient email address
            first_name: User's first name (optional)
            
        Returns:
            bool: True if email sent successfully
        """
        try:
            # TODO: Integrate with actual email service
            greeting = f"Hello {first_name}" if first_name else "Hello"
            
            logger.info(f"Welcome email would be sent to {email}")
            print(f"\n📧 Welcome email: {greeting}, {email}\n")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to send welcome email: {e}")
            return False
