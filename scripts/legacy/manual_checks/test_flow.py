class MockApp:
    def __init__(self):
        self.frases_por_video = {"video.mp4": [{"texto": "test", "x": 540, "y": 960}]}
        self.video_frase_selecionado = "video.mp4"
        self._drag_frase_idx = 0
        self._frases_images_data = {0: (15, 15)}
        self.coords = [215, 500] # Simulated dropped coordinate

    def on_frase_release(self):
        scale_w = 1080 / 360 # 3.0
        scale_h = 1920 / 640 # 3.0
        
        offset_x, offset_y = self._frases_images_data[self._drag_frase_idx]
        real_x = int((self.coords[0] + offset_x) * scale_w)
        real_y = int((self.coords[1] + offset_y) * scale_h)
        
        print("real_x:", real_x, "real_y:", real_y)
        
        if self.video_frase_selecionado:
            frases = self.frases_por_video.get(self.video_frase_selecionado, [])
            print("Before:", frases)
            if 0 <= self._drag_frase_idx < len(frases):
                frases[self._drag_frase_idx]["x"] = real_x
                frases[self._drag_frase_idx]["y"] = real_y
            print("After:", self.frases_por_video)

app = MockApp()
app.on_frase_release()
