with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '''        dialog.destroy()\n        self.desenhar_frases_no_canvas()''',
    '''        self._current_entry_x_var = None\n        self._current_entry_y_var = None\n        dialog.destroy()\n        self.desenhar_frases_no_canvas()'''
)

code = code.replace(
    '''        ctk.CTkButton(f_btns_dialog, text="❌ Cancelar",\n                      fg_color="#e74c3c", hover_color="#c0392b",\n                      height=42, font=ctk.CTkFont(weight="bold"),\n                      command=dialog.destroy)''',
    '''        def on_cancel():\n            self._current_entry_x_var = None\n            self._current_entry_y_var = None\n            dialog.destroy()\n        ctk.CTkButton(f_btns_dialog, text="❌ Cancelar",\n                      fg_color="#e74c3c", hover_color="#c0392b",\n                      height=42, font=ctk.CTkFont(weight="bold"),\n                      command=on_cancel)'''
)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched destroy")
