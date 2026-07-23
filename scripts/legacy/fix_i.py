with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

code = code.replace("for i, linha in enumerate(linhas):", "for i_line, linha in enumerate(linhas):")
code = code.replace("if i == 0:", "if i_line == 0:")

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print('Fixed i_line')
