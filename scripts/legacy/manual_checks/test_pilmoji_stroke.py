from PIL import Image, ImageFont
from pilmoji import Pilmoji

font = ImageFont.truetype('arial.ttf', 30)
with Image.new('RGBA', (400, 200), (255, 255, 255, 255)) as image:
    with Pilmoji(image) as pilmoji:
        pilmoji.text((10, 10), 'linha 1\nlinha 2 com emoji 😃\nlinha 3', fill='black', font=font, stroke_width=3, stroke_fill='red')
    image.save('test_stroke.png')
