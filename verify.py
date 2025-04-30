# verify.py
from twilio.rest import Client

# Your Twilio credentials
account_sid = ''      # Your real Twilio Account SID
auth_token = ''          # Your real Twilio Auth Token
verify_sid = ''        # Your Verify Service SID

client = Client(account_sid, auth_token)

def send_otp_with_verify(phone_number):
    try:
        verification = client.verify.v2.services(verify_sid).verifications.create(
            to=phone_number,
            channel='sms'
        )
        return f"OTP sent! Status: {verification.status}"
    except Exception as e:
        return f"Failed to send OTP: {str(e)}"

def check_otp(phone_number, otp_code):
    try:
        verification_check = client.verify.v2.services(verify_sid).verification_checks.create(
            to=phone_number,
            code=otp_code
        )
        return verification_check.status == 'approved'
    except Exception as e:
        print(f"OTP check failed: {e}")
        return False
