AGENTS — Instruções para agentes de código

Propósito
- Fornecer orientações curtas e acionáveis para agentes que trabalham neste repositório.

Comportamento esperado
- Seja conservador: não modifique artefatos de build (`build/`, `dist_build/`) sem pedir.
- Execute testes antes de propor alterações que afetem lógica: `pytest -q`.
- Ao propor mudanças amplas, solicite confirmação do usuário.

Comandos úteis
- Testes: `pytest -q` (o repositório contém muitos arquivos `test_*.py`).
- Build (PyInstaller): `pyinstaller --clean TemplaterFNK.spec` ou `pyinstaller --clean editor_automacao.spec` (existem `.spec` para empacotamento).
- Executar script principal: `python editor_automacao.py` ou `python check_pixels.py` conforme o objetivo.

Arquivos e pastas-chave
- [editor_automacao.py](editor_automacao.py) — script de automação principal.
- [TemplaterFNK.spec](TemplaterFNK.spec), [editor_automacao.spec](editor_automacao.spec) — specs do PyInstaller.
- [build/](build/) e [dist_build/](dist_build/) — artefatos de build (não editar diretamente).
- Vários testes: arquivos `test_*.py` na raiz (por exemplo [test_flow.py](test_flow.py)).
- Scripts utilitários: [check_pixels.py](check_pixels.py), [fix_* .py] — correções/patches úteis para manutenção.

Convenções e armadilhas comuns
- Testes seguem padrão `test_*.py` e usam pytest.
- Projeto parece empacotado com PyInstaller; evitar commitar artefatos gerados por ele.
- Ambiente alvo provável: Windows (arquivos `.spec`, pastas `localpycs` em builds).

Boas práticas para agentes
- Linke, não copie: referencie documentação existente em vez de duplicar conteúdo.
- Mantenha alterações pequenas e verificáveis; rode testes e peça revisão humana para mudanças grandes.

Feedback
- Se algo estiver incorreto ou faltando, responda com o que deve ser ajustado e atualizo este arquivo.
