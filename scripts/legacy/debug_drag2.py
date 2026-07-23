with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

debug_code = '''                if self.video_frase_selecionado:
                    frases = self.frases_por_video.get(self.video_frase_selecionado, [])
                    if 0 <= self._drag_frase_idx < len(frases):
                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        with open("drag_log.txt", "a") as log:
                            log.write(f"Drag: idx={self._drag_frase_idx}, coords={coords}, offset={offset_x},{offset_y}, scale={scale_w},{scale_h}, real={real_x},{real_y}\\n")
                        self.salvar_config()
                    else:
                        with open("drag_log.txt", "a") as log:
                            log.write(f"Error: idx {self._drag_frase_idx} out of bounds for len {len(frases)}\\n")
                else:
                    with open("drag_log.txt", "a") as log:
                        log.write(f"Error: video_frase_selecionado is None\\n")'''

code = code.replace('''                if self.video_frase_selecionado:
                    frases = self.frases_por_video.get(self.video_frase_selecionado, [])
                    if 0 <= self._drag_frase_idx < len(frases):
                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        with open("drag_log.txt", "a") as log:
                            log.write(f"Drag: idx={self._drag_frase_idx}, coords={coords}, offset={offset_x},{offset_y}, scale={scale_w},{scale_h}, real={real_x},{real_y}\\n")
                        self.salvar_config()''', debug_code)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Added more debug logging')
