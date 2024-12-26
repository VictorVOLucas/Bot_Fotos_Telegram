import customtkinter as ctk
from tkinter import filedialog, messagebox
import os
import asyncio
import schedule
import time
import json
from telegram import Bot
from threading import Thread

# Caminho do arquivo de configuração JSON
CONFIG_FILE = "config.json"
ARQUIVO_ENVIADOS = "fotos_enviadas.txt"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("Envio Sequencial de Fotos - Telegram")
        self.geometry("800x500")

        # Variáveis
        self.diretorio_fotos = None
        self.fotos_restantes = []
        self.horarios = []

        # Carregar configurações do arquivo JSON
        self.config = self.carregar_configuracoes()

        # Personalizar o tema
        ctk.set_appearance_mode("dark")  # Inicializando o modo claro

        # Alterar o fundo da janela para uma cor personalizada ou transparente
        self.configure(bg="white")  # Altere "white" para a cor desejada ou "transparent" para transparência (no sistema que suportar).

        # Definir o comportamento de redimensionamento
        self.grid_rowconfigure(0, weight=0)  # Botões de navegação
        self.grid_rowconfigure(1, weight=1)  # Conteúdo das abas
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Componentes da interface
        self.aba_atual = "envio"  # Aba ativa inicial
        self.criar_interface()

        # Thread para execução do scheduler
        self.running = False
        self.thread = None

    def criar_interface(self):
        # Botões para navegação entre as abas
        self.botao_envio = ctk.CTkButton(self, text="Envio de Fotos", command=self.mudar_aba_envio, width=200, height=40)
        self.botao_envio.grid(row=0, column=0, padx=20, pady=10, sticky="ew")

        self.botao_configuracao = ctk.CTkButton(self, text="Configurações", command=self.mudar_aba_configuracao, width=200, height=40)
        self.botao_configuracao.grid(row=0, column=1, padx=20, pady=10, sticky="ew")

        # Switch para alterar o tema
        self.switch_appearance = ctk.CTkSwitch(self, text="Modo Escuro/Claro", command=self.alternar_tema)
        self.switch_appearance.grid(row=0, column=2, padx=20, pady=10, sticky="ew")

        # Frames para cada aba
        self.frame_envio = ctk.CTkFrame(self)
        self.frame_configuracao = ctk.CTkFrame(self)

        # Criar conteúdo da aba de envio
        self.criar_interface_envio()

        # Criar conteúdo da aba de configurações
        self.criar_interface_configuracao()

        # Exibir o frame da aba ativa
        self.exibir_aba()

    def criar_interface_envio(self):
        self.label = ctk.CTkLabel(self.frame_envio, text="Selecione um diretório de fotos:", font=("Arial", 14), anchor="w")
        self.label.grid(row=0, column=0, padx=20, pady=20, sticky="w")

        self.selecionar_btn = ctk.CTkButton(self.frame_envio, text="Selecionar Diretório", command=self.selecionar_diretorio, width=200, height=40)
        self.selecionar_btn.grid(row=1, column=0, padx=10, pady=10)

        self.horario_entry = ctk.CTkEntry(self.frame_envio, placeholder_text="Adicionar horário (HH:MM)", width=200, height=40)
        self.horario_entry.grid(row=3, column=2, padx=10, pady=10)

        self.add_horario_btn = ctk.CTkButton(self.frame_envio, text="Adicionar Horário", command=self.adicionar_horario, width=200, height=40)
        self.add_horario_btn.grid(row=3, column=0, padx=10, pady=10)

        self.horarios_label = ctk.CTkLabel(self.frame_envio, text="Horários programados: Nenhum", font=("Arial", 12), text_color="blue")
        self.horarios_label.grid(row=3, column=3, padx=10, pady=20)

        self.iniciar_btn = ctk.CTkButton(self.frame_envio, text="Iniciar Envio Programado", command=self.iniciar_envio, width=200, height=40, state="disabled")
        self.iniciar_btn.grid(row=5, column=0, padx=10, pady=10)

        self.status_label = ctk.CTkLabel(self.frame_envio, text="", font=("Arial", 12), text_color="green")
        self.status_label.grid(row=1, column=2, padx=10, pady=20)

    def criar_interface_configuracao(self):
        # Usando StringVar para vincular o texto dos campos de entrada
        self.token_var = ctk.StringVar(value=self.config["token"])
        self.chat_id_var = ctk.StringVar(value=self.config["chat_id"])

        self.token_label = ctk.CTkLabel(self.frame_configuracao, text="Token:", font=("Arial", 12))
        self.token_label.grid(row=0, column=0, padx=10, pady=10)
        self.token_entry = ctk.CTkEntry(self.frame_configuracao, placeholder_text="Digite o Token do Bot", textvariable=self.token_var, width=200, height=40)
        self.token_entry.grid(row=1, column=0, padx=10, pady=10)

        self.chat_id_label = ctk.CTkLabel(self.frame_configuracao, text="Chat ID:", font=("Arial", 12))
        self.chat_id_label.grid(row=2, column=0, padx=10, pady=10)
        self.chat_id_entry = ctk.CTkEntry(self.frame_configuracao, placeholder_text="Digite o Chat ID", textvariable=self.chat_id_var, width=200, height=40)
        self.chat_id_entry.grid(row=3, column=0, padx=10, pady=10)

        self.salvar_btn = ctk.CTkButton(self.frame_configuracao, text="Salvar Configurações", command=self.salvar_configuracoes, width=200, height=40)
        self.salvar_btn.grid(row=4, column=0, padx=10, pady=20)

    def alternar_tema(self):
        if self.switch_appearance.get():
            ctk.set_appearance_mode("light")  # Ativa o modo escuro
        else:
            ctk.set_appearance_mode("dark")  # Ativa o modo claro

    def mudar_aba_envio(self):
        self.aba_atual = "envio"
        self.exibir_aba()

    def mudar_aba_configuracao(self):
        self.aba_atual = "configuracao"
        self.exibir_aba()

    def exibir_aba(self):
        # Esconde todas as abas e exibe a aba ativa
        if self.aba_atual == "envio":
            self.frame_envio.grid(row=1, column=0, columnspan=3, sticky="nsew")
            self.frame_configuracao.grid_forget()
        elif self.aba_atual == "configuracao":
            self.frame_configuracao.grid(row=1, column=0, columnspan=3, sticky="nsew")
            self.frame_envio.grid_forget()

    def selecionar_diretorio(self):
        self.diretorio_fotos = filedialog.askdirectory()
        if self.diretorio_fotos:
            arquivos = os.listdir(self.diretorio_fotos)
            self.fotos_restantes = sorted(
                [os.path.join(self.diretorio_fotos, f) for f in arquivos if f.lower().endswith(('.png', '.jpg', '.jpeg'))]
            )
            if self.fotos_restantes:
                self.status_label.configure(text=f"Diretório válido: {len(self.fotos_restantes)} fotos encontradas.", text_color="blue")
                self.iniciar_btn.configure(state="normal")
            else:
                self.status_label.configure(text="Nenhuma foto encontrada no diretório selecionado.", text_color="red")
                self.iniciar_btn.configure(state="disabled")

    def adicionar_horario(self):
        horario = self.horario_entry.get().strip()
        if horario and self.validar_horario(horario):
            self.horarios.append(horario)
            self.horarios_label.configure(text=f"Horários programados: {', '.join(self.horarios)}")
            self.horario_entry.delete(0, 'end')
        else:
            self.status_label.configure(text="Horário inválido! Use o formato HH:MM.", text_color="red")

    def validar_horario(self, horario):
        try:
            time.strptime(horario, "%H:%M")
            return True
        except ValueError:
            return False

    def iniciar_envio(self):
        if self.diretorio_fotos and self.horarios:
            self.status_label.configure(text="Envio programado iniciado!", text_color="green")
            for horario in self.horarios:
                schedule.every().day.at(horario).do(lambda: asyncio.run(self.enviar_proxima_foto()))
            if not self.running:
                self.running = True
                self.thread = Thread(target=self.executar_scheduler, daemon=True)
                self.thread.start()

    def executar_scheduler(self):
        while self.running:
            schedule.run_pending()
            time.sleep(1)

    async def enviar_proxima_foto(self):
        # Certifica-se de carregar o histórico de fotos enviadas
        enviadas = self.carregar_fotos_enviadas()

        while self.fotos_restantes:
            foto = self.fotos_restantes.pop(0)
            if foto not in enviadas:
                try:
                    await self.enviar_foto(foto)
                    self.registrar_foto_enviada(foto)
                    self.status_label.configure(text=f"Foto enviada: {os.path.basename(foto)}", text_color="green")
                    return
                except Exception as e:
                    self.status_label.configure(text=f"Erro ao enviar a foto {os.path.basename(foto)}: {e}", text_color="red")
            else:
                print(f"Foto já enviada anteriormente: {os.path.basename(foto)}")

        self.status_label.configure(text="Todas as fotos já foram enviadas ou nenhuma nova encontrada.", text_color="green")

    async def enviar_foto(self, caminho_foto):
        try:
            bot = Bot(token=self.config["token"])
            with open(caminho_foto, 'rb') as foto:
                await bot.send_photo(chat_id=self.config["chat_id"], photo=foto)
            print(f"Foto enviada com sucesso: {caminho_foto}")
        except Exception as e:
            print(f"Erro ao enviar a foto {caminho_foto}: {e}")
            raise e

    def registrar_foto_enviada(self, foto):
        with open(ARQUIVO_ENVIADOS, 'a') as arquivo:
            arquivo.write(f"{foto}\n")

    def carregar_fotos_enviadas(self):
        if not os.path.exists(ARQUIVO_ENVIADOS):
            return set()
        with open(ARQUIVO_ENVIADOS, 'r') as arquivo:
            return set(linha.strip() for linha in arquivo)

    def carregar_configuracoes(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as arquivo:
                return json.load(arquivo)
        return {"token": "", "chat_id": ""}

    def salvar_configuracoes(self):
        self.config["token"] = self.token_var.get().strip()
        self.config["chat_id"] = self.chat_id_var.get().strip()

        # Salvar as configurações no arquivo JSON
        with open(CONFIG_FILE, 'w') as arquivo:
            json.dump(self.config, arquivo, indent=4)

        messagebox.showinfo("Configuração", "Configurações salvas com sucesso!")

if __name__ == "__main__":
    app = App()
    app.mainloop()
