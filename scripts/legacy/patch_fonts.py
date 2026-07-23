with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

# Add Montserrat to fonts list
code = code.replace(
    'cb_fonte_wm = ctk.CTkComboBox(tab_marca, values=["Arial", "Impact", "Verdana", "Tahoma", "Courier New", "Comic Sans MS"])',
    'cb_fonte_wm = ctk.CTkComboBox(tab_marca, values=["Arial", "Montserrat", "Impact", "Verdana", "Tahoma", "Courier New", "Comic Sans MS"])'
)

code = code.replace(
    'fontes = ["Arial", "Impact", "Verdana", "Tahoma", "Courier New",\n                  "Times New Roman", "Comic Sans MS"]',
    'fontes = ["Arial", "Montserrat", "Impact", "Verdana", "Tahoma", "Courier New",\n                  "Times New Roman", "Comic Sans MS"]'
)

# Also add robust logging to see exactly why dragging fails!
code = code.replace(
    '''    def on_frase_release(self, event):\n        if hasattr(self, '_drag_frase_idx'):''',
    '''    def on_frase_release(self, event):\n        if hasattr(self, '_drag_frase_idx'):\n            with open('drag_log.txt', 'a') as f: f.write(f"RELEASE idx={self._drag_frase_idx}, sel={getattr(self, 'video_frase_selecionado', 'None')}\\n")'''
)

code = code.replace(
    '''    def on_frase_drag(self, event):\n        if hasattr(self, '_drag_frase_idx'):''',
    '''    def on_frase_drag(self, event):\n        if hasattr(self, '_drag_frase_idx'):\n            pass #with open('drag_log.txt', 'a') as f: f.write(f"DRAG dx={event.x - self._drag_start_x} dy={event.y - self._drag_start_y}\\n")'''
)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched fonts and added log")
