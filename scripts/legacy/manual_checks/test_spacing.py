from PIL import ImageDraw, ImageFont, Image
for font_name in ['arial.ttf', 'verdana.ttf', 'comic.ttf']:
    try:
        font = ImageFont.truetype(font_name, 58)
        d = ImageDraw.Draw(Image.new('RGBA', (1,1)))
        
        spacing_A = (d.textbbox((0,0), 'A', font=font)[3] - d.textbbox((0,0), 'A', font=font)[1]) + 4
        print(f'{font_name}: spacing_A={spacing_A}')
    except Exception as e:
        print(e)
