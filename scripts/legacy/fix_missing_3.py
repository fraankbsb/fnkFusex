with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing = '''    def debounce_atualizar_grid(self):
        if hasattr(self, "_debounce_timer"):
            self.after_cancel(self._debounce_timer)
        self._debounce_timer = self.after(500, self.renderizar_grid)

    def sincronizar_frases_txt(self):
        videos = list(self.videos_frases)
        if not videos:
            messagebox.showwarning("Aviso", "Não há vídeos carregados!")
            return
        caminho_arquivo = filedialog.askopenfilename(title="Selecionar arquivo de frases (.txt)", filetypes=[("Text", "*.txt")])
        if not caminho_arquivo:
            return
        try:
            with open(caminho_arquivo, "r", encoding="utf-8") as f:
                linhas = f.readlines()
            conteudo = "".join(linhas).strip()
            lista_frases = [p.strip() for p in conteudo.split("\n\n") if p.strip()] if "\n\n" in conteudo else [l.strip() for l in conteudo.split("\n") if l.strip()]
            count = 0
            for i, video in enumerate(videos):
                if i < len(lista_frases):
                    self.frases_por_video[str(video)] = [{
                        "id": self._proximo_id_frase(),
                        "texto": lista_frases[i],
                        "fonte": "Arial",
                        "tamanho": 48,
                        "cor": "white",
                        "negrito": True,
                        "italico": False,
                        "inicio": 0.0,
                        "fim": 5.0,
                        "x": 540,
                        "y": 960,
                        "posicao_preset": "Centro"
                    }]
                    count += 1
            self.salvar_config()
            self._atualizar_lista_videos_frases()
            self.pf_lbl_status.configure(text=f"{count} vídeos processados.")
            if self.video_frase_selecionado:
                self._atualizar_lista_frases(self.video_frase_selecionado)
                self.desenhar_frases_no_canvas()
        except Exception as e:
            messagebox.showerror("Erro", str(e))

    def _construir_interface'''

code = code.replace('    def _construir_interface', missing)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched missing methods 3")
