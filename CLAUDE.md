# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

TemplaterFNK ("Cortador Pro FRANK") is a single-file Windows desktop app (`editor_automacao.py`) built with
CustomTkinter. It batch-processes videos through FFmpeg: overlaying them onto a template/background image,
applying zoom/crop/stretch/position transforms, adding a watermark, drawing custom text phrases per video
(via Pillow + Pilmoji for emoji support), and exporting the result. There is no test suite, no package
manifest, and no other source directory — everything lives in this one ~2000-line script.

## Running

```
pip install -r requirements.txt
python editor_automacao.py
```

Requires `customtkinter`, `Pillow`, `pilmoji`, and a `ffmpeg` binary on PATH (FFmpeg is invoked via
`subprocess.run(["ffmpeg", ...])`, never as a library).

## Testing

```
pytest -q
```

`pytest.ini` restricts collection to `tests/`, which only contains real pytest test functions
(`test_build_filter_complex.py` covers the core filter-graph logic in isolation; `test_engine.py` is a
guarded integration check that skips itself if the hardcoded sample video path doesn't exist on the current
machine). Legacy ad-hoc scripts that print/inspect output visually rather than assert anything live in
`scripts/legacy/manual_checks/` and are intentionally excluded from pytest collection — run them directly
with `python` if you need to eyeball font/emoji/spacing rendering.

## Building the .exe

Built with PyInstaller using the spec file:

```
pyinstaller TemplaterFNK.spec
```

`editor_automacao.spec` is a near-duplicate spec that only differs in output name (`editor_automacao` vs
`TemplaterFNK`) — treat `TemplaterFNK.spec` as canonical unless told otherwise. Both bundle `app_icon.ico`
as a data file and produce a console-enabled exe (not windowed), so stdout/stderr are visible when run from
`dist/`. `resource_path()` in `editor_automacao.py` resolves bundled resources via `sys._MEIPASS` when frozen.

## Sistema de auto-update

O app roda em varios PCs. Em vez de copiar `Fusex.exe` manualmente entre eles, existe um sistema de
launcher + releases no GitHub, no mesmo molde do `fnkDownloader` (`D:\fnkSocialMidia\fnkDonwloader`) —
unica diferenca real: aqui o payload publicado e o **binario `Fusex.exe` ja compilado** (nao um script
`.py`), porque o app depende de customtkinter/Pillow/pilmoji/ffmpeg e as maquinas de destino nao tem
Python instalado, so o launcher.

- **Repositorio**: `fraankbsb/fnkFusex` no GitHub, **publico** (unico repositorio, criado uma vez —
  comecou privado e foi trocado pra publico logo em seguida, nunca apagado/recriado). Precisa ser publico
  porque o `launcher.py` consulta a API do GitHub sem autenticacao (igual ao fnkDownloader); com o repo
  privado, `GET /repos/{repo}/releases/latest` retorna 404 mesmo pra quem tem acesso, e nao ha token
  embutido no launcher (embutir um token no `.exe` distribuido seria extraivel por qualquer um que tivesse
  o arquivo). Nao reverter pra privado sem resolver esse problema de autenticacao antes.
- **`launcher.py`** → compilado em `FusexLauncher.exe` (PyInstaller `--onefile --windowed`). Tem 2 botoes:
  "Atualizar App" (consulta a release mais recente, baixa o asset `payload_*.zip` — nunca "o primeiro .zip
  que achar", ver nota de bug abaixo — e sobrescreve o `Fusex.exe` local) e "Iniciar App" (abre `Fusex.exe`
  direto via `subprocess.Popen`, sem precisar de python na maquina). So precisa recompilar quando
  `launcher.py` MESMO muda — mudancas em `editor_automacao.py` nao exigem recompilar o launcher, so
  publicar release normal (`publish.py`). Comando de build:
  `python -m PyInstaller --onefile --windowed --name FusexLauncher --distpath . --workpath build launcher.py`
  seguido de `rm -rf build FusexLauncher.spec`.
  **Bug real ja corrigido:** uma release tem DOIS assets `.zip` (`payload_vX.Y.Z.zip` e
  `launcher_setup.zip`, ver `publish.py` abaixo) — pegar "o primeiro .zip da lista" pode escolher o
  `launcher_setup.zip` por engano e o launcher tenta sobrescrever o proprio `.exe` em execucao, o que o
  Windows bloqueia (`PermissionError: [Errno 13]`). `escolher_asset_payload()` exige o prefixo `payload_`
  no nome do asset, e `aplicar_update()` tem uma segunda camada de protecao: nunca extrai um arquivo cujo
  nome bata com o do proprio `.exe` do launcher em execucao (`LAUNCHER_EXE_NOME`), nao importa o que vier
  dentro do zip.
- **`publish.py`** → roda no PC de edicao. Builda o `Fusex.exe` com `pyinstaller TemplaterFNK.spec`, sobe a
  versao (patch +1) em `version.json`, da commit+push no repo (codigo-fonte, nunca o `.exe` — se nao
  houver nada novo alem da versao, o commit e pulado sem travar o script), empacota `Fusex.exe` +
  `version.json` em `payload_vX.Y.Z.zip` e publica como GitHub Release via `gh release create`. Uso:
  `python publish.py auto` (versao/mensagem automaticas) ou `python publish.py 1.0.1 "mensagem"`.
  Tambem monta e publica, na MESMA release, um segundo asset de nome **fixo** (`launcher_setup.zip` =
  `FusexLauncher.exe` + `update_config.json`, via `montar_launcher_setup()`) — isso cria um link
  permanente `github.com/fraankbsb/fnkFusex/releases/latest/download/launcher_setup.zip` pra instalar em
  PC novo do zero, sem precisar trocar link a cada versao (nao precisa mais reanexar manualmente o
  launcher a cada release). Se `FusexLauncher.exe` nao existir na pasta (ainda nao foi compilado), esse
  passo e pulado com aviso — o `payload_*.zip` do app sai normalmente.
- **`watch_and_publish.py`** + **`iniciar_vigia.bat`** → vigia que fica monitorando `editor_automacao.py` e
  `TemplaterFNK.spec`; ao detectar mudanca salva, espera 8s de silencio e chama `publish.py auto` sozinho.
  Dar duplo-clique no `.bat` no inicio de uma sessao de edicao.
- **`update_config.json`** → config do projeto: `repo` (`fraankbsb/fnkFusex`), `entry_point` (`Fusex.exe`),
  `app_title`, `payload_files` (`["Fusex.exe"]`). `version.json` guarda a versao local instalada.
- `Fusex.exe`, `FusexLauncher.exe` e `*.exe` em geral **nunca sao commitados no git** (`.gitignore`, junto
  com `payload_v*.zip` e `launcher_setup.zip`) — so existem localmente (build) e como asset anexado nas
  GitHub Releases. Isso evita inchar o historico do repo a cada rebuild.
- Numeracao de versao so pode subir (nunca republicar com o mesmo numero ou menor, senao o launcher nao
  detecta a atualizacao).
- `editor_automacao.py` tenta instalar o `ffmpeg` sozinho via `winget` (`_garantir_ffmpeg()`, chamada antes
  de abrir a UI) se nao encontrar no PATH — util em PC novo que so tem o launcher. Sempre passa
  `--source winget` explicito: sem isso o winget busca em todas as fontes por padrao (inclusive
  `msstore`), que falha com erro de certificado (`0x8a15005e`) em varios PCs mesmo quando o pacote so
  existe na fonte winget.

## Repo hygiene notes

The root directory contains many one-off `fix_*.py`, `patch_*.py`, `test_*.py`, and `debug_*.py` scripts and
sample images/videos left over from ad-hoc debugging sessions. These are not a test suite and are not wired
into any build or CI process — don't assume they still apply to the current state of `editor_automacao.py`.
`build/` and `dist/`/`dist_build/` are PyInstaller output directories, not source.

## Architecture

Everything is in `editor_automacao.py`, structured as two classes plus one big filter-building function:

- **`build_filter_complex()`** (module-level) — constructs the FFmpeg `-filter_complex` graph string as a
  function of the video's individual config (position, zoom, crop, stretch) and global config (resolution,
  background color/template, watermark text, "anti-duplication" tweaks). This is the single place that
  encodes how a video is composited onto the template. Preview rendering and final export both build their
  command through this function, so changes to compositing behavior should happen here, not duplicated
  elsewhere.
- **`ProcessadorVideo`** — the export engine. `iniciar()` spawns a background thread that iterates the
  video queue, calls `_executar_ffmpeg()` per video (which calls `build_filter_complex()` and shells out to
  `ffmpeg`), and reports progress/errors back to the UI via callbacks (`callback_progresso`,
  `callback_fim`). Runs off the Tk main thread — UI updates from these callbacks must stay thread-safe with
  Tk (the existing code does this via simple `.configure()`/messagebox calls from the callback, no explicit
  locking).
- **`EditorAutomaDarkApp(ctk.CTk)`** — the entire UI and application state. Key state held on `self`:
  - `videos_carregados`: list of loaded video paths (grid/queue view).
  - `configs_individuais`: `{str(video_path): {...per-video transform config...}}` (position, zoom, crop,
    stretch, etc.) — set via drag interactions on the preview canvas (`on_frase_press/drag/release` and
    similar handlers) or the individual-adjustment controls.
  - `frases_por_video`: `{str(video_path): [ {...phrase/text overlay config...}, ... ]}` — the "Editar
    Frases" tab lets users attach one or more draggable text overlays (font, size, color, position) to each
    video, rendered live via `desenhar_frases_no_canvas()` and persisted through `sincronizar_frases_txt()`.
  - Config persistence is manual JSON, not a framework: `carregar_config()`/`salvar_config()` read/write
    `config.json` in the working directory (last-used input/output folders, last template, and
    `frases_por_video`). This file is user machine state, not project config — don't treat it as a settings
    schema to extend casually.
  - The UI is tab-based (`switch_tab`/`mudar_aba`) with a live preview player that shells out to `ffmpeg`
    for frame generation/streaming (`iniciar_player`, `_loop_player`, `_atualizar_frame_player`) separately
    from the export path in `ProcessadorVideo`.

When changing compositing/rendering behavior, keep the preview path (`gerar_preview_visual`,
`atualizar_preview_frases`, the player) and the export path (`ProcessadorVideo._executar_ffmpeg`) in sync —
both ultimately depend on `build_filter_complex()` and the same `configs`/`configs_individuais`/
`frases_por_video` state, and diverging them is a common source of "preview doesn't match export" bugs.

## Video aspect ratio handling

Videos are always uploaded already pre-cropped to one of three native ratios: 1:1, 4:5, or 9:16 —
`build_filter_complex()` does **not** re-crop to force a ratio (that was removed; it caused unwanted
zoom/cropping on already-correct videos). The "Redimensionar para" panel (right side, below the preview)
only has 3 radio options (Feed Square 1:1, Feed Portrait 4:5, Stories 9:16 — no "Nenhum") plus a
Preencher/Ajustar toggle (cover vs contain).

Each ratio has a fixed default vertical position, applied automatically when the ratio is picked (single
video) or via "Aplicar a todos os vídeos" (`POSICAO_Y_PADRAO_ASPECT` dict + `_aplicar_posicao_padrao_aspect()`
in `editor_automacao.py`):
- **1:1** → y = 738.3
- **4:5** → y = 520.9
- **9:16** → y = 0, x = 0, mode forced to "preencher" (must fill the entire template)

All videos of the same ratio should land in the same position — don't reintroduce per-video origin-copy
logic for x/y when applying to all.

## Per-video card controls (grid view)

Each video card only has vertical-position buttons now (no zoom/stretch/left-right — videos already arrive
at the correct size): two rows of 3 buttons, `⬆1x ⬆2x ⬆3x` / `⬇1x ⬇2x ⬇3x`, moving the video up/down at 1x,
2x, or 3x the base step (20px). The card status label shows only `Y:<value>`. The crop-selection ("✂")
button was removed from the card header.

`detectar_crop_automatico()` (auto black-bar crop on video upload) uses the **last** stable `cropdetect`
match, not the first — early frames (fade-ins, black intros) can report invalid `crop=W:0:X:Y` boxes that
would otherwise crash ffmpeg. `build_filter_complex()` also defensively discards any stored crop with
zero width/height as a second line of defense for old `config.json` entries.

## No embedded cover (attached-pic) — removed on purpose

`ProcessadorVideo` used to have a `_gerar_capa()` step that embedded a cover image as an attached-pic
mjpeg stream inside the exported `.mp4` (extracted from the middle of the video). **Removed** — Instagram
doesn't read that embedded metadata anyway, and worse, the resulting file has two video streams (the real
h264 one plus the mjpeg attached-pic), which appears to confuse Instagram's own thumbnail generation:
videos exported with this enabled showed up as solid black tiles in the profile grid. Exported files are
now a single clean video+audio stream again, matching normal camera-recorded video structure. Don't
reintroduce attached-pic cover embedding without first confirming (on a real Instagram upload) that it
doesn't break thumbnail generation.

## Windows-specific export safety

`_executar_ffmpeg()` writes to a temp filename (`<stem>_tmp<suffix>`) in the output folder and only renames
over the final destination after ffmpeg exits 0. This avoids a Windows file-lock failure when the output
folder is the same as the input folder (reading and writing the same open file at once used to raise
`Exception(process.stderr)` even though the video had actually been produced correctly).
