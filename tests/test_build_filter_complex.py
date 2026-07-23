"""Real pytest coverage for the core compositing logic (no ffmpeg execution, no I/O)."""
from editor_automacao import build_filter_complex, get_res_dimensions


def base_configs(**overrides):
    configs = {
        'pixels_y': 682,
        'cor_fundo_video': 'black',
        'resolucao': '1080p',
        'esticar': False,
        'anti_dup': False,
        'wm_text': '',
    }
    configs.update(overrides)
    return configs


def test_get_res_dimensions_known_values():
    assert get_res_dimensions("2160p") == (2160, 3840)
    assert get_res_dimensions("1440p") == (1440, 2560)
    assert get_res_dimensions("1080p") == (1080, 1920)


def test_get_res_dimensions_unknown_defaults_to_720p():
    assert get_res_dimensions("qualquer_coisa") == (720, 1280)


def test_build_filter_complex_no_template_uses_background_color():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, last_out = build_filter_complex("input.mp4", "", base_configs(), None, out_w, out_h)
    assert "color=c=black" in filtros
    assert last_out == "[out1]"


def test_build_filter_complex_no_template_transparent_skips_background():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, last_out = build_filter_complex(
        "input.mp4", "", base_configs(cor_fundo_video="transparent"), None, out_w, out_h
    )
    assert "color=c=" not in filtros
    assert "[vid]null[out1]" in filtros


def test_build_filter_complex_watermark_appends_drawtext_stage():
    out_w, out_h = get_res_dimensions("1080p")
    configs = base_configs(
        wm_text="@marca", wm_opacidade=100, wm_x=25, wm_y=800, wm_tamanho=36,
        wm_cor="white", wm_fonte="Arial",
    )
    filtros, last_out = build_filter_complex("input.mp4", "", configs, None, out_w, out_h)
    assert "drawtext=" in filtros
    assert last_out == "[out2]"
    # No stray comma between the previous stage's output label and drawtext: a comma there
    # makes ffmpeg parse an empty filter name and fail with "No such filter: ''".
    assert ",drawtext=" not in filtros
    assert "[out1]drawtext=" in filtros


def test_build_filter_complex_anti_dup_appends_eq_stage():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, last_out = build_filter_complex("input.mp4", "", base_configs(anti_dup=True), None, out_w, out_h)
    assert "eq=brightness=0.01:contrast=1.01" in filtros
    assert last_out == "[finalv]"


def test_build_filter_complex_video_config_overrides_zoom_and_position():
    out_w, out_h = get_res_dimensions("1080p")
    video_config = {"y": 100, "x": 50, "zoom": 0.5, "stretch_x": 1.0}
    filtros, _ = build_filter_complex("input.mp4", "", base_configs(), video_config, out_w, out_h)
    assert f"scale={int(out_w * 0.5)}" in filtros or f"scale={int(out_w * 0.5) + 1}" in filtros


def test_build_filter_complex_preencher_ignores_zoom_and_fits_exact_width():
    out_w, out_h = get_res_dimensions("1080p")
    # Mesmo com zoom reduzido, o modo "Preencher" deve ignorá-lo e encaixar a largura
    # exatamente em out_w, mantendo a proporção (altura automática via -2).
    video_config = {"y": 100, "x": 50, "zoom": 0.5, "stretch_x": 1.0}
    filtros, _ = build_filter_complex(
        "input.mp4", "", base_configs(aspect_video="Preencher"), video_config, out_w, out_h
    )
    assert f"scale={out_w}:-2[vid]" in filtros


def test_build_filter_complex_no_aspect_video_skips_extra_crop():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, _ = build_filter_complex("input.mp4", "", base_configs(), None, out_w, out_h)
    assert "min(iw" not in filtros


def test_build_filter_complex_aspect_video_1x1_crops_square_centered():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, _ = build_filter_complex("input.mp4", "", base_configs(aspect_video="1:1"), None, out_w, out_h)
    assert "crop=w='min(iw\\,ih*1.0)':h='min(ih\\,iw/1.0)'" in filtros
    # A proporção só recorta o vídeo — o canvas de saída (fundo/template) continua no tamanho normal.
    assert f"s={out_w}x{out_h}" in filtros or f":s={out_w}x{out_h}" in filtros


def test_build_filter_complex_aspect_video_4x5():
    out_w, out_h = get_res_dimensions("1080p")
    filtros, _ = build_filter_complex("input.mp4", "", base_configs(aspect_video="4:5"), None, out_w, out_h)
    assert "ih*0.8" in filtros
