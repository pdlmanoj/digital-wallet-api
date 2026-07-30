def generate_email_template(otp: str, otp_exipry: int) -> str:
    return f"""
        <!doctype html>
        <html lang="en">
            <head>
                <meta charset="utf-8" />
                <title>Email OTP Verification (Digtal Wallet API)</title>
            </head>
            <body>
                <p>Dear Customer,</p>
                <p>To complete your <strong>email validation</strong> for Digital Wallet, please enter the One-Time Password (OTP) below:</p>
                <p><strong>Your OTP : {otp}</strong></p>
                <p>This OTP is valid for <strong>{otp_exipry} minutes </strong>and can only be used once.</p>
                <p style="margin: 30px 0 0 0;">
                    Warm Regards,<br />
                    <strong>Digtal Wallet API</strong>
                </p>
            </body>
        </html>
    """