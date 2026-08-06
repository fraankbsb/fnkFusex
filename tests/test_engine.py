from pathlib import Path

import pytest

from editor_automacao import ProcessadorVideo

# These paths are specific to the original developer's machine. This is an opportunistic
# integration check: it exercises the real ffmpeg pipeline end-to-end when the sample
# assets happen to be present locally, and skips cleanly (rather than passing vacuously
# or failing everywhere else) when they aren't.
INPUT_VIDEO = Path(__file__).parent / "fixtures" / "siga_esse_mesmo_padrão_continencia_202607120943.mp4"
TEMPLATE = Path(r"D:/fnkSocialMidia/fnkTemplates/Homens/CODIGODECONDUTABR/template_base.png")


@pytest.mark.skipif(not INPUT_VIDEO.exists(), reason="sample input video not present on this machine")
def test_executar_ffmpeg_produces_output_file(tmp_path):
    motor = ProcessadorVideo(lambda msg, perc: None, lambda s, t: None)
    output = tmp_path / "test_saida_final.mp4"

    configs = {
        'pixels_y': 682,
        'cor_fundo_video': 'black',
        'resolucao': '1080p',
        'audio_melhorado': True,
        'anti_dup': True,
        'wm_text': '@naturezamortal',
        'wm_cor': 'white',
        'wm_fonte': 'Arial',
        'wm_tamanho': 36,
        'wm_x': 25,
        'wm_y': 800,
        'wm_opacidade': 100
    }

    motor._executar_ffmpeg(INPUT_VIDEO, TEMPLATE, output, configs)

    assert output.exists()
    assert output.stat().st_size > 0
