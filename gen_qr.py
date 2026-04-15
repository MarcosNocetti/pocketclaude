import qrcode
import pyotp
import os
from dotenv import load_dotenv

load_dotenv()
t = pyotp.TOTP(os.environ['TOTP_SECRET'])
uri = t.provisioning_uri(name='marcos', issuer_name='telegram-pc-bot')
qr = qrcode.QRCode()
qr.add_data(uri)
qr.print_ascii(invert=True)
