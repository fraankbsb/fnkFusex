with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

debug_code = '''                if self.video_frase_selecionado:
                    frases = self.frases_por_video.get(self.video_frase_selecionado, [])
                    if 0 <= self._drag_frase_idx < len(frases):
                        import tkinter.messagebox as mb
                        mb.showinfo("Debug Drag", f"idx={self._drag_frase_idx} coords={coords} offset={offset_x},{offset_y} scale={scale_w} real={real_x},{real_y} old_x={frases[self._drag_frase_idx].get('x')}")
                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        self.salvar_config()'''

import re
code = re.sub(r' *if self\.video_frase_selecionado:[\s\S]*?self\.salvar_config\(\)', debug_code, code)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched with messagebox")
