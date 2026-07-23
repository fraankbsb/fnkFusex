with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

bad_code = '''            self.salvar_config()
            self._atualizar_lista_videos_frases()
            
                if self.video_frase_selecionado:
                    frases = self.frases_por_video.get(self.video_frase_selecionado, [])
                    if 0 <= self._drag_frase_idx < len(frases):
                        import tkinter.messagebox as mb
                        mb.showinfo("Debug Drag", f"idx={self._drag_frase_idx} coords={coords} offset={offset_x},{offset_y} scale={scale_w} real={real_x},{real_y} old_x={frases[self._drag_frase_idx].get('x')}")
                        frases[self._drag_frase_idx]["x"] = real_x
                        frases[self._drag_frase_idx]["y"] = real_y
                        self.salvar_config()
            self.pasta_entrada = pasta'''

good_code = '''            self.salvar_config()
            self._atualizar_lista_videos_frases()
            self.pf_lbl_status.configure(text=f"{count} vídeos processados.")
            if self.video_frase_selecionado:
                self._atualizar_lista_frases(self.video_frase_selecionado)
                self.desenhar_frases_no_canvas()
                
    def selecionar_entrada(self):
        pasta = filedialog.askdirectory(initialdir=self.ultima_pasta_entrada if self.ultima_pasta_entrada else os.path.expanduser("~"))
        if pasta:
            self.pasta_entrada = pasta'''

# I'm not 100% sure what was before self.pasta_entrada = pasta. 
# Let me just restore from a fresh copy of the code by removing the bad block and re-inserting the correct one using replace_file_content!
