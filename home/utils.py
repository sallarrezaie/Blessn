from django.core.mail import EmailMessage

from rest_framework.authtoken.models import Token

from blessn.settings import SENDGRID_EMAIL

import pyotp


def auth_token(user):
    token, created = Token.objects.get_or_create(user=user)
    return token

def verifyOTP(otp=None, user=None):
    totp = pyotp.TOTP(user.activation_key, digits=4)
    return totp.verify(otp, valid_window=16)

def send_otp(user):
    email = user.email
    if not user.activation_key:
        secret = pyotp.random_base32()
        user.activation_key = secret
    else:
        secret = user.activation_key
    totp = pyotp.TOTP(secret, digits=4)
    otp = totp.now()

    user.otp = otp
    user.save()
    email_body = """\
            <html>
            <head></head>
            <body>
            <p>
            Your access code for Blessn is %s<br><br>
            To your success,<br>
            The Blessn Team
            </p>
            </body>
            </html>
            """ % (otp)
    email_msg = EmailMessage(f"Blessn Access Code", email_body, from_email=SENDGRID_EMAIL, to=[email])
    email_msg.content_subtype = "html"
    email_msg.send()

def send_email(subject, message, to_email):
    email_msg = EmailMessage(subject, message, from_email=SENDGRID_EMAIL, to=[to_email])
    email_msg.content_subtype = "html"
    email_msg.send()
