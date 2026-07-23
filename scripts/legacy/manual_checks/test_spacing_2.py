from PIL import ImageDraw, ImageFont, Image
for font_name in ['arial.ttf', 'verdana.ttf', 'comic.ttf']:
    try:
        font = ImageFont.truetype(font_name, 58)
        d = ImageDraw.Draw(Image.new('RGBA', (1,1)))
        texto = 'linha 1\nlinha 2\nlinha 3'
        bbox = d.textbbox((0,0), texto, font=font)
        
        my_h = d.textbbox((0,0), texto.split('\n')[0], font=font)[3] - d.textbbox((0,0), texto.split('\n')[0], font=font)[1]
        line_spacing = d.textbbox((0,0), 'A', font=font)[3] - d.textbbox((0,0), 'A', font=font)[1] + 4
        my_h += line_spacing * 2
            
        print(f'{font_name}: bbox_h={bbox[3] - bbox[1]}, my_h_with_A_spacing={my_h}')
    except Exception as e:
        print(e)
