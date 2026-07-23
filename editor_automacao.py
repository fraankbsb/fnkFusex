import sys, os
if sys.stdout is None:
    sys.stdout = open(os.devnull, 'w')
if sys.stderr is None:
    sys.stderr = open(os.devnull, 'w')
import os
import json
import threading
import subprocess
import time
from pathlib import Path
import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageStat, ImageDraw, ImageFont, ImageTk, ImageColor
from pilmoji import Pilmoji

import sys

def resource_path(relative_path):
    try:
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

# Configuração global
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("green")

GRID_COLS = 10
THUMB_W, THUMB_H = 84, 102

# Proporções de recorte disponíveis para o vídeo (largura/altura) — aplicadas somente
# ao vídeo em si, o template/canvas de saída continua com suas próprias dimensões.
ASPECT_RATIOS = {"1:1": 1.0, "4:5": 4 / 5}

def get_res_dimensions(res_str):
    if res_str == "2160p": return 2160, 3840
    if res_str == "1440p": return 1440, 2560
    if res_str == "1080p": return 1080, 1920
    return 720, 1280

def build_filter_complex(input_video_str, template_path, configs, video_config, out_w, out_h, is_preview=False):
    filtros = []
    descer_y = video_config['y'] if video_config else configs['pixels_y']
    mover_x = video_config['x'] if video_config else 0
    zoom = video_config['zoom'] if video_config else 1.0
    stretch_x = video_config.get('stretch_x', 1.0) if video_config else 1.0
    crop_str = f"crop={video_config['crop']}," if (video_config and video_config.get('crop')) else ""

    # Proporção do vídeo (recorte centralizado — não afeta o canvas/template de saída)
    aspect_crop_str = ""
    ratio = ASPECT_RATIOS.get(configs.get('aspect_video'))
    if ratio:
        aspect_crop_str = f"crop=w='min(iw\\,ih*{ratio})':h='min(ih\\,iw/{ratio})',"

    # Escala base (aplica o zoom)
    base_w = int(out_w * zoom)
    base_w = base_w if base_w % 2 == 0 else base_w + 1

    if configs.get('aspect_video') == 'Preencher':
        # Encaixa a largura do vídeo exatamente nas laterais do template (out_w), mantendo
        # a proporção original (altura calculada automaticamente) — sem esticar/distorcer
        # e ignorando zoom/largura manual, para garantir preenchimento perfeito e sem gaps.
        filtros.append(f"[0:v]{crop_str}{aspect_crop_str}scale={out_w}:-2[vid]")
    elif configs.get('esticar'):
        # Força a altura para preencher, e aplica stretch_x na largura
        scale_w = int(out_w * zoom * stretch_x)
        scale_w = scale_w if scale_w % 2 == 0 else scale_w + 1
        scale_h = int(out_h * zoom)
        scale_h = scale_h if scale_h % 2 == 0 else scale_h + 1
        filtros.append(f"[0:v]{crop_str}{aspect_crop_str}scale={scale_w}:{scale_h}[vid]")
    else:
        # Mantém a proporção original na altura, mas estica a largura independentemente
        filtros.append(f"[0:v]{crop_str}{aspect_crop_str}scale={base_w}:-2,scale=iw*{stretch_x}:ih[vid]")
        
    # Fundo / Template
    if template_path and Path(template_path).exists():
        filtros.append(f"[1:v]scale={out_w}:{out_h}[bg];[bg][vid]overlay=(W-w)/2+({mover_x}):({descer_y})[out1]")
    else:
        cor_fundo = configs.get('cor_fundo_video', 'black')
        if cor_fundo in ["transparent", "Nenhum (Normal)"]:
            filtros.append(f"[vid]null[out1]")
        else:
            filtros.append(f"color=c={cor_fundo}:s={out_w}x{out_h}[bg];[bg][vid]overlay=(W-w)/2+({mover_x}):({descer_y}):shortest=1[out1]")

    # Marca d'água
    drawtext = ""
    if configs.get('wm_text'):
        opac = configs['wm_opacidade'] / 100.0
        x = configs['wm_x']
        y = configs['wm_y']
        size = configs['wm_tamanho']
        cor = configs['wm_cor']
        # Ajusta coords/size se a resolução for maior que 1080p proporcionalmente?
        # O usuário setou via UI pensando em 1080p, vamos escalar a fonte e posições
        scale_factor = out_w / 1080.0
        x_scaled = int(x * scale_factor)
        y_scaled = int(y * scale_factor)
        size_scaled = int(size * scale_factor)
        
        drawtext = f"drawtext=font='{configs.get('wm_fonte', 'Arial')}':text='{configs['wm_text']}':fontcolor={cor}@{opac}:fontsize={size_scaled}:x={x_scaled}:y={y_scaled}"
        
    last_out = "[out1]"
    if drawtext:
        filtros.append(f"{last_out}{drawtext}[out2]")
        last_out = "[out2]"
        
    # Anti Duplicidade
    if configs.get('anti_dup'):
        filtros.append(f"{last_out}eq=brightness=0.01:contrast=1.01[finalv]")
        last_out = "[finalv]"
        
    return ";".join(filtros), last_out

class ProcessadorVideo:
    def __init__(self, callback_progresso, callback_fim):
        self.callback_progresso = callback_progresso
        self.callback_fim = callback_fim
        self.is_processing = False
        
    def iniciar(self, videos, template_por_video, output_folder, configs, configs_individuais):
        if self.is_processing: return
        self.is_processing = True
        t = threading.Thread(target=self._processar_fila, args=(videos, template_por_video, output_folder, configs, configs_individuais))
        t.start()

    def _processar_fila(self, videos, template_por_video, output_folder, configs, configs_individuais):
        total = len(videos)
        sucessos = 0
        for i, video in enumerate(videos):
            self.callback_progresso(f"Processando {i+1}/{total}: {video.name}", (i / total))
            output_path = Path(output_folder) / f"{video.name}"
            video_config = configs_individuais.get(str(video))
            template_video = template_por_video.get(str(video), "")
            try:
                self._executar_ffmpeg(video, template_video, output_path, configs, video_config)
                sucessos += 1
            except Exception as e:
                import tkinter.messagebox
                tkinter.messagebox.showerror("Erro de Processamento", f"Falha ao processar {video.name}:\n\n{str(e)}")
        self.callback_progresso("Processamento Concluído!", 1.0)
        self.is_processing = False
        self.callback_fim(sucessos, total)

    def _executar_ffmpeg(self, input_video, template_path, output_path, configs, video_config=None, extra_args=None):
        out_w, out_h = get_res_dimensions(configs['resolucao'])
        filtros_str, last_out = build_filter_complex(str(input_video), template_path, configs, video_config, out_w, out_h)
        
        cmd = ["ffmpeg", "-y"]
        cmd.extend(["-i", str(input_video)])
        
        if template_path and Path(template_path).exists():
            cmd.extend(["-i", str(template_path)])
            
        cmd.extend([
            "-filter_complex", filtros_str,
            "-map", last_out
        ])
        
        if extra_args and "-vframes" in extra_args:
            cmd.extend(extra_args)
            cmd.extend(["-update", "1"])
            cmd.append(str(output_path))
        else:
            cmd.extend(["-map", "0:a?"])
            if configs['audio_melhorado']:
                cmd.extend(["-c:a", "aac", "-b:a", "192k", "-af", "highpass=f=200,lowpass=f=3000"])
            else:
                cmd.extend(["-c:a", "aac", "-b:a", "128k"])
                
            cmd.extend(["-c:v", "libx264", "-preset", "veryfast", "-crf", "23"])
            if configs['anti_dup']:
                cmd.extend(["-r", "30.01", "-map_metadata", "-1"])
            cmd.append(str(output_path))
        
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, universal_newlines=True, creationflags=subprocess.CREATE_NO_WINDOW)
        if process.returncode != 0:
            raise Exception(process.stderr)


class EditorAutomaDarkApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("fnkTemplater")
        self.geometry("1600x900")
        self.state("zoomed")
        self.configure(fg_color="#2b2d31")
        try:
            self.iconbitmap(resource_path("app_icon.ico"))
        except:
            pass
        
        self.pasta_entrada = ""
        self.pasta_saida = ""
        self.template_path = ""
        self.templates_carregados = []
        self.template_por_video = {}
        self.videos_carregados = []
        self.video_preview_selecionado = None
        self.active_tab_index = 0
        
        self.configs_individuais = {}
        self.labels_status_indiv = {}
        self.labels_thumb_indiv = {}
        
        # Controle do Player
        self.player_ativo = False
        self.ffmpeg_process_player = None
        self.ffplay_audio_process = None
        
        self.config_file = "config.json"
        self.ultima_pasta_entrada = ""
        self.ultima_pasta_saida = ""
        self.ultimo_template = ""
        self.carregar_config()
        
        self.motor = ProcessadorVideo(self.atualizar_progresso, self.finalizar_processamento)
        self._construir_interface()
        self.bind("<Delete>", self.deletar_video_selecionado)
        
    def _ao_mudar_aspect_video(self):
        """A proporção afeta só o recorte do vídeo (o template/canvas de saída não muda)."""
        self.salvar_config()
        if self.videos_carregados:
            self.renderizar_grid()
        if self.video_preview_selecionado:
            self.gerar_preview_visual()

    def mover_wm(self, dx, dy):
        """Move a marca d'água pelos botões de seta da aba Marca.
        dx/dy em pixels (relativos à resolução 1080p).
        Atualiza os sliders de X e Y e dispara o preview.
        """
        # Lê valores atuais dos sliders
        novo_x = int(self.slider_x.get()) + dx
        novo_y = int(self.slider_y.get()) + dy

        # Clamp dentro dos limites dos sliders
        novo_x = max(0, min(1080, novo_x))
        novo_y = max(0, min(1920, novo_y))

        # Atualiza os sliders na UI
        self.slider_x.set(novo_x)
        self.slider_y.set(novo_y)

        # Marca d'água é redesenhada na hora, sem precisar re-renderizar o vídeo no ffmpeg
        self.atualizar_marca_dagua_preview()

    def _construir_interface(self):
        # Só a coluna central (grade de vídeos) recebe peso — as laterais (esquerda e
        # direita) ficam com largura fixa de verdade. Antes a coluna direita tinha
        # weight=1, então ela era esticada pelo grid além da largura configurada.
        self.grid_columnconfigure(1, weight=1)
        self.grid_columnconfigure(2, weight=0)
        self.grid_rowconfigure(0, weight=1)

        # ==================== PAINEL ESQUERDO ====================
        # Compacto (metade da largura original) para sobrar espaço para a grade de vídeos.
        self.painel_esq = ctk.CTkFrame(self, width=160, corner_radius=0, fg_color="#2b2d31")
        self.painel_esq.grid(row=0, column=0, sticky="nsew")
        self.painel_esq.grid_propagate(False)
        self.painel_esq.grid_columnconfigure(0, weight=1)
        self.painel_esq.grid_rowconfigure(2, weight=1)

        f_menu_topo = ctk.CTkFrame(self.painel_esq, fg_color="transparent")
        f_menu_topo.grid(row=0, column=0, sticky="ew", padx=8, pady=8)
        ctk.CTkLabel(f_menu_topo, text="fnkTemplater", font=ctk.CTkFont(size=13, weight="bold"), wraplength=140).pack(pady=(0, 5))
        btn_style = {"fg_color": "#383a40", "hover_color": "#474a51", "text_color": "white", "height": 28, "corner_radius": 6, "font": ctk.CTkFont(size=11)}
        ctk.CTkButton(f_menu_topo, text="📥 Enviar Vídeos", command=self.selecionar_entrada, **btn_style).pack(fill="x", pady=3)
        self.btn_template = ctk.CTkButton(f_menu_topo, text="🖼️ Template", command=self.selecionar_template, **btn_style)
        self.btn_template.pack(fill="x", pady=3)
        self.btn_processar = ctk.CTkButton(f_menu_topo, text="▶ PROCESSAR", command=self.iniciar_processamento, fg_color="#2ecc71", hover_color="#27ae60", text_color="white", height=34, corner_radius=6, font=ctk.CTkFont(weight="bold", size=11))
        self.btn_processar.pack(fill="x", pady=(10, 3))
        ctk.CTkButton(f_menu_topo, text="📁 Abrir Saída", command=self.selecionar_saida, **btn_style).pack(fill="x", pady=3)
        self.lbl_contador_esq = ctk.CTkLabel(f_menu_topo, text="📥 0 vídeo(s)", anchor="w", font=ctk.CTkFont(size=10), wraplength=140)
        self.lbl_contador_esq.pack(fill="x", pady=(8, 0))

        # --- Tabview Inferior ---
        self.tabview_configs = ctk.CTkTabview(self.painel_esq, fg_color="#232428", segmented_button_selected_color="#2ecc71")
        self.tabview_configs.grid(row=2, column=0, sticky="nsew", padx=6, pady=(0, 8))
        self.tabview_configs.add("Básico")
        self.tabview_configs.add("Marca")

        # TAB BÁSICO
        tab_basico = self.tabview_configs.tab("Básico")
        ctk.CTkLabel(tab_basico, text="Pixels p/ descer:", font=ctk.CTkFont(size=10), wraplength=130).pack(anchor="w", pady=(5,0))
        self.entry_pixels = ctk.CTkEntry(tab_basico, width=70)
        self.entry_pixels.insert(0, "682")
        self.entry_pixels.pack(anchor="w", pady=(0, 10))

        # (O redimensionamento/proporção do vídeo fica no painel de Preview, à direita.)
        self.var_aspect_video = ctk.StringVar(value="Nenhum")

        # TAB MARCA
        tab_marca = self.tabview_configs.tab("Marca")
        ctk.CTkLabel(tab_marca, text="Texto:", font=ctk.CTkFont(size=10)).pack(anchor="w")

        self.var_wm_text = ctk.StringVar(value="@naturezamortal")
        self.var_wm_text.trace_add("write", self.atualizar_marca_dagua_preview)
        self.entry_wm_text = ctk.CTkEntry(tab_marca, textvariable=self.var_wm_text, font=ctk.CTkFont(size=11))
        self.entry_wm_text.pack(fill="x", pady=(0, 8))

        self.cb_cor_wm = ctk.CTkComboBox(tab_marca, values=["white", "black", "red", "yellow"],
                                          command=self.atualizar_marca_dagua_preview, font=ctk.CTkFont(size=10))
        self.cb_cor_wm.pack(fill="x", pady=4)
        self.cb_fonte_wm = ctk.CTkComboBox(tab_marca, values=["Arial", "Impact", "Verdana", "Tahoma", "Courier New", "Comic Sans MS", "Times New Roman", "Montserrat"],
                                            command=self.atualizar_marca_dagua_preview, font=ctk.CTkFont(size=10))
        self.cb_fonte_wm.pack(fill="x", pady=4)

        f_wm_arrows = ctk.CTkFrame(tab_marca, fg_color="transparent")
        f_wm_arrows.pack(pady=8)
        btn_wm_up = ctk.CTkButton(f_wm_arrows, text="⬆️", width=24, height=24, fg_color="#f39c12", hover_color="#d68910", command=lambda: self.mover_wm(0, -20))
        btn_wm_up.grid(row=0, column=1, padx=2, pady=2)
        btn_wm_left = ctk.CTkButton(f_wm_arrows, text="⬅️", width=24, height=24, fg_color="#8e44ad", hover_color="#732d91", command=lambda: self.mover_wm(-20, 0))
        btn_wm_left.grid(row=1, column=0, padx=2, pady=2)
        btn_wm_right = ctk.CTkButton(f_wm_arrows, text="➡️", width=24, height=24, fg_color="#8e44ad", hover_color="#732d91", command=lambda: self.mover_wm(20, 0))
        btn_wm_right.grid(row=1, column=2, padx=2, pady=2)
        btn_wm_down = ctk.CTkButton(f_wm_arrows, text="⬇️", width=24, height=24, fg_color="#f39c12", hover_color="#d68910", command=lambda: self.mover_wm(0, 20))
        btn_wm_down.grid(row=2, column=1, padx=2, pady=2)

        f_sliders = ctk.CTkFrame(tab_marca, fg_color="#2b2d31")
        f_sliders.pack(fill="x", pady=8, ipady=4, ipadx=4)

        # Tamanho
        f_tam = ctk.CTkFrame(f_sliders, fg_color="transparent")
        f_tam.pack(fill="x", pady=2)
        ctk.CTkLabel(f_tam, text="Tam.", width=35, anchor="e", font=ctk.CTkFont(size=9)).pack(side="left", padx=3)
        self.slider_tam = ctk.CTkSlider(f_tam, from_=10, to=150, button_color="#2ecc71", command=self.atualizar_marca_dagua_preview)
        self.slider_tam.set(36)
        self.slider_tam.pack(side="left", fill="x", expand=True, padx=3)

        # Opacidade
        f_op = ctk.CTkFrame(f_sliders, fg_color="transparent")
        f_op.pack(fill="x", pady=2)
        ctk.CTkLabel(f_op, text="Opac.", width=35, anchor="e", font=ctk.CTkFont(size=9)).pack(side="left", padx=3)
        self.slider_opac = ctk.CTkSlider(f_op, from_=0, to=100, button_color="#2ecc71", command=self.atualizar_marca_dagua_preview)
        self.slider_opac.set(100)
        self.slider_opac.pack(side="left", fill="x", expand=True, padx=3)

        # X
        f_x = ctk.CTkFrame(f_sliders, fg_color="transparent")
        f_x.pack(fill="x", pady=2)
        ctk.CTkLabel(f_x, text="X", width=35, anchor="e", font=ctk.CTkFont(size=9)).pack(side="left", padx=3)
        self.slider_x = ctk.CTkSlider(f_x, from_=0, to=1080, button_color="#2ecc71", command=self.atualizar_marca_dagua_preview)
        self.slider_x.set(25)
        self.slider_x.pack(side="left", fill="x", expand=True, padx=3)

        # Y
        f_y = ctk.CTkFrame(f_sliders, fg_color="transparent")
        f_y.pack(fill="x", pady=2)
        ctk.CTkLabel(f_y, text="Y", width=35, anchor="e", font=ctk.CTkFont(size=9)).pack(side="left", padx=3)
        self.slider_y = ctk.CTkSlider(f_y, from_=0, to=1920, button_color="#2ecc71", command=self.atualizar_marca_dagua_preview)
        self.slider_y.set(800)
        self.slider_y.pack(side="left", fill="x", expand=True, padx=3)

        # ==================== ÁREA CENTRAL ====================
        self.area_central = ctk.CTkFrame(self, fg_color="#313338", corner_radius=0)
        self.area_central.grid(row=0, column=1, sticky="nsew")
        self.area_central.grid_rowconfigure(1, weight=1)
        self.area_central.grid_columnconfigure(0, weight=1)
        
        self.toolbar_grid = ctk.CTkFrame(self.area_central, fg_color="#2b2d31", corner_radius=0, height=50)
        self.toolbar_grid.grid(row=0, column=0, sticky="ew")
        self.f_tb = ctk.CTkFrame(self.toolbar_grid, fg_color="transparent")
        self.f_tb.pack(side="left", padx=15, pady=10, fill="x", expand=True)
        self.atualizar_abas()
        
        self.grid_frame = ctk.CTkScrollableFrame(self.area_central, fg_color="transparent")
        self.grid_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)

        # ==================== PAINEL DIREITO (Preview) ====================
        # Sem cabeçalhos redundantes — quase todo o espaço vertical vai para a visualização.
        self.painel_dir = ctk.CTkFrame(self, width=260, fg_color="#232428", corner_radius=0)
        self.painel_dir.grid(row=0, column=2, sticky="nsew")
        self.painel_dir.grid_propagate(False)
        self.painel_dir.grid_rowconfigure(1, weight=1)
        self.painel_dir.grid_columnconfigure(0, weight=1)

        f_timeline = ctk.CTkFrame(self.painel_dir, fg_color="#2b2d31", corner_radius=0)
        f_timeline.grid(row=0, column=0, sticky="ew")

        self.barra_status = ctk.CTkProgressBar(f_timeline, progress_color="#2ecc71", height=5, corner_radius=3)
        self.barra_status.pack(pady=(8, 4), fill="x", padx=12)
        self.barra_status.set(0)
        self.lbl_status = ctk.CTkLabel(f_timeline, text="Aguardando...",
                                        font=ctk.CTkFont(size=9), text_color="#9aa0a6", wraplength=220)
        self.lbl_status.pack(pady=(0, 6))

        # A Box da Imagem — o Canvas preenche 100% do container (sem moldura/padding
        # sobrando ao redor); o tamanho é recalculado dinamicamente em
        # _ajustar_tamanho_preview_canvas(), mantendo a proporção 9:16.
        self.f_image_container = ctk.CTkFrame(self.painel_dir, fg_color="transparent")
        self.f_image_container.grid(row=1, column=0, sticky="nsew")
        self.f_image_container.grid_rowconfigure(0, weight=1)
        self.f_image_container.grid_columnconfigure(0, weight=1)

        self.preview_canvas = ctk.CTkCanvas(self.f_image_container, bg="#0f1012", highlightthickness=0, width=234, height=416)
        self.preview_canvas.grid(row=0, column=0, pady=(4, 2))  # sem sticky: tamanho exato calculado dinamicamente
        self.preview_canvas.create_text(117, 208, text="Selecione um vídeo\npara ver o preview",
                                         fill="#5f6368", justify="center", font=("Segoe UI", 9), tags=("placeholder",))

        self.preview_canvas.tag_bind("wm", "<ButtonPress-1>", self.on_wm_press)
        self.preview_canvas.tag_bind("wm", "<B1-Motion>", self.on_wm_drag)
        self.preview_canvas.tag_bind("wm", "<ButtonRelease-1>", self.on_wm_release)
        self.f_image_container.bind("<Configure>", self._ajustar_tamanho_preview_canvas)

        self.btn_play_preview = ctk.CTkButton(self.f_image_container, text="▶", width=32, height=32, corner_radius=16,
                                               fg_color="white", text_color="black", hover_color="#ecf0f1",
                                               font=ctk.CTkFont(weight="bold", size=13), command=self.toggle_player)
        self.btn_play_preview.grid(row=1, column=0, pady=(2, 8))

        # Redimensionar vídeo (proporção) — logo abaixo do preview
        f_aspect = ctk.CTkFrame(self.f_image_container, fg_color="#2b2d31", corner_radius=8)
        f_aspect.grid(row=2, column=0, sticky="ew", padx=14, pady=(0, 8))
        ctk.CTkLabel(f_aspect, text="Redimensionar vídeo:", font=ctk.CTkFont(size=10, weight="bold")).pack(anchor="w", padx=8, pady=(6, 2))
        ctk.CTkRadioButton(f_aspect, text="Nenhum (original)", variable=self.var_aspect_video, value="Nenhum",
                            font=ctk.CTkFont(size=10), radiobutton_width=14, radiobutton_height=14,
                            command=self._ao_mudar_aspect_video).pack(anchor="w", padx=8, pady=2)
        ctk.CTkRadioButton(f_aspect, text="Feed Square — 1:1", variable=self.var_aspect_video, value="1:1",
                            font=ctk.CTkFont(size=10), radiobutton_width=14, radiobutton_height=14,
                            command=self._ao_mudar_aspect_video).pack(anchor="w", padx=8, pady=2)
        ctk.CTkRadioButton(f_aspect, text="Feed Portrait — 4:5", variable=self.var_aspect_video, value="4:5",
                            font=ctk.CTkFont(size=10), radiobutton_width=14, radiobutton_height=14,
                            command=self._ao_mudar_aspect_video).pack(anchor="w", padx=8, pady=2)
        ctk.CTkRadioButton(f_aspect, text="🔲 Preencher (encaixar nas laterais)", variable=self.var_aspect_video, value="Preencher",
                            font=ctk.CTkFont(size=10), radiobutton_width=14, radiobutton_height=14,
                            command=self._ao_mudar_aspect_video).pack(anchor="w", padx=8, pady=(2, 6))

        # Botão de exportar — mesma ação do "PROCESSAR VÍDEOS", exporta todos os vídeos da área de edição
        self.btn_exportar_preview = ctk.CTkButton(self.f_image_container, text="⬇ Exportar Vídeos",
                                                   command=self.iniciar_processamento,
                                                   fg_color="#2ecc71", hover_color="#27ae60", text_color="black",
                                                   height=38, corner_radius=8, font=ctk.CTkFont(weight="bold", size=12))
        self.btn_exportar_preview.grid(row=3, column=0, sticky="ew", padx=14, pady=(0, 14))

    def selecionar_entrada(self):
        arquivos = filedialog.askopenfilenames(
            title="Selecionar Vídeos",
            filetypes=[("Vídeos", "*.mp4 *.mov *.avi *.mkv")]
        )
        if arquivos:
            pasta = os.path.dirname(arquivos[0])
            self.pasta_entrada = pasta
            self.videos_carregados = [Path(f) for f in arquivos]
            total = len(self.videos_carregados)
            
            try: y_base = int(self.entry_pixels.get())
            except: y_base = 682
            
            self.configs_individuais.clear()
            for i, v in enumerate(self.videos_carregados):
                self.lbl_contador_esq.configure(text=f"Analisando bordas {i+1}/{total}...")
                self.update()
                crop_val = self.detectar_crop_automatico(str(v))
                self.configs_individuais[str(v)] = {'y': y_base, 'x': 0, 'zoom': 1.0, 'crop': crop_val}
            self._remapear_templates()

            self.lbl_contador_esq.configure(text=f"📥 {total} vídeo(s) adicionados")
            self.active_tab_index = 0
            self.atualizar_abas()
            self.renderizar_grid()

    def selecionar_template(self):
        dir_inicial = os.path.dirname(self.ultimo_template) if self.ultimo_template else os.path.expanduser("~")
        arqs = filedialog.askopenfilenames(title="Selecionar Template(s) (Imagem) — na mesma ordem dos vídeos", initialdir=dir_inicial, filetypes=[("Imagens", "*.png *.jpg *.jpeg")])
        if arqs:
            self.templates_carregados = [Path(a) for a in arqs]
            self.ultimo_template = arqs[0]
            self.salvar_config()
            self._remapear_templates()
            if len(self.templates_carregados) == 1:
                self.btn_template.configure(text=f"Template: {Path(arqs[0]).name}")
            else:
                self.btn_template.configure(text=f"Templates: {len(self.templates_carregados)} (1 por vídeo, na ordem)")
            self._atualizar_cor_play_btn()
            if self.videos_carregados:
                self.renderizar_grid()
            if self.video_preview_selecionado:
                self.gerar_preview_visual()

    def _remapear_templates(self):
        """Casa cada vídeo com seu template. Se apenas 1 template foi enviado, ele vale para
        todos os vídeos (modo clássico). Se vários foram enviados, casa por ordem: video[0]
        com template[0], video[1] com template[1], etc. — vídeos sem template correspondente
        ficam sem template (usam a cor de fundo)."""
        self.template_por_video = {}
        if len(self.templates_carregados) == 1:
            for v in self.videos_carregados:
                self.template_por_video[str(v)] = str(self.templates_carregados[0])
        else:
            for v, t in zip(self.videos_carregados, self.templates_carregados):
                self.template_por_video[str(v)] = str(t)
        self.template_path = str(self.templates_carregados[0]) if self.templates_carregados else ""

    def _template_para_video(self, video_path_str):
        """Retorna o template casado com este vídeo específico (usado para preview/thumb/player)."""
        return self.template_por_video.get(video_path_str, "")

    def _atualizar_cor_play_btn(self):
        if not self.template_path or not Path(self.template_path).exists():
            return
        try:
            img = Image.open(self.template_path).convert('L')
            stat = ImageStat.Stat(img)
            avg = stat.mean[0]
            if avg > 127:
                self.btn_play_preview.configure(fg_color="#1e1f22", text_color="white", hover_color="#2b2d31")
            else:
                self.btn_play_preview.configure(fg_color="white", text_color="black", hover_color="#ecf0f1")
        except: pass

    def selecionar_saida(self):
        dir_inicial = self.ultima_pasta_saida if self.ultima_pasta_saida else os.path.expanduser("~")
        pasta = filedialog.askdirectory(title="Pasta de Saída", initialdir=dir_inicial)
        if pasta:
            self.ultima_pasta_saida = pasta
            self.salvar_config()
            self.pasta_saida = pasta

    def ajustar_individual(self, video_path_str, eixo, valor):
        if video_path_str not in self.configs_individuais: return
        cfg = self.configs_individuais[video_path_str]
        
        if eixo == 'y': cfg['y'] += valor
        elif eixo == 'x': cfg['x'] += valor
        elif eixo == 'zoom':
            cfg['zoom'] += valor
            cfg['zoom'] = max(0.5, min(3.0, cfg['zoom']))
            cfg['zoom'] = round(cfg['zoom'], 1)
        elif eixo == 'stretch_x':
            cfg['stretch_x'] = cfg.get('stretch_x', 1.0) + valor
            cfg['stretch_x'] = max(0.5, min(3.0, cfg['stretch_x']))
            cfg['stretch_x'] = round(cfg['stretch_x'], 1)
            
        if video_path_str in self.labels_status_indiv:
            stx = cfg.get('stretch_x', 1.0)
            self.labels_status_indiv[video_path_str].configure(text=f"X:{cfg['x']} | Y:{cfg['y']} | Z:{cfg['zoom']}x | W:{stx}x")

        # Re-start player instantly if playing this video
        if self.player_ativo and str(self.video_preview_selecionado) == video_path_str:
            self.pausar_player()
            self.iniciar_player()
        elif hasattr(self, 'video_preview_selecionado') and str(self.video_preview_selecionado) == video_path_str:
            self.gerar_preview_visual()
            
        self._gerar_thumb_card(video_path_str)

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

    def _obter_dimensoes_video(self, video_path_str):
        """Retorna (largura, altura) reais do vídeo usando ffprobe."""
        cmd = ["ffprobe", "-v", "error", "-select_streams", "v:0",
               "-show_entries", "stream=width,height", "-of", "csv=p=0", video_path_str]
        try:
            result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,
                                     creationflags=subprocess.CREATE_NO_WINDOW)
            w_str, h_str = result.stdout.strip().split(",")
            return int(w_str), int(h_str)
        except Exception:
            return None

    def abrir_selecao_corte(self, video_path):
        """Abre um diálogo para o usuário arrastar e escolher a área de corte (crop) do vídeo,
        com a opção de aplicar só a este vídeo ou a todos os vídeos carregados (edição em massa)."""
        v_str = str(video_path)
        dims = self._obter_dimensoes_video(v_str)
        if not dims:
            messagebox.showerror("Erro", "Não foi possível ler as dimensões do vídeo.")
            return
        real_w, real_h = dims

        # Extrai um frame para exibir no diálogo, em um tamanho de exibição confortável
        disp_w = 480
        disp_h = int(disp_w * real_h / real_w)
        frame_path = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / f"crop_sel_{Path(v_str).stem}.jpg"
        cmd = ["ffmpeg", "-y", "-ss", "00:00:01", "-i", v_str, "-vframes", "1", "-update", "1",
               "-s", f"{disp_w}x{disp_h}", "-q:v", "2", str(frame_path)]
        subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        if not frame_path.exists():
            messagebox.showerror("Erro", "Não foi possível gerar o frame para seleção de corte.")
            return

        dialog = ctk.CTkToplevel(self)
        dialog.title(f"✂ Selecionar área de corte — {Path(v_str).name}")
        dialog.geometry(f"{disp_w + 40}x{disp_h + 150}")
        dialog.configure(fg_color="#2b2d31")
        dialog.grab_set()
        dialog.resizable(False, False)

        ctk.CTkLabel(dialog, text="Arraste no vídeo abaixo para marcar a área de corte:",
                     font=ctk.CTkFont(size=12)).pack(pady=(12, 6))

        canvas = ctk.CTkCanvas(dialog, bg="#000000", highlightthickness=0, width=disp_w, height=disp_h)
        canvas.pack(padx=10)

        frame_photo = ImageTk.PhotoImage(Image.open(frame_path))
        canvas.create_image(0, 0, anchor="nw", image=frame_photo)
        dialog._frame_photo_ref = frame_photo  # evita coleta de lixo da imagem

        sel = {"x0": None, "y0": None, "x1": None, "y1": None, "rect": None}

        def on_press(event):
            sel["x0"], sel["y0"] = event.x, event.y
            if sel["rect"]:
                canvas.delete(sel["rect"])
            sel["rect"] = canvas.create_rectangle(event.x, event.y, event.x, event.y,
                                                   outline="#2ecc71", width=2)

        def on_drag(event):
            if sel["rect"] is None:
                return
            x1 = max(0, min(disp_w, event.x))
            y1 = max(0, min(disp_h, event.y))
            sel["x1"], sel["y1"] = x1, y1
            canvas.coords(sel["rect"], sel["x0"], sel["y0"], x1, y1)

        canvas.bind("<ButtonPress-1>", on_press)
        canvas.bind("<B1-Motion>", on_drag)

        f_btns = ctk.CTkFrame(dialog, fg_color="transparent")
        f_btns.pack(fill="x", padx=15, pady=(10, 15))

        def _crop_string_da_selecao():
            if None in (sel["x0"], sel["y0"], sel["x1"], sel["y1"]):
                messagebox.showwarning("Aviso", "Arraste no vídeo para marcar a área de corte primeiro.", parent=dialog)
                return None
            x0, x1 = sorted((sel["x0"], sel["x1"]))
            y0, y1 = sorted((sel["y0"], sel["y1"]))
            if x1 - x0 < 5 or y1 - y0 < 5:
                messagebox.showwarning("Aviso", "A área selecionada é pequena demais.", parent=dialog)
                return None
            escala_x = real_w / disp_w
            escala_y = real_h / disp_h
            rw = int((x1 - x0) * escala_x)
            rh = int((y1 - y0) * escala_y)
            rx = int(x0 * escala_x)
            ry = int(y0 * escala_y)
            # ffmpeg exige dimensões pares
            rw -= rw % 2
            rh -= rh % 2
            return f"{rw}:{rh}:{rx}:{ry}"

        def aplicar(somente_este):
            crop_str = _crop_string_da_selecao()
            if not crop_str:
                return
            alvos = [video_path] if somente_este else list(self.videos_carregados)
            for v in alvos:
                vs = str(v)
                cfg = self.configs_individuais.setdefault(vs, {'y': 682, 'x': 0, 'zoom': 1.0, 'crop': None})
                cfg['crop'] = crop_str
                self._gerar_thumb_card(vs, force_regenerate=True)
            if self.video_preview_selecionado and str(self.video_preview_selecionado) in [str(v) for v in alvos]:
                self.gerar_preview_visual()
            self.salvar_config()
            dialog.destroy()
            msg = "Corte aplicado a este vídeo!" if somente_este else f"Corte aplicado a {len(alvos)} vídeo(s)!"
            messagebox.showinfo("Sucesso", msg)

        ctk.CTkButton(f_btns, text="✅ Somente este vídeo", fg_color="#3498db", hover_color="#2980b9",
                      command=lambda: aplicar(True)).pack(side="left", fill="x", expand=True, padx=(0, 5))
        ctk.CTkButton(f_btns, text="🌐 Aplicar a todos os vídeos", fg_color="#e67e22", hover_color="#d35400",
                      command=lambda: aplicar(False)).pack(side="left", fill="x", expand=True, padx=(5, 5))
        ctk.CTkButton(f_btns, text="❌ Cancelar", fg_color="#e74c3c", hover_color="#c0392b",
                      command=dialog.destroy).pack(side="left", fill="x", expand=True, padx=(5, 0))

    def _gerar_thumb_card(self, video_path_str, force_regenerate=False):
        video_path = Path(video_path_str)
        if not video_path.exists() or video_path_str not in self.configs_individuais: return
        
        cfg = self.configs_individuais[video_path_str]
        configs = self.obter_configs_atuais()
        thumb_path = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / f"thumb_{video_path.stem}_edit.jpg"
        
        # Se não forçar regeneração e a miniatura já existir, apenas carrega do disco instantaneamente
        if not force_regenerate and thumb_path.exists() and video_path_str in self.labels_thumb_indiv:
            try:
                img_pil = Image.open(thumb_path)
                ctk_img = ctk.CTkImage(light_image=img_pil, size=(THUMB_W, THUMB_H))
                self.labels_thumb_indiv[video_path_str].configure(image=ctk_img, text="")
                return
            except: pass

        template_video = self._template_para_video(video_path_str)
        out_w, out_h = get_res_dimensions(configs['resolucao'])
        filtros_str, last_out = build_filter_complex(video_path_str, template_video, configs, cfg, out_w, out_h)

        cmd_thumb = ["ffmpeg", "-y", "-ss", "00:00:01", "-i", video_path_str]
        if template_video and Path(template_video).exists():
            cmd_thumb.extend(["-i", str(template_video)])
            
        cmd_thumb.extend(["-filter_complex", filtros_str, "-map", last_out, "-vframes", "1", "-update", "1", "-s", f"{THUMB_W}x{THUMB_H}", "-q:v", "5", str(thumb_path)])
        subprocess.run(cmd_thumb, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        
        if thumb_path.exists() and video_path_str in self.labels_thumb_indiv:
            try:
                img_pil = Image.open(thumb_path)
                ctk_img = ctk.CTkImage(light_image=img_pil, size=(THUMB_W, THUMB_H))
                self.labels_thumb_indiv[video_path_str].configure(image=ctk_img, text="")
            except: pass

    def remover_video(self, video_path):
        import tkinter.messagebox as mb
        if not mb.askyesno("Confirmar", f"Deseja remover o vídeo {video_path.name}?"):
            return
            
        if video_path in self.videos_carregados:
            self.videos_carregados.remove(video_path)
            
        v_str = str(video_path)
        if v_str in self.configs_individuais:
            del self.configs_individuais[v_str]
        if v_str in self.template_por_video:
            del self.template_por_video[v_str]

        self.lbl_contador_esq.configure(text=f"📥 {len(self.videos_carregados)} vídeo(s) adicionados")
        self.salvar_config()
        self.atualizar_abas()
        self.renderizar_grid()

    def renderizar_grid(self):
        for widget in self.grid_frame.winfo_children(): widget.destroy()
        self.labels_status_indiv.clear()
        
        if not hasattr(self, 'labels_thumb_indiv'):
            self.labels_thumb_indiv = {}
        self.labels_thumb_indiv.clear()
        
        # Garante distribuição igual das colunas no grid
        for col in range(GRID_COLS):
            self.grid_frame.grid_columnconfigure(col, weight=1)

        start_idx = self.active_tab_index * 50
        end_idx = start_idx + 50
        videos_aba = self.videos_carregados[start_idx:end_idx]

        for i, video in enumerate(videos_aba):
            self.lbl_contador_esq.configure(text=f"Gerando thumb {i+1}/{len(videos_aba)}...")
            self.update()
            row, col = i // GRID_COLS, i % GRID_COLS
            v_str = str(video)

            card = ctk.CTkFrame(self.grid_frame, fg_color="#2b2d31", border_width=2, border_color="#1e1f22", cursor="hand2")

            header_card = ctk.CTkFrame(card, fg_color="transparent")
            header_card.pack(fill="x", padx=2, pady=(2, 0))

            btn_crop = ctk.CTkButton(header_card, text="✂", width=10, height=14, fg_color="#f39c12", hover_color="#d68910",
                                      font=ctk.CTkFont(size=8, weight="bold"),
                                      command=lambda v=video: self.abrir_selecao_corte(v))
            btn_crop.pack(side="left", padx=1)

            lbl_title = ctk.CTkLabel(header_card, text=video.name[:6], font=ctk.CTkFont(size=8))
            lbl_title.pack(side="left", padx=1)

            btn_remove = ctk.CTkButton(header_card, text="✕", width=10, height=14, fg_color="#e74c3c", hover_color="#c0392b", font=ctk.CTkFont(size=8, weight="bold"), command=lambda v=video: self.remover_video(v))
            btn_remove.pack(side="right", padx=1)

            f_thumb = ctk.CTkFrame(card, width=THUMB_W, height=THUMB_H, fg_color="#1e1f22")
            f_thumb.pack(padx=3, pady=3)
            f_thumb.pack_propagate(False)

            lbl_thumb = ctk.CTkLabel(f_thumb, text="🎥\nCarregando...", text_color="gray")
            lbl_thumb.place(relx=0.5, rely=0.5, anchor="center")
            self.labels_thumb_indiv[v_str] = lbl_thumb

            self._gerar_thumb_card(v_str)

            # --- Controles Individuais ---
            # Zoom/esticar em grade 2x2 (em vez de 4 botões numa fileira só) para o card
            # ficar mais estreito e caber mais miniaturas lado a lado.
            f_controls_zoom = ctk.CTkFrame(card, fg_color="transparent")
            f_controls_zoom.pack(pady=1)
            mini_btn = {"width": 20, "height": 15, "font": ctk.CTkFont(size=8)}

            btn_z_in = ctk.CTkButton(f_controls_zoom, text="Z+", fg_color="#3498db", hover_color="#2980b9", **mini_btn,
                                     command=lambda v=v_str: self.ajustar_individual(v, 'zoom', 0.1))
            btn_z_in.grid(row=0, column=0, padx=1, pady=1)
            btn_z_out = ctk.CTkButton(f_controls_zoom, text="Z-", fg_color="#e74c3c", hover_color="#c0392b", **mini_btn,
                                      command=lambda v=v_str: self.ajustar_individual(v, 'zoom', -0.1))
            btn_z_out.grid(row=0, column=1, padx=1, pady=1)
            btn_sx_in = ctk.CTkButton(f_controls_zoom, text="W+", fg_color="#2ecc71", hover_color="#27ae60", **mini_btn,
                                     command=lambda v=v_str: self.ajustar_individual(v, 'stretch_x', 0.1))
            btn_sx_in.grid(row=1, column=0, padx=1, pady=1)
            btn_sx_out = ctk.CTkButton(f_controls_zoom, text="W-", fg_color="#e67e22", hover_color="#d35400", **mini_btn,
                                     command=lambda v=v_str: self.ajustar_individual(v, 'stretch_x', -0.1))
            btn_sx_out.grid(row=1, column=1, padx=1, pady=1)

            # Posição X/Y em cruz (D-pad), igual ao padrão da aba Marca — 3 colunas de
            # largura em vez de 4, também para economizar largura do card.
            f_controls_pos = ctk.CTkFrame(card, fg_color="transparent")
            f_controls_pos.pack(pady=(0, 2))
            dpad_btn = {"width": 20, "height": 15, "font": ctk.CTkFont(size=8)}

            btn_up = ctk.CTkButton(f_controls_pos, text="⬆", fg_color="#f39c12", hover_color="#d68910", **dpad_btn,
                                    command=lambda v=v_str: self.ajustar_individual(v, 'y', -20))
            btn_up.grid(row=0, column=1, padx=1, pady=1)
            btn_left = ctk.CTkButton(f_controls_pos, text="⬅", fg_color="#8e44ad", hover_color="#732d91", **dpad_btn,
                                      command=lambda v=v_str: self.ajustar_individual(v, 'x', -20))
            btn_left.grid(row=1, column=0, padx=1, pady=1)
            btn_right = ctk.CTkButton(f_controls_pos, text="➡", fg_color="#8e44ad", hover_color="#732d91", **dpad_btn,
                                       command=lambda v=v_str: self.ajustar_individual(v, 'x', 20))
            btn_right.grid(row=1, column=2, padx=1, pady=1)
            btn_dw = ctk.CTkButton(f_controls_pos, text="⬇", fg_color="#f39c12", hover_color="#d68910", **dpad_btn,
                                    command=lambda v=v_str: self.ajustar_individual(v, 'y', 20))
            btn_dw.grid(row=2, column=1, padx=1, pady=1)

            cfg = self.configs_individuais.get(v_str, {'y': 682, 'x': 0, 'zoom': 1.0, 'stretch_x': 1.0})
            stx = cfg.get('stretch_x', 1.0)
            lbl_status = ctk.CTkLabel(card, text=f"Z{cfg['zoom']} W{stx}", font=ctk.CTkFont(size=8, weight="bold"))
            lbl_status.pack(pady=1)
            self.labels_status_indiv[v_str] = lbl_status
            
            card.grid(row=row, column=col, padx=2, pady=2)
            
            def on_click(event, v=video, c=card):
                self.selecionar_video_para_preview(v, c)
                
            card.bind("<Button-1>", on_click)
            f_thumb.bind("<Button-1>", on_click)
            lbl_thumb.bind("<Button-1>", on_click)
            lbl_title.bind("<Button-1>", on_click)
            lbl_status.bind("<Button-1>", on_click)
            
        self.lbl_contador_esq.configure(text=f"📥 {len(self.videos_carregados)} vídeo(s) adicionados")

    def selecionar_video_para_preview(self, video_path, card_widget):
        self.video_preview_selecionado = video_path
        try: self.focus_set()
        except: pass
        for widget in self.grid_frame.winfo_children():
            widget.configure(border_color="#1e1f22")
            
        card_widget.configure(border_color="#2ecc71")
        self.preview_canvas.delete("all")
        cx, cy = self._centro_preview()
        self.preview_canvas.create_text(cx, cy, text="Carregando...", fill="#5f6368", justify="center", font=("Segoe UI", 9), tags=("placeholder",))
        self.lbl_status.configure(text="Pronto para Preview")
        self.gerar_preview_visual()

    def deletar_video_selecionado(self, event=None):
        foc = self.focus_get()
        if foc:
            class_name = foc.__class__.__name__.lower()
            if "entry" in class_name or "text" in class_name or "combobox" in class_name:
                return
                
        if not self.video_preview_selecionado:
            return
            
        v_sel = self.video_preview_selecionado
        v_str = str(v_sel)
        
        if self.player_ativo:
            self.pausar_player()
            
        if v_sel in self.videos_carregados:
            self.videos_carregados.remove(v_sel)
            
        if v_str in self.configs_individuais:
            del self.configs_individuais[v_str]
        if v_str in self.labels_status_indiv:
            del self.labels_status_indiv[v_str]
        if v_str in self.labels_thumb_indiv:
            del self.labels_thumb_indiv[v_str]
            
        self.video_preview_selecionado = None
        self.preview_canvas.delete("all")
        cx, cy = self._centro_preview()
        self.preview_canvas.create_text(cx, cy, text="Selecione um vídeo\npara ver o preview", fill="#5f6368", justify="center", font=("Segoe UI", 9), tags=("placeholder",))
        self.atualizar_abas()
        self.renderizar_grid()

    def atualizar_abas(self):
        # Limpa os botões anteriores na barra de abas
        if not hasattr(self, 'f_tb') or not self.f_tb:
            return
        for widget in self.f_tb.winfo_children():
            widget.destroy()
            
        num_videos = len(self.videos_carregados)
        num_tabs = max(1, (num_videos + 49) // 50)
        
        # Garante que a aba ativa está nos limites
        if self.active_tab_index >= num_tabs:
            self.active_tab_index = 0
            
        for i in range(num_tabs):
            tab_name = f"Aba {i+1}"
            is_active = (i == self.active_tab_index)
            color = "#2ecc71" if is_active else "#383a40"
            text_color = "black" if is_active else "white"
            hover_color = "#27ae60" if is_active else "#474a51"
            
            btn = ctk.CTkButton(
                self.f_tb, 
                text=tab_name, 
                fg_color=color, 
                text_color=text_color, 
                hover_color=hover_color,
                width=80, 
                height=25,
                command=lambda idx=i: self.mudar_aba(idx)
            )
            btn.pack(side="left", padx=5)

    def mudar_aba(self, idx):
        self.active_tab_index = idx
        self.atualizar_abas()
        self.renderizar_grid()

    # ==========================
    # PLAYER DE VÍDEO FFPLAY-LIKE
    # ==========================
    def toggle_player(self):
        if not self.video_preview_selecionado: return
        if self.player_ativo:
            self.pausar_player()
        else:
            self.iniciar_player()
            
    def pausar_player(self):
        self.player_ativo = False
        if self.ffmpeg_process_player:
            try: self.ffmpeg_process_player.kill()
            except: pass
        if getattr(self, 'ffplay_audio_process', None):
            try: self.ffplay_audio_process.kill()
            except: pass
            self.ffplay_audio_process = None
        self.btn_play_preview.configure(text="▶")
        self.gerar_preview_visual() # Restaura o frame estático em alta resolução

    def iniciar_player(self):
        self.player_ativo = True
        self.btn_play_preview.configure(text="⏸")
        self._iniciar_audio_player()
        t = threading.Thread(target=self._loop_player)
        t.daemon = True
        t.start()

    def _iniciar_audio_player(self):
        """Toca o áudio original do vídeo em paralelo à reprodução de frames no canvas
        (o canvas mostra só a imagem, sem som embutido, então tocamos o áudio à parte)."""
        video_path_str = str(self.video_preview_selecionado)
        cmd = ["ffplay", "-nodisp", "-autoexit", "-loglevel", "quiet", "-vn", video_path_str]
        try:
            self.ffplay_audio_process = subprocess.Popen(cmd, creationflags=subprocess.CREATE_NO_WINDOW)
        except Exception:
            self.ffplay_audio_process = None
        
    def _loop_player(self):
        video_path_str = str(self.video_preview_selecionado)
        configs = self.obter_configs_atuais()
        cfg = self.configs_individuais.get(video_path_str)
        template_video = self._template_para_video(video_path_str)
        out_w, out_h = get_res_dimensions(configs['resolucao'])
        filtros_str, last_out = build_filter_complex(video_path_str, template_video, configs, cfg, out_w, out_h)

        w, h = getattr(self, 'preview_display_size', (234, 416))

        cmd = ["ffmpeg", "-y", "-re", "-i", video_path_str]
        if template_video and Path(template_video).exists():
            cmd.extend(["-i", str(template_video)])
            
        cmd.extend([
            "-filter_complex", filtros_str,
            "-map", last_out,
            "-s", f"{w}x{h}", # Reduz para caber no UI rápido mantendo a proporção exata
            "-f", "image2pipe",
            "-pix_fmt", "rgb24",
            "-vcodec", "rawvideo",
            "-"
        ])
        
        self.ffmpeg_process_player = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, creationflags=subprocess.CREATE_NO_WINDOW)
        chunk_size = w * h * 3
        
        while self.player_ativo:
            raw = self.ffmpeg_process_player.stdout.read(chunk_size)
            if len(raw) < chunk_size:
                break
            self.after(0, self._atualizar_frame_player, raw)
            
        self.after(0, self.pausar_player)
            
    def _atualizar_frame_player(self, raw_bytes):
        if not self.player_ativo: return
        w, h = getattr(self, 'preview_display_size', (234, 416))
        img = Image.frombytes("RGB", (w, h), raw_bytes)
        # Durante a reprodução, a marca d'água já vem queimada no vídeo pelo ffmpeg,
        # então some com a camada arrastável para não desenhar o texto duas vezes.
        self.preview_canvas.delete("wm")
        self._preview_base_photo = ImageTk.PhotoImage(img)
        self.preview_canvas.delete("base")
        cx, cy = self._centro_preview()
        self.preview_canvas.create_image(cx, cy, anchor="center", image=self._preview_base_photo, tags=("base",))

    def _centro_preview(self):
        w, h = getattr(self, 'preview_display_size', (234, 416))
        return w // 2, h // 2

    def _ajustar_tamanho_preview_canvas(self, event=None):
        """Recalcula o tamanho do canvas de preview para aproveitar ao máximo o espaço do
        container (sem a moldura/padding antigos que deixavam faixas cinzas ao redor),
        mantendo a proporção 9:16 do vídeo."""
        cont_w = self.f_image_container.winfo_width()
        cont_h = self.f_image_container.winfo_height()
        reservado_h = 90  # botão de play + seletor de proporção logo abaixo do canvas
        avail_w = max(50, cont_w - 8)
        avail_h = max(50, cont_h - reservado_h)

        target_w = avail_w
        target_h = int(target_w * 1920 / 1080)
        if target_h > avail_h:
            target_h = avail_h
            target_w = int(target_h * 1080 / 1920)
        target_w -= target_w % 2
        target_h -= target_h % 2
        if target_w < 20 or target_h < 20:
            return

        if getattr(self, '_preview_canvas_wh', None) == (target_w, target_h):
            return
        self._preview_canvas_wh = (target_w, target_h)
        self.preview_canvas.configure(width=target_w, height=target_h)
        self.preview_display_size = (target_w, target_h)

        cx, cy = target_w // 2, target_h // 2
        for item in self.preview_canvas.find_withtag("placeholder"):
            self.preview_canvas.coords(item, cx, cy)

        if self.video_preview_selecionado and not self.player_ativo:
            self.gerar_preview_visual()

    def gerar_preview_visual(self):
        if not self.video_preview_selecionado: return
        if self.player_ativo: return # Deixa o player atualizar a tela
        try:
            self.lbl_status.configure(text="Gerando preview individual...")
            self.update()

            # Renderiza só a base (vídeo + template), sem queimar a marca d'água:
            # ela é desenhada em cima no canvas, arrastável, por atualizar_marca_dagua_preview().
            configs = dict(self.obter_configs_atuais())
            configs['wm_text'] = ''
            video_config = self.configs_individuais.get(str(self.video_preview_selecionado))
            temp_img = Path(os.environ.get("TEMP", "C:/Windows/Temp")) / f"preview_temp_editor_{self.video_preview_selecionado.stem}.jpg"
            if temp_img.exists(): temp_img.unlink(missing_ok=True)

            self.motor._executar_ffmpeg(
                self.video_preview_selecionado,
                self._template_para_video(str(self.video_preview_selecionado)),
                temp_img,
                configs,
                video_config,
                extra_args=["-ss", "00:00:01", "-vframes", "1", "-q:v", "2"]
            )

            if temp_img.exists():
                max_w = int(self.preview_canvas.cget("width"))
                max_h = int(self.preview_canvas.cget("height"))
                with Image.open(temp_img) as img_pil:
                    img_copy = img_pil.copy()
                img_copy.thumbnail((max_w, max_h))
                w, h = img_copy.size
                w = w if w % 2 == 0 else w - 1
                h = h if h % 2 == 0 else h - 1
                self.preview_display_size = (w, h)

                self._preview_base_photo = ImageTk.PhotoImage(img_copy)
                self.preview_canvas.delete("all")
                cx, cy = self._centro_preview()
                self.preview_canvas.create_image(cx, cy, anchor="center", image=self._preview_base_photo, tags=("base",))
                self.atualizar_marca_dagua_preview()
                self.lbl_status.configure(text="Preview atualizado! (arraste o texto no preview)")
                self.update_idletasks()
            else:
                self.lbl_status.configure(text="Erro no preview (FFmpeg falhou)")
        except Exception as e:
            self.lbl_status.configure(text="Erro no preview: " + str(e))

    def _resolver_fonte_wm(self, fonte_nome):
        fontes_map = {
            "Arial": "arial.ttf",
            "Impact": "impact.ttf",
            "Verdana": "verdana.ttf",
            "Tahoma": "tahoma.ttf",
            "Courier New": "cour.ttf",
            "Comic Sans MS": "comic.ttf",
            "Times New Roman": "times.ttf",
            "Montserrat": "Montserrat-Regular.ttf",
        }
        return fontes_map.get(fonte_nome, "arial.ttf")

    def atualizar_marca_dagua_preview(self, *args):
        """Redesenha só a camada de texto da marca d'água sobre a base já renderizada
        (sem re-rodar o ffmpeg) — usada por todo controle da aba Marca e pelo arrastar no canvas."""
        if not hasattr(self, '_preview_base_photo') or not hasattr(self, 'preview_canvas'):
            return
        self.preview_canvas.delete("wm")
        texto = self.var_wm_text.get() if hasattr(self, 'var_wm_text') else ""
        if not texto:
            return

        w, h = getattr(self, 'preview_display_size', (234, 416))
        # Fator ÚNICO baseado só na largura — precisa ser exatamente a mesma conta que
        # build_filter_complex usa no drawtext (scale_factor = out_w / 1080.0) para X, Y e
        # fonte. Usar w/1080 e h/1920 separadamente diverge do export quando o canvas
        # final não é exatamente 1080x1920 (ex: vídeo sem template correspondente), fazendo
        # o texto "pular" de onde foi solto.
        scale_factor = w / 1080.0

        cor = self.cb_cor_wm.get()
        tam = int(self.slider_tam.get())
        opac = int(self.slider_opac.get()) / 100.0
        x = int(self.slider_x.get())
        y = int(self.slider_y.get())

        x_scaled = int(x * scale_factor)
        y_scaled = int(y * scale_factor)
        size_scaled = max(6, int(tam * scale_factor))

        fonte_arquivo = self._resolver_fonte_wm(self.cb_fonte_wm.get())
        try:
            font = ImageFont.truetype(fonte_arquivo, size_scaled)
        except Exception:
            try:
                font = ImageFont.truetype("arial.ttf", size_scaled)
            except Exception:
                font = ImageFont.load_default()

        dummy = Image.new("RGBA", (1, 1), (0, 0, 0, 0))
        bbox = ImageDraw.Draw(dummy).textbbox((0, 0), texto, font=font)
        tw = max(1, bbox[2] - bbox[0])
        th = max(1, bbox[3] - bbox[1])
        pad = 6
        img = Image.new("RGBA", (tw + pad * 2, th + pad * 2), (0, 0, 0, 0))
        alpha = max(0, min(255, int(opac * 255)))
        with Pilmoji(img) as pilmoji:
            pilmoji.text((pad - bbox[0], pad - bbox[1]), texto, fill=(*ImageColor.getrgb(cor), alpha), font=font)

        self._wm_photo = ImageTk.PhotoImage(img)
        self._wm_bbox_offset = (pad - bbox[0], pad - bbox[1])
        # x_scaled/y_scaled representam o canto onde o ffmpeg desenha o texto (drawtext usa x,y = topo-esquerda)
        canvas_x = x_scaled - pad
        canvas_y = y_scaled - pad
        self.preview_canvas.create_image(canvas_x, canvas_y, anchor="nw", image=self._wm_photo, tags=("wm",))

    def on_wm_press(self, event):
        self._wm_drag_start = (event.x, event.y)

    def on_wm_drag(self, event):
        if not hasattr(self, '_wm_drag_start'):
            return
        dx = event.x - self._wm_drag_start[0]
        dy = event.y - self._wm_drag_start[1]
        self.preview_canvas.move("wm", dx, dy)
        self._wm_drag_start = (event.x, event.y)

    def on_wm_release(self, event):
        if not hasattr(self, '_wm_drag_start'):
            return
        del self._wm_drag_start
        items = self.preview_canvas.find_withtag("wm")
        if not items:
            return
        canvas_x, canvas_y = self.preview_canvas.coords(items[0])
        w, h = getattr(self, 'preview_display_size', (234, 416))
        # Mesmo fator único (baseado na largura) usado em atualizar_marca_dagua_preview,
        # invertido — mantém preview e export sempre em sincronia.
        scale_inv = 1080.0 / w
        pad = 6
        real_x = int((canvas_x + pad) * scale_inv)
        real_y = int((canvas_y + pad) * scale_inv)
        real_x = max(0, min(1080, real_x))
        real_y = max(0, min(1920, real_y))
        self.slider_x.set(real_x)
        self.slider_y.set(real_y)
        self.atualizar_marca_dagua_preview()
        self.salvar_config()

    def obter_configs_atuais(self):
        try: pixels = int(self.entry_pixels.get())
        except: pixels = 0
        return {
            'pixels_y': pixels,
            'cor_fundo_video': 'Nenhum (Normal)',
            'resolucao': '1080p',
            'esticar': False,
            'audio_melhorado': False,
            'anti_dup': True,
            'auto_crop': True,
            'aspect_video': self.var_aspect_video.get(),
            'wm_text': self.entry_wm_text.get(),
            'wm_cor': self.cb_cor_wm.get(),
            'wm_fonte': self.cb_fonte_wm.get(),
            'wm_tamanho': int(self.slider_tam.get()),
            'wm_x': int(self.slider_x.get()),
            'wm_y': int(self.slider_y.get()),
            'wm_opacidade': int(self.slider_opac.get())
        }
        
    def iniciar_processamento(self):
        if not self.videos_carregados:
            messagebox.showwarning("Aviso", "Envie vídeos primeiro.")
            return
        if not self.pasta_saida:
            messagebox.showwarning("Aviso", "Selecione a pasta de saída (Abrir Saída).")
            return
        self.btn_processar.configure(state="disabled")
        self.btn_exportar_preview.configure(state="disabled")
        self.motor.iniciar(self.videos_carregados, self.template_por_video, self.pasta_saida, self.obter_configs_atuais(), self.configs_individuais)
        
    def atualizar_progresso(self, msg, perc):
        self.lbl_status.configure(text=msg)
        self.barra_status.set(perc)
        
    def carregar_config(self):
        if os.path.exists(self.config_file):
            try:
                import json
                with open(self.config_file, "r", encoding="utf-8") as f:
                    dados = json.load(f)
                    self.ultima_pasta_entrada = dados.get("ultima_pasta_entrada", "")
                    self.ultima_pasta_saida = dados.get("ultima_pasta_saida", "")
                    self.ultimo_template = dados.get("ultimo_template", "")
            except Exception:
                pass

    def salvar_config(self):
        try:
            import json
            dados = {
                "ultima_pasta_entrada": getattr(self, "pasta_entrada", getattr(self, "ultima_pasta_entrada", "")),
                "ultima_pasta_saida": getattr(self, "pasta_saida", getattr(self, "ultima_pasta_saida", "")),
                "ultimo_template": getattr(self, "template_path", getattr(self, "ultimo_template", ""))
            }
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(dados, f, ensure_ascii=False, indent=4)
        except Exception:
            pass

    def finalizar_processamento(self, sucessos, total):
        self.btn_processar.configure(state="normal")
        self.btn_exportar_preview.configure(state="normal")
        messagebox.showinfo("Sucesso", f"Processados {sucessos} de {total} vídeos!")

if __name__ == "__main__":
    app = EditorAutomaDarkApp()
    app.mainloop()

