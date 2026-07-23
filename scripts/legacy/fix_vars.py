import re

with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Inside _abrir_janela_edicao, save the vars to self
code = code.replace(
    '''        entry_x = ctk.CTkEntry(f_xy, width=80, textvariable=entry_x_var)''',
    '''        self._current_entry_x_var = entry_x_var\n        self._current_entry_y_var = entry_y_var\n        entry_x = ctk.CTkEntry(f_xy, width=80, textvariable=entry_x_var)'''
)

# 2. Inside _abrir_janela_edicao, when dialog closes, remove them
code = code.replace(
    '''        dialog.grab_set()''',
    '''        def on_close():\n            self._current_entry_x_var = None\n            self._current_entry_y_var = None\n            dialog.destroy()\n        dialog.protocol("WM_DELETE_WINDOW", on_close)\n        dialog.grab_set()'''
)

# 3. Inside on_frase_release, update the vars if they exist
release_hook = '''                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        if getattr(self, '_current_entry_x_var', None):
                            self._current_entry_x_var.set(str(real_x))
                        if getattr(self, '_current_entry_y_var', None):
                            self._current_entry_y_var.set(str(real_y))
                        self.salvar_config()'''

code = code.replace(
    '''                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        self.salvar_config()''',
    release_hook
)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched vars")
