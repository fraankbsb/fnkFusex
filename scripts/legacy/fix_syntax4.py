with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
skip = False
for i, line in enumerate(lines):
    if skip:
        if '") if l.strip()]' in line:
            skip = False
            new_lines.append('            lista_frases = [p.strip() for p in conteudo.split("\\n\\n") if p.strip()] if "\\n\\n" in conteudo else [l.strip() for l in conteudo.split("\\n") if l.strip()]\n')
        continue
    
    if 'lista_frases = [p.strip() for p in conteudo.split("' in line and '") if p.strip()] if "' not in line:
        skip = True
        continue
        
    new_lines.append(line)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)
print("Fixed syntax")
