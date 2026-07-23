import re

with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

draw_canvas_old = '''            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
            d = ImageDraw.Draw(dummy_img)
            bbox = d.textbbox((0, 0), frase["texto"], font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            
            pad = 10
            img = Image.new("RGBA", (max(1, w) + pad*2, max(1, h) + pad*2), (0, 0, 0, 0))
            with Pilmoji(img) as pilmoji:
                y_offset = pad - bbox[1]
                stroke_w = max(1, int(2*scale_w)) if not frase.get("negrito") else max(2, int(4*scale_w))
                for linha in frase["texto"].split('\\n'):
                    pilmoji.text((pad - bbox[0], y_offset), linha, fill=frase["cor"], font=font, stroke_width=stroke_w, stroke_fill="black")
                    try:
                        y_offset += sum(font.getmetrics()) + 4
                    except:
                        y_offset += sz_scaled + 4'''

draw_canvas_new = '''            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
            d = ImageDraw.Draw(dummy_img)
            linhas = frase["texto"].split('\\n')
            
            try:
                line_spacing = sum(font.getmetrics()) + 4
            except:
                line_spacing = sz_scaled + 4
                
            w = 0
            min_x, min_y = 0, 0
            for i, linha in enumerate(linhas):
                bbox_linha = d.textbbox((0, 0), linha, font=font)
                lw = bbox_linha[2] - bbox_linha[0]
                if lw > w: w = lw
                if i == 0:
                    min_x = bbox_linha[0]
                    min_y = bbox_linha[1]
                else:
                    if bbox_linha[0] < min_x: min_x = bbox_linha[0]
                    if bbox_linha[1] < min_y: min_y = bbox_linha[1]
            
            h = len(linhas) * line_spacing
            
            pad = 10
            img = Image.new("RGBA", (max(1, w) + pad*2, max(1, h) + pad*2), (0, 0, 0, 0))
            with Pilmoji(img) as pilmoji:
                y_offset = pad - min_y
                stroke_w = max(1, int(2*scale_w)) if not frase.get("negrito") else max(2, int(4*scale_w))
                for linha in linhas:
                    pilmoji.text((pad - min_x, y_offset), linha, fill=frase["cor"], font=font, stroke_width=stroke_w, stroke_fill="black")
                    y_offset += line_spacing
            bbox = [min_x, min_y, min_x + w, min_y + h]'''
code = code.replace(draw_canvas_old, draw_canvas_new)

draw_image_old = '''        x, y = frase["x"], frase["y"]
        with Pilmoji(img) as pilmoji:
            y_offset = y
            stroke_w = 2 if not frase.get("negrito") else 5
            for linha in frase["texto"].split('\\n'):
                pilmoji.text((x, y_offset), linha, fill=frase["cor"], font=font,
                             stroke_width=stroke_w, stroke_fill="black")
                try:
                    y_offset += sum(font.getmetrics()) + 4
                except:
                    y_offset += int(frase["tamanho"]) + 4'''

draw_image_new = '''        x, y = frase["x"], frase["y"]
        
        try:
            line_spacing = sum(font.getmetrics()) + 4
        except:
            line_spacing = int(frase["tamanho"]) + 4
            
        with Pilmoji(img) as pilmoji:
            y_offset = y
            stroke_w = 2 if not frase.get("negrito") else 5
            for linha in frase["texto"].split('\\n'):
                pilmoji.text((x, y_offset), linha, fill=frase["cor"], font=font,
                             stroke_width=stroke_w, stroke_fill="black")
                y_offset += line_spacing'''
code = code.replace(draw_image_old, draw_image_new)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
