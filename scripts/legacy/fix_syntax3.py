with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

import re
code = re.sub(r'lista_frases = \[p\.strip\(\) for p in conteudo\.split\(\"[\s\S]*?if l\.strip\(\)\]', 'lista_frases = [p.strip() for p in conteudo.split("\\n\\n") if p.strip()] if "\\n\\n" in conteudo else [l.strip() for l in conteudo.split("\\n") if l.strip()]', code)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Fixed syntax")
