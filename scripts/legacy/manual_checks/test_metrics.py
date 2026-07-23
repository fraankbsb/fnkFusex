from PIL import Image, ImageFont
from pilmoji import Pilmoji

font = ImageFont.truetype('arial.ttf', 30)
with Image.new('RGBA', (400, 200), (255, 255, 255, 255)) as image:
    with Pilmoji(image) as pilmoji:
        pilmoji.text((10, 10), 'linha 1\nlinha 2\nlinha 3', fill='black', font=font, stroke_width=0)
    image.save('test_metrics1.png')

with Image.new('RGBA', (400, 200), (255, 255, 255, 255)) as image:
    with Pilmoji(image) as pilmoji:
        y_offset = 10
        for linha in ['linha 1', 'linha 2', 'linha 3']:
            pilmoji.text((10, y_offset), linha, fill='black', font=font, stroke_width=0)
            y_offset += sum(font.getmetrics()) + 4
    image.save('test_metrics2.png')

import hashlib
print(hashlib.md5(open('test_metrics1.png', 'rb').read()).hexdigest())
print(hashlib.md5(open('test_metrics2.png', 'rb').read()).hexdigest())
