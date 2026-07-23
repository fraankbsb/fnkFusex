with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing_methods = '''    def ao_mudar_cor_fundo(self, escolha):
        self.salvar_config()
        self.atualizar_preview()

    def ao_mudar_borda(self, escolha):
        self.salvar_config()
        self.atualizar_preview()

    def _construir_interface'''

code = code.replace('    def _construir_interface', missing_methods)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched missing methods 2")
