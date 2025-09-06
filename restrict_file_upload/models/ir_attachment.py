import base64
import logging
from odoo import models, api
from odoo.exceptions import ValidationError
from odoo.tools import ImageProcess

_logger = logging.getLogger(__name__)

class IrAttachment(models.Model):
    _inherit = 'ir.attachment'

    @api.model
    def create(self, vals):
        _logger.info(f"in custom ir.attachment create method")
        blocked_mime_types = [
            # **Executables & Scripts**
            "application/x-msdownload",  # EXE
            "application/x-dosexec",  # EXE
            "application/x-msdos-program",  # EXE (MS-DOS)
            "application/x-executable",  # General Executable
            "application/octet-stream",  # Generic Executable
            "application/x-msi",  # MSI Installer
            "application/java-archive",  # JAR
            "application/x-java-archive",  # JAR alternative
            "application/x-python-code",  # Python PYC/PYO
            "application/x-sh",  # SH script
            "application/x-bat",  # BAT script
            "application/x-ms-shortcut",  # Windows Shortcut (.lnk)

            # **Shell & Batch Files**
            "text/x-shellscript",  # Shell script
            "application/x-perl",  # Perl script
            "application/x-python",  # Python script
            "application/x-php",  # PHP script
            "application/x-ruby",  # Ruby script
            "application/x-csh",  # C Shell script
            "application/x-tcl",  # TCL script

            # **Archives that Can Contain Executables**
            "application/x-7z-compressed",  # 7z
            "application/x-rar",  # RAR
            "application/x-tar",  # TAR
            "application/zip",  # ZIP
            "application/x-zip-compressed",  # ZIP alternative
            "application/gzip",  # GZ
            "application/x-bzip",  # BZ2
            "application/x-bzip2",  # BZ2 alternative

            # **Other Potentially Dangerous Files**
            "application/x-ms-wim",  # Windows Imaging Format (can contain executables)
            "application/x-ms-manifest",  # Windows ClickOnce Deployment
            "application/x-silverlight",  # Silverlight apps
            "application/x-shockwave-flash",  # SWF (Flash)
            "application/vnd.android.package-archive",  # APK (Android installer)
            "application/x-iso9660-image",  # ISO (disk image)
            "application/x-diskcopy",  # DMG (macOS installer)
        ]

        mimetype = self._compute_mimetype(vals)
        _logger.info(f"custom ir.attachment create method: mimetype file detected: MIME: {mimetype}")
        if vals.get('datas'):
            _logger.info(f"Uploaded file detected: {vals.get('name')} - MIME: {mimetype}")

        # Block dangerous file types
        if mimetype in blocked_mime_types:
            raise ValidationError(f"Blocked file type detected: {mimetype}")

        # Check if the file is an image but cannot be decoded (Fake Image)
        if mimetype.startswith("image") and mimetype != "image/svg+xml":
            try:
                image_data = base64.b64decode(vals['datas'])
                img = ImageProcess(image_data, verify_resolution=True)
                if not img.image:
                    raise ValidationError("Invalid image file detected! Upload a valid image.")
            except Exception as e:
                _logger.warning(f"Blocked invalid image upload: {vals.get('name')}. Error: {e}")
                raise ValidationError("Invalid image file detected! Upload a valid image.")

        return super(IrAttachment, self).create(vals)