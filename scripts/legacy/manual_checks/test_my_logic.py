from PIL import ImageDraw, ImageFont, Image
for font_name in ['arial.ttf', 'verdana.ttf', 'comic.ttf']:
    try:
        font = ImageFont.truetype(font_name, 58)
        texto = 'testese as palavras nesse\nas palavras lesse video teste\ntestando um dois tres'
        linhas = texto.split('\n')
        d = ImageDraw.Draw(Image.new('RGBA', (1, 1), (0,0,0,0)))
        
        try:
            line_spacing = sum(font.getmetrics()) + 4
        except:
            line_spacing = 58 + 4

        w = 0
        min_x = 0
        min_y = 0
        for linha in linhas:
            bbox_linha = d.textbbox((0, 0), linha, font=font)
            lw = bbox_linha[2] - bbox_linha[0]
            if lw > w: w = lw
            if bbox_linha[0] < min_x: min_x = bbox_linha[0]
            if bbox_linha[1] < min_y: min_y = bbox_linha[1]
            
        h = len(linhas) * line_spacing
        
        print(f'{font_name}: w={w}, h={h}, min_x={min_x}, min_y={min_y}')
    except Exception as e:
        print(e)
