"""Safe image-upload support for the server-scoped bot profile settings."""
import base64
import io
import json
import re
import urllib.parse
from pathlib import Path

from PIL import Image, UnidentifiedImageError

import guild_profile_settings

MAX_UPLOAD_BYTES = 2 * 1024 * 1024
IMAGE_DATA_URI = re.compile(r"^data:image/(png|jpeg|webp|gif);base64,([A-Za-z0-9+/=]+)$")


def _avatar_from_upload(value):
    if not isinstance(value, str) or not value.startswith("data:"):
        return guild_profile_settings._download_avatar(value)
    match = IMAGE_DATA_URI.fullmatch(value)
    if not match:
        raise ValueError("La imagen subida debe ser PNG, JPG, WEBP o GIF.")
    try:
        image_bytes = base64.b64decode(match.group(2), validate=True)
    except (ValueError, base64.binascii.Error) as error:
        raise ValueError("El archivo de imagen no es válido.") from error
    if not image_bytes or len(image_bytes) > MAX_UPLOAD_BYTES:
        raise ValueError("La imagen procesada debe pesar como máximo 2 MB.")
    try:
        with Image.open(io.BytesIO(image_bytes)) as image:
            if image.format not in {"PNG", "JPEG", "WEBP", "GIF"}:
                raise ValueError("La imagen subida debe ser PNG, JPG, WEBP o GIF.")
            if image.width * image.height > 20_000_000:
                raise ValueError("La resolución de la imagen es demasiado grande.")
            image.verify()
    except (UnidentifiedImageError, OSError) as error:
        raise ValueError("El archivo subido no es una imagen válida.") from error
    mime = match.group(1)
    return f"data:image/{mime};base64,{base64.b64encode(image_bytes).decode('ascii')}"


def install_profile_upload_support(handler_class):
    """Allow bounded JSON image uploads and inject the account upload control."""
    guild_profile_settings._download_avatar = _avatar_from_upload

    original_read_json_body = handler_class.read_json_body

    def read_json_body(self):
        if urllib.parse.urlparse(self.path).path != "/api/settings/guild-profile":
            return original_read_json_body(self)
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except (TypeError, ValueError):
            raise ValueError("Tamaño de solicitud no válido.")
        if not 0 < length <= 3 * 1024 * 1024:
            raise ValueError("La imagen es demasiado grande; el límite de subida es 2 MB.")
        data = json.loads(self.rfile.read(length))
        if not isinstance(data, dict):
            raise ValueError("Solicitud no válida.")
        return data

    handler_class.read_json_body = read_json_body
    original_do_get = handler_class.do_GET
    index_path = Path(__file__).resolve().parent / "website" / "index.html"

    def do_get(self):
        if urllib.parse.urlparse(self.path).path not in ("/", "/index.html"):
            return original_do_get(self)
        try:
            html = index_path.read_text(encoding="utf-8")
        except OSError:
            return original_do_get(self)
        script = '<script src="/assets/profile-upload.js" defer></script>'
        if script not in html:
            html = html.replace("</body>", f"  {script}\n</body>")
        body = html.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    handler_class.do_GET = do_get


__all__ = ["install_profile_upload_support"]
