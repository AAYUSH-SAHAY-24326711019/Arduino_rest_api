import qrcode
import base64
from io import BytesIO
import json

def generate_qr(student):

    payload = {
        "roll": student.sroll
    }

    qr = qrcode.make(
        json.dumps(payload)
    )

    buffer = BytesIO()

    qr.save(buffer, format="PNG")

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode()

    return encoded