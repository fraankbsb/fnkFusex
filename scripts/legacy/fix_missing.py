with open('editor_automacao.py', 'r', encoding='utf-8') as f:
    code = f.read()

missing_methods = '''    def carregar_config(self):
        self.frases_por_video = {}
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.frases_por_video = dados.get("frases_por_video", {})
                    self.ultima_pasta_entrada = dados.get("ultima_pasta_entrada", "")
                    self.ultima_pasta_saida = dados.get("ultima_pasta_saida", "")
                    self.ultimo_template = dados.get("ultimo_template", "")
            except Exception:
                pass

    def salvar_config(self):
        try:
            import json
            dados = {
                "frases_por_video": getattr(self, "frases_por_video", {}),
                "ultima_pasta_entrada": getattr(self, "pasta_entrada", getattr(self, "ultima_pasta_entrada", "")),
                "ultima_pasta_saida": getattr(self, "pasta_saida", getattr(self, "ultima_pasta_saida", "")),
                "ultimo_template": getattr(self, "template_path", getattr(self, "ultimo_template", ""))
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def finalizar_processamento'''

code = code.replace('    def finalizar_processamento', missing_methods)

with open('editor_automacao.py', 'w', encoding='utf-8') as f:
    f.write(code)
print("Patched missing methods")
