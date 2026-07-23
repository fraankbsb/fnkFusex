import re

with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

resolver_func = '''
    def _resolver_fonte(self, nome_fonte, negrito=False, italico=False):
        nome = nome_fonte.lower()
        mapa = {
            "arial": {"reg": "arial.ttf", "b": "arialbd.ttf", "i": "ariali.ttf", "bi": "arialbi.ttf"},
            "times new roman": {"reg": "times.ttf", "b": "timesbd.ttf", "i": "timesi.ttf", "bi": "timesbi.ttf"},
            "comic sans ms": {"reg": "comic.ttf", "b": "comicbd.ttf", "i": "comici.ttf", "bi": "comicz.ttf"},
            "courier new": {"reg": "cour.ttf", "b": "courbd.ttf", "i": "couri.ttf", "bi": "courbi.ttf"},
            "georgia": {"reg": "georgia.ttf", "b": "georgiab.ttf", "i": "georgiai.ttf", "bi": "georgiaz.ttf"},
            "verdana": {"reg": "verdana.ttf", "b": "verdanab.ttf", "i": "verdanai.ttf", "bi": "verdanaz.ttf"},
            "tahoma": {"reg": "tahoma.ttf", "b": "tahomabd.ttf", "i": "tahoma.ttf", "bi": "tahomabd.ttf"},
            "impact": {"reg": "impact.ttf", "b": "impact.ttf", "i": "impact.ttf", "bi": "impact.ttf"}
        }
        if nome in mapa:
            if negrito and italico: return mapa[nome]["bi"]
            elif negrito: return mapa[nome]["b"]
            elif italico: return mapa[nome]["i"]
            return mapa[nome]["reg"]
        return nome_fonte + ".ttf"

'''

# Inject before _gerar_imagem_frase
code = code.replace('    def _gerar_imagem_frase(self, frase, output_path, out_w, out_h):', resolver_func + '    def _gerar_imagem_frase(self, frase, output_path, out_w, out_h):')

draw_canvas_old = '''            try:
                font = ImageFont.truetype(frase["fonte"], sz_scaled)
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", sz_scaled)
                except:
                    font = ImageFont.load_default()
            
            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
            d = ImageDraw.Draw(dummy_img)
            bbox = d.textbbox((0, 0), frase["texto"], font=font)
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            
            pad = 10
            img = Image.new("RGBA", (max(1, w) + pad*2, max(1, h) + pad*2), (0, 0, 0, 0))
            with Pilmoji(img) as pilmoji:
                pilmoji.text((pad - bbox[0], pad - bbox[1]), frase["texto"], fill=frase["cor"], font=font, stroke_width=max(1, int(2*scale_w)), stroke_fill="black")'''

draw_canvas_new = '''            fonte_arquivo = self._resolver_fonte(frase.get("fonte", "Arial"), frase.get("negrito", False), frase.get("italico", False))
            try:
                font = ImageFont.truetype(fonte_arquivo, sz_scaled)
            except Exception:
                try:
                    font = ImageFont.truetype("arial.ttf", sz_scaled)
                except:
                    font = ImageFont.load_default()
            
            dummy_img = Image.new("RGBA", (1, 1), (0,0,0,0))
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
code = code.replace(draw_canvas_old, draw_canvas_new)

draw_image_old = '''        img = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
        try:
            font = ImageFont.truetype(frase["fonte"], int(frase["tamanho"]))
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", int(frase["tamanho"]))
            except:
                font = ImageFont.load_default()
        x, y = frase["x"], frase["y"]
        with Pilmoji(img) as pilmoji:
            pilmoji.text((x, y), frase["texto"], fill=frase["cor"], font=font,
                         stroke_width=5, stroke_fill="black")'''

draw_image_new = '''        img = Image.new("RGBA", (out_w, out_h), (0, 0, 0, 0))
        fonte_arquivo = self._resolver_fonte(frase.get("fonte", "Arial"), frase.get("negrito", False), frase.get("italico", False))
        try:
            font = ImageFont.truetype(fonte_arquivo, int(frase["tamanho"]))
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", int(frase["tamanho"]))
            except:
                font = ImageFont.load_default()
        x, y = frase["x"], frase["y"]
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
code = code.replace(draw_image_old, draw_image_new)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Done!")
