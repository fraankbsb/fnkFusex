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
