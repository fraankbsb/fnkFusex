def detectar_crop_automatico(self, video_path):
    import subprocess, re
    cmd = [
        'ffmpeg', '-i', str(video_path), 
        '-t', '1', '-vf', 'cropdetect=24:16:0', 
        '-f', 'null', '-'
    ]
    try:
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
        match = re.search(r'crop=([0-9]+:[0-9]+:[0-9]+:[0-9]+)', result.stderr)
        if match:
            return match.group(1)
    except Exception as e:
        print(f"Erro no crop: {e}")
    return None
