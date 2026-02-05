import re
from io import BytesIO

import pyotp
from PIL import Image
from pyzbar.pyzbar import decode


def get_otp(secret: str) -> str:
    """
    Get the OTP for the given secret.
    Args:
        secret: The secret.
    Returns:
        str: The OTP.
    """
    totp = pyotp.TOTP(secret)
    return totp.now()


def extract_secret_from_qrcode_image(qr_code: str | bytes) -> str:
    """
    Extract the secret from the QR code image.
    Args:
        qr_code: The QR code image. Can be a path to the image or a bytes object.
    Returns:
        str: The secret.
    """
    if isinstance(qr_code, bytes):
        qr_code_io = BytesIO(qr_code)
        try:
            img = Image.open(qr_code_io)
        except Exception as e:
            raise ValueError(f"Failed to open QR code image from bytes: {str(e)}")
    else:
        try:
            img = Image.open(qr_code)
        except Exception as e:
            raise ValueError(f"Failed to open QR code image from path: {str(e)}")

    decoded = decode(img)
    if not decoded:
        raise ValueError("No QR code found")
    qrcode_data = decoded[0].data.decode("utf-8")
    match = re.search(r"secret=([A-Za-z0-9]+)", qrcode_data)
    if not match:
        raise ValueError("No secret found in QR code data")
    return match.group(1)


if __name__ == "__main__":
    # example usage

    # by path
    secret = extract_secret_from_qrcode_image("local_tmp_file/asana_qr_code.png")
    print(secret)
    print(get_otp(secret))

    # by bytes
    with open("local_tmp_file/asana_qr_code.png", "rb") as f:
        data = f.read()
        secret = extract_secret_from_qrcode_image(data)
    print(secret)
    print(get_otp(secret))
