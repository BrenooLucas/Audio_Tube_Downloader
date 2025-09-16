import os
import re
import threading
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import yt_dlp

# -----------------------------
# Configurações / Constantes
# -----------------------------
WIN_TITLE = "AudioTube Downloader"
WIN_SIZE = "600x350"
ICON_PATH = "player_.ico"  # arquivo .ico (se não existir, será ignorado)
WINDOW_RESIZABLE = (False, False)

# Cores e fontes usados na interface
BTN_COLOR_SELECT = "#4CAF50"
BTN_COLOR_SELECT_HOVER = "#5DD75D"
BTN_COLOR_DOWNLOAD = "#007BFF"
BTN_COLOR_DOWNLOAD_HOVER = "#0056b3"
FONT_LABEL = ("Arial", 12)
FONT_SMALL_ITALIC = ("Arial", 10, "italic")
FONT_BTN = ("Arial", 10)
FOOTER_TEXT = "© 2025-2030 | Desenvolvido por: Breno Lucas. Todos os direitos reservados."


class YouTubeDownloader:

    def __init__(self, root: tk.Tk):

        self.root = root
        self._configure_root()

        # Variáveis que controlam o estado da aplicação e armazenam entradas do usuário
        self.url_var = tk.StringVar()
        self.path_var = tk.StringVar()
        self.is_downloading = False

        # Barra de progresso temporária central (animação) enquanto a UI principal carrega
        self.loading_progress = ttk.Progressbar(
            self.root, orient="horizontal", length=200, mode="indeterminate"
        )
        self.loading_progress.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        self.loading_progress.start(10)

        # Agenda a criação dos widgets principais após pequena espera (mesma UX do original)
        self.root.after(1200, self.load_main_ui)

    # -----------------------------
    # Configuração da janela
    # -----------------------------
    def _configure_root(self):
        """Configuração básica da janela principal (título, tamanho, ícone, comportamento)."""
        self.root.title(WIN_TITLE)
        self.root.geometry(WIN_SIZE)
        self.root.resizable(*WINDOW_RESIZABLE)
        # Tenta definir ícone, mas ignora caso falhe (Windows X11 cross-platform safe)
        try:
            if os.path.exists(ICON_PATH):
                self.root.iconbitmap(ICON_PATH)
        except Exception:
            # Falha ao setar o ícone não é crítica — manter a execução
            pass

    # -----------------------------
    # Carregamento da UI
    # -----------------------------
    def load_main_ui(self):
        """
        Remove a barra de carregamento inicial e cria os widgets principais.
        Chamado após o delay definido no construtor para reproduzir a animação original.
        """
        self.loading_progress.stop()
        self.loading_progress.destroy()
        self.create_widgets()

    # -----------------------------
    # Construção da interface
    # -----------------------------
    def create_widgets(self):
        """Cria todos os widgets visuais e organiza o layout da aplicação."""
        # Label e campo de URL
        ttk.Label(self.root, text="🔗 Cole o link do YouTube:", font=FONT_LABEL).pack(pady=10)
        self.url_entry = ttk.Entry(self.root, textvariable=self.url_var, width=70)
        self.url_entry.pack(pady=5)

        # Label e área de seleção de diretório
        ttk.Label(self.root, text="💾 Escolha o diretório para salvar:", font=FONT_LABEL).pack(pady=10)
        path_frame = ttk.Frame(self.root)
        path_frame.pack()

        # Campo de caminho (readonly) e botão 'Selecionar'
        self.path_entry = ttk.Entry(path_frame, textvariable=self.path_var, width=50, state="readonly")
        self.path_entry.pack(side=tk.LEFT, padx=5)

        self.btn_select = tk.Button(
            path_frame,
            text="Selecionar",
            bg=BTN_COLOR_SELECT,
            fg="white",
            activebackground=BTN_COLOR_SELECT_HOVER,
            relief="flat",
            font=FONT_BTN,
            cursor="hand2",
            command=self.select_path,
        )
        self.btn_select.pack(side=tk.LEFT)

        # Eventos para hover (mesmo comportamento visual do original)
        self.btn_select.bind("<Enter>", lambda e: self.btn_select.config(bg=BTN_COLOR_SELECT_HOVER))
        self.btn_select.bind("<Leave>", lambda e: self.btn_select.config(bg=BTN_COLOR_SELECT))

        # Observação sobre qualidade do áudio
        ttk.Label(
            self.root,
            text="⚙️ O áudio será baixado na melhor qualidade disponível.",
            font=FONT_SMALL_ITALIC,
        ).pack(pady=15)

        # Botão de download e seus eventos de hover
        self.download_btn = tk.Button(
            self.root,
            text="Baixar Áudio",
            bg=BTN_COLOR_DOWNLOAD,
            fg="white",
            activebackground=BTN_COLOR_DOWNLOAD_HOVER,
            relief="flat",
            font=(FONT_BTN[0], FONT_BTN[1], "bold"),
            cursor="hand2",
            command=self.start_download,
        )
        self.download_btn.pack(pady=10)
        self.download_btn.bind("<Enter>", lambda e: self.download_btn.config(bg=BTN_COLOR_DOWNLOAD_HOVER))
        self.download_btn.bind("<Leave>", lambda e: self.download_btn.config(bg=BTN_COLOR_DOWNLOAD))

        # Label que mostra mensagens de espera/estado
        self.wait_label = ttk.Label(self.root, text="", font=FONT_SMALL_ITALIC, foreground="green")
        self.wait_label.pack()

        # Barra de progresso para o download (determine)
        self.progress = ttk.Progressbar(self.root, orient="horizontal", length=500, mode="determinate")
        self.progress.pack(pady=5)

        # Label que mostra a porcentagem atual de download
        self.progress_label = ttk.Label(self.root, text="0%")
        self.progress_label.pack()

        # Rodapé com direitos autorais
        footer_label = ttk.Label(self.root, text=FOOTER_TEXT, font=("Arial", 9))
        footer_label.pack(side=tk.BOTTOM, anchor=tk.W, pady=5, padx=5)

        # Clique em qualquer área para remover foco dos campos de entrada
        self.root.bind("<Button-1>", self.remove_focus_on_click)

    # -----------------------------
    # Eventos e utilitários da UI
    # -----------------------------
    def remove_focus_on_click(self, event):
        """
        Remove o foco dos campos de entrada caso o clique seja fora deles.
        """
        widget = event.widget
        if widget not in (self.url_entry, self.path_entry):
            try:
                self.url_entry.selection_clear()
                self.url_entry.icursor(0)
            except Exception:

                pass
            self.root.focus_set()

    def select_path(self):
        """
        Abre caixinha de seleção de diretório e armazena o caminho selecionado em path_var.
        Mantém o campo em estado de 'somente para leitura'.
        """
        path = filedialog.askdirectory()
        if path:  # Apenas atualiza se o usuário escolheu algo
            # Troca temporária para atualizar o conteúdo do Entry readonly
            self.path_entry.config(state="normal")
            self.path_var.set(path)
            self.path_entry.config(state="readonly")

    # -----------------------------
    # Validação de URL
    # -----------------------------
    def is_valid_youtube_url(self, url: str) -> bool:

        if not url or not isinstance(url, str):
            return False

        youtube_regex = re.compile(r'^(https?://)?(www\.)?(youtube\.com|youtu\.be)/.+$')
        if not youtube_regex.match(url):
            return False

        # Lógica idêntica ao original: valida watch?v= e youtu.be/<id>
        if "youtube.com/watch" in url:
            return "v=" in url
        if "youtu.be/" in url:
            path = url.split("youtu.be/")[-1]
            return len(path.strip()) > 0
        return False

    # -----------------------------
    # Início do processo de download
    # -----------------------------
    def start_download(self):
        """
        Valida entradas, evita downloads paralelos e dispara uma Thread para executar o download.
        """
        # Impede que o usuário inicie um novo download enquanto um estiver em andamento
        if self.is_downloading:
            return

        # Reset visual da barra/label de progresso
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.wait_label.config(text="")

        url = self.url_var.get().strip()
        save_path = self.path_var.get().strip()

        # Validações com mensagens idênticas às do original
        if not url:
            messagebox.showerror("Erro", "Por favor, insira um link do YouTube.")
            self.is_downloading = False
            return
        if not self.is_valid_youtube_url(url):
            messagebox.showerror("Erro", "Link inválido. Insira um link válido do YouTube.")
            self.is_downloading = False
            return
        if not save_path:
            messagebox.showerror("Erro", "Por favor, selecione um diretório para salvar o arquivo.")
            self.is_downloading = False
            return

        # Sinaliza que o download começou e atualiza a UI
        self.is_downloading = True
        self.wait_label.config(text="Aguarde...")

        # Cria thread de download (daemon para não travar encerramento da app)
        thread = threading.Thread(target=self.download, args=(url, save_path), daemon=True)
        thread.start()

    # -----------------------------
    # Download e hooks do yt_dlp
    # -----------------------------
    def download(self, url: str, save_path: str):
        """
        Executa o yt_dlp para baixar o melhor áudio disponível.
        Usa um progress_hook para atualizar a barra e, ao final, tenta renomear
        a extensão para .mp3 (como no código original).
        """
        ydl_opts = {
            # Preferências de formato idênticas ao original
            'format': 'bestaudio[abr>=320][ext=m4a]/bestaudio/best',
            'outtmpl': os.path.join(save_path, '%(title)s.%(ext)s'),
            'noplaylist': True,
            'quiet': True,
            'no_warnings': True,
            'progress_hooks': [self.hook],
        }

        try:
            # Extrai e baixa usando yt_dlp
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=True)

            # Recupera extensão e título retornados pelo yt_dlp
            original_ext = info.get("ext", "m4a")
            title = info.get("title", "audio")

            original_file = os.path.join(save_path, f"{title}.{original_ext}")
            target_file = os.path.join(save_path, f"{title}.mp3")

            # Tenta renomear para .mp3 apenas se o arquivo existir e não for já mp3.

            if original_ext.lower() != "mp3" and os.path.exists(original_file):
                try:
                    os.rename(original_file, target_file)
                except Exception as e:
                    # Mostra aviso parecido com o original em caso de falha no rename
                    self.root.after(
                        0,
                        lambda: messagebox.showwarning(
                            "Aviso",
                            f"Não foi possível renomear para .mp3 automaticamente.\n"
                            f"Arquivo salvo como {original_ext}.\nErro: {e}"
                        ),
                    )


            self.root.after(0, self.download_finished)

        except Exception as e:
            # Em caso de erro, apresenta mensagem e reseta progresso (mesma UX do original)
            self.root.after(0, lambda: messagebox.showerror("Erro", f"Ocorreu um erro durante o download:\n{str(e)}"))
            self.root.after(0, self.reset_progress)

    def hook(self, d: dict):
        """
        Hook de progresso do yt_dlp. Recebe d (dict) contendo status e bytes baixados.
        Atualiza a barra de progresso apenas durante o status 'downloading'.
        """
        try:
            if d.get('status') == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                downloaded = d.get('downloaded_bytes', 0)
                if total_bytes and total_bytes > 0:
                    percent = downloaded / total_bytes * 100
                    # Atualiza no loop principal da GUI
                    self.root.after(0, lambda: self.update_progress(percent))
        except Exception:
            # Segurança: qualquer problema no hook não deve interromper o download
            pass

    def update_progress(self, percent: float):
        """
        Atualiza os widgets de progresso (barra e label) com o valor fornecido.
        """
        # Limita percentuais para evitar valores estranhos na UI
        try:
            percent = max(0.0, min(float(percent), 100.0))
        except Exception:
            percent = 0.0

        self.progress['value'] = percent
        self.progress_label.config(text=f"{percent:.1f}%")
        # Garante que a UI seja redesenhada imediatamente
        self.root.update_idletasks()

    # -----------------------------
    # Fim do download e reset de estado
    # -----------------------------
    def download_finished(self):
        """Executa a finalização visual do download (limpa campos e alerta o usuário)."""
        self.wait_label.config(text="")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.url_var.set("")
        self.path_var.set("")
        self.is_downloading = False
        messagebox.showinfo("Concluído", "Download do áudio finalizado com sucesso!")

    def reset_progress(self):
        """Reseta a barra de progresso e o estado da aplicação (usado em casos de erro)."""
        self.wait_label.config(text="")
        self.progress['value'] = 0
        self.progress_label.config(text="0%")
        self.is_downloading = False


# -----------------------------
# Ponto de entrada da aplicação
# -----------------------------
def main():
    """Cria a janela principal e inicia o loop do Tkinter."""
    root = tk.Tk()
    app = YouTubeDownloader(root)
    root.mainloop()
if __name__ == "__main__":
    main()