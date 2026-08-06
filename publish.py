#!/usr/bin/env python3
"""
publish.py — roda no PC de edicao (onde voce mexe no editor_automacao.py).
Builda o Fusex.exe com PyInstaller, empacota num zip e publica uma nova
Release no GitHub usando o GitHub CLI (gh). Tambem commita e da push no
codigo-fonte (o .exe NUNCA e commitado no git, so vai como asset da release).

Uso manual:
    python publish.py 1.0.1 "Corrige bug X"

Uso automatico (versao/mensagem geradas sozinhas):
    python publish.py auto
"""

import sys
import json
import shutil
import subprocess
import zipfile
from datetime import datetime
from pathlib import Path

APP_DIR       = Path(__file__).resolve().parent
VERSION_FILE  = APP_DIR / "version.json"
CONFIG_FILE   = APP_DIR / "update_config.json"
SPEC_FILE     = APP_DIR / "TemplaterFNK.spec"
EXE_NOME      = "Fusex.exe"
LAUNCHER_EXE  = "FusexLauncher.exe"
LAUNCHER_ZIP  = "launcher_setup.zip"

_CAMINHOS_GH_CONHECIDOS = [
    r"C:\Program Files\GitHub CLI\gh.exe",
    r"C:\Program Files (x86)\GitHub CLI\gh.exe",
]


def resolver_gh():
    """Encontra o executavel do gh mesmo se o PATH da sessao atual nao tiver sido atualizado."""
    encontrado = shutil.which("gh")
    if encontrado:
        return encontrado
    for caminho in _CAMINHOS_GH_CONHECIDOS:
        if Path(caminho).exists():
            return caminho
    print("ERRO: nao encontrei o executavel do GitHub CLI (gh). Instale com: winget install GitHub.cli")
    sys.exit(1)


GH = resolver_gh()

# Arquivos que entram no pacote de atualizacao (NUNCA incluir config.json do
# usuario, videos, templates ou qualquer coisa pessoal!)
ARQUIVOS_PAYLOAD = [APP_DIR / EXE_NOME, VERSION_FILE]


def ler_repo():
    cfg = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
    repo = cfg.get("repo", "")
    if not repo or "/" not in repo or repo == "OWNER/REPO":
        print("ERRO: configure 'repo' em update_config.json (formato OWNER/REPO) antes de publicar.")
        sys.exit(1)
    return repo


def ler_versao_atual():
    try:
        return json.loads(VERSION_FILE.read_text(encoding="utf-8")).get("version", "1.0.0")
    except Exception:
        return "1.0.0"


def proxima_versao_patch(versao_atual):
    partes = versao_atual.split(".")
    while len(partes) < 3:
        partes.append("0")
    major, minor, patch = partes[0], partes[1], partes[2]
    return f"{major}.{minor}.{int(patch) + 1}"


def buildar_exe():
    print("  🔨  Buildando Fusex.exe com PyInstaller...")
    resultado = subprocess.run(["pyinstaller", str(SPEC_FILE), "--noconfirm"], cwd=APP_DIR)
    if resultado.returncode != 0:
        print("  ❌  Falha ao buildar o .exe. Corrija o erro acima antes de publicar.")
        sys.exit(resultado.returncode)
    exe_gerado = APP_DIR / "dist" / EXE_NOME
    if not exe_gerado.exists():
        print(f"  ❌  Build terminou mas nao encontrei {exe_gerado}.")
        sys.exit(1)
    shutil.copy2(exe_gerado, APP_DIR / EXE_NOME)
    print(f"  ✓  {EXE_NOME} buildado e copiado pra raiz.")


def commitar_e_dar_push(mensagem):
    # git add -A (nao so os arquivos do payload) — senao mudancas em outros
    # arquivos do projeto (launcher.py, o proprio publish.py, etc) ficam
    # penduradas sem commit. O .gitignore ja protege o config.json do usuario
    # e os *.exe (o Fusex.exe so vai pro GitHub como asset de release, nunca
    # commitado no git).
    subprocess.run(["git", "add", "-A"], cwd=APP_DIR)
    resultado = subprocess.run(
        ["git", "commit", "-m", mensagem], cwd=APP_DIR, capture_output=True, text=True
    )
    if resultado.returncode != 0:
        if "nothing to commit" in resultado.stdout:
            # Nada novo alem do version.json/republicacao — nao trava o script,
            # so segue direto pro push/release.
            print("  ℹ️  Nada novo pra commitar alem da versao, seguindo pro push/release.")
        else:
            print(f"  ⚠️  git commit: {resultado.stdout.strip()} {resultado.stderr.strip()}")
    subprocess.run(["git", "push"], cwd=APP_DIR)


def montar_launcher_setup():
    """Empacota o launcher ja compilado + update_config.json num zip de nome
    FIXO (launcher_setup.zip), publicado em toda release. Isso cria um link
    permanente (releases/latest/download/launcher_setup.zip) pra instalar o
    app do zero num PC novo, sem precisar trocar o link a cada versao. O
    FusexLauncher.exe em si so precisa ser recompilado se o launcher.py MESMO
    mudar — aqui so reempacotamos o que ja existe na pasta."""
    launcher_exe = APP_DIR / LAUNCHER_EXE
    if not launcher_exe.exists():
        print(f"  ⚠️  {LAUNCHER_EXE} nao encontrado — pulando o pacote de instalacao inicial "
              f"({LAUNCHER_ZIP}). Compile uma vez com:\n"
              f"      python -m PyInstaller --onefile --windowed --name FusexLauncher "
              f"--distpath . --workpath build launcher.py")
        return None
    zip_path = APP_DIR / LAUNCHER_ZIP
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.write(launcher_exe, arcname=LAUNCHER_EXE)
        zf.write(CONFIG_FILE, arcname=CONFIG_FILE.name)
    print(f"  ✓  Pacote criado: {zip_path.name}")
    return zip_path


def main():
    modo_auto = len(sys.argv) >= 2 and sys.argv[1] == "auto"

    if modo_auto:
        atual       = ler_versao_atual()
        nova_versao = proxima_versao_patch(atual)
        mensagem    = f"Auto update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    elif len(sys.argv) >= 2:
        nova_versao = sys.argv[1].lstrip("v")
        mensagem    = sys.argv[2] if len(sys.argv) > 2 else f"Versao {nova_versao}"
    else:
        print("Uso: python publish.py <versao> [mensagem]  |  python publish.py auto")
        print('Exemplo: python publish.py 1.0.1 "Corrige o crop invalido"')
        sys.exit(1)

    repo = ler_repo()

    # 1. Builda o .exe mais recente
    buildar_exe()

    # 2. Atualiza version.json
    VERSION_FILE.write_text(json.dumps({"version": nova_versao}, indent=2), encoding="utf-8")
    print(f"  ✓  version.json atualizado para {nova_versao}")

    # 3. Commit + push do codigo-fonte (mantem o repo em dia)
    commitar_e_dar_push(mensagem)

    # 4. Monta o zip do payload (nome tem que comecar com "payload_" — e assim
    # que o launcher reconhece qual dos .zips da release e o autoupdate).
    zip_path = APP_DIR / f"payload_v{nova_versao}.zip"
    if zip_path.exists():
        zip_path.unlink()

    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for arquivo in ARQUIVOS_PAYLOAD:
            zf.write(arquivo, arcname=arquivo.name)
    print(f"  ✓  Pacote criado: {zip_path.name}")

    # 4b. Monta o pacote de instalacao inicial (launcher_setup.zip, nome fixo)
    launcher_zip_path = montar_launcher_setup()

    # 5. Cria a release no GitHub via gh CLI, com os dois assets
    tag = f"v{nova_versao}"
    arquivos_release = [str(zip_path)]
    if launcher_zip_path:
        arquivos_release.append(str(launcher_zip_path))
    cmd = [
        GH, "release", "create", tag,
        *arquivos_release,
        "--repo", repo,
        "--title", tag,
        "--notes", mensagem,
    ]
    print(f"  🚀  Publicando release {tag} no GitHub ({repo})...")
    resultado = subprocess.run(cmd, cwd=APP_DIR)

    zip_path.unlink()
    if launcher_zip_path:
        launcher_zip_path.unlink()

    if resultado.returncode == 0:
        print(f"  ✅  Release {tag} publicada! O botao 'Atualizar App' ja vai encontrar essa versao.")
        if launcher_zip_path:
            print(f"  🔗  Link permanente de instalacao: "
                  f"https://github.com/{repo}/releases/latest/download/{LAUNCHER_ZIP}")
    else:
        print("  ❌  Falha ao publicar a release. Veja o erro acima.")
        sys.exit(resultado.returncode)


if __name__ == "__main__":
    main()
