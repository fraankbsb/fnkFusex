from PIL import ImageDraw, ImageFont, Image
for font_name in ['arial.ttf', 'verdana.ttf', 'comic.ttf']:
    try:
        font = ImageFont.truetype(font_name, 58)
        d = ImageDraw.Draw(Image.new('RGBA', (1,1)))
        texto = 'linha 1\nlinha 2\nlinha 3'
        bbox = d.textbbox((0,0), texto, font=font)
        h_bbox = bbox[3] - bbox[1]
        
        my_h = 0
        for linha in texto.split('\n'):
            my_h += sum(font.getmetrics()) + 4
            
        print(f'{font_name}: bbox_h={h_bbox}, my_h={my_h}')
    except Exception as e:
        print(e)
