with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

debug_code = '''                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        with open("drag_log.txt", "a") as log:
                            log.write(f"Drag: idx={self._drag_frase_idx}, coords={coords}, offset={offset_x},{offset_y}, scale={scale_w},{scale_h}, real={real_x},{real_y}\\n")
                        self.salvar_config()'''

code = code.replace('''                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        self.salvar_config()''', debug_code)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Added debug logging')
