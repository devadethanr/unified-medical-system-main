import re
import uuid
import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from PIL import Image

def generate_patient_id():
    return 'UMSP' + re.sub('-', '', str(uuid.uuid4()))[:8].upper()

def generate_barcode(ums_id):
    code128 = barcode.get_barcode_class('code128')
    
    class TransparentPNGWriter(ImageWriter):
        def _init(self, code):
            super()._init(code)
            self.format = 'PNG'
            self.dpi = 300
            self.module_width = 0.6  # Adjust this value to change the barcode width
            self.module_height = 3.75  # Reduced to 25% of original height (15.0 * 0.25)

        def render(self, code):
            image = super().render(code)
            image = image.convert('RGBA')
            data = image.getdata()
            new_data = []
            for item in data:
                if item[:3] == (255, 255, 255):  # If the pixel is white
                    new_data.append((255, 255, 255, 0))  # Make it transparent
                else:
                    new_data.append(item)
            image.putdata(new_data)
            return image

    rv = BytesIO()
    code128(ums_id, writer=TransparentPNGWriter()).write(rv)
    
    return base64.b64encode(rv.getvalue()).decode('utf-8')
