from PIL import Image, ImageDraw, ImageFont
from pilmoji import Pilmoji

font = ImageFont.truetype('arial.ttf', 60)
with Image.new('RGBA', (500, 200), (255, 255, 255, 0)) as image:
    with Pilmoji(image) as pilmoji:
        pilmoji.text((10, 10), 'Test 😀 ✅ 💀 🤍', (0, 0, 0), font=font)
    image.save('test_emoji.png')
