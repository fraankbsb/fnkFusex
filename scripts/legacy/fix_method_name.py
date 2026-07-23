with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace(
    '    def adicionar_videos(self):',
    '    def selecionar_entrada(self):'
)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Renamed method")
