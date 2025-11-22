import tkinter as tk
from tkinter import ttk, messagebox, scrolledtext
import psycopg2
from psycopg2 import sql
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import pandas as pd
import datetime


class ConflictosBelicosApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Sistema de Gerenciamento de Conflitos Bélicos")
        self.root.geometry("1200x800")

        # Configuração da conexão com banco padrão
        self.db_config = {
            'host': 'localhost',
            'database': 'conflitos',
            'user': 'postgres',
            'password': '123'
        }
        self.conn = None
        self.setup_gui()
        # self.test_connection()  # Conectar ao iniciar

    def connect_db(self):
        """Conecta ao banco de dados PostgreSQL"""
        try:
            # Se já houver uma conexão, fecha antes de abrir uma nova
            if self.conn and not self.conn.closed:
                self.conn.close()
            self.conn = psycopg2.connect(**self.db_config)
            # Define o search_path para o schema conflitos para todas as transações desta conexão
            # Isso evita a necessidade de prefixar tabelas com 'conflitos.' em todas as queries
            return True
        except psycopg2.Error as e:
            messagebox.showerror(
                "Erro de Conexão", f"Erro ao conectar ao banco: {str(e)}")
            return False

    def execute_query(self, query, params=None, fetch=True):
        """Executa uma query no banco de dados"""
        try:
            if not self.conn or self.conn.closed:
                if not self.connect_db():
                    return None

            cursor = self.conn.cursor()
            cursor.execute(query, params)

            if fetch:
                results = cursor.fetchall()
                columns = [desc[0]
                           for desc in cursor.description] if cursor.description else []
                cursor.close()
                return results, columns
            else:
                self.conn.commit()
                cursor.close()
                return True
        except psycopg2.Error as e:
            messagebox.showerror(
                "Erro na Query", f"Erro ao executar query: {str(e)}\nQuery: {query}")
            if self.conn and not self.conn.closed:  # Verifica se a conexão ainda está aberta
                try:
                    self.conn.rollback()
                except psycopg2.Error as re:
                    print(f"Erro durante o rollback: {re}")
            return None

    def setup_gui(self):
        """Configura a interface gráfica"""
        # --- Configuração de Estilos (Início das Alterações) ---
        style = ttk.Style()

        # Tentar usar um tema escuro se disponível. Nem todos os sistemas operacionais suportam todos os temas.
        # 'clam' é um bom ponto de partida para personalização
        try:
            style.theme_use('clam')
        except tk.TclError:
            print("Tema 'clam' não disponível, usando o tema padrão.")

        # Cores para o tema escuro
        BG_COLOR = "#2B2B2B"  # Quase preto
        FG_COLOR = "#FFFFFF"  # Branco
        ACCENT_COLOR = "#4CAF50"  # Um verde suave para destaque (botões, etc.)
        BORDER_COLOR = "#4A4A4A"  # Cinza escuro para bordas

        # Estilo para o Root (janela principal)
        self.root.configure(bg=BG_COLOR)

        # Estilo para Frames e LabelFrames (fundo e borda)
        style.configure("TFrame", background=BG_COLOR)
        style.configure("TLabelframe", background=BG_COLOR,
                        foreground=FG_COLOR, bordercolor=BORDER_COLOR)
        style.configure("TLabelframe.Label", background=BG_COLOR,
                        foreground=FG_COLOR)  # Cor do texto do LabelFrame

        # Estilo para Labels
        style.configure("TLabel", background=BG_COLOR, foreground=FG_COLOR)

        # Estilo para Buttons
        style.configure("TButton", background=ACCENT_COLOR,
                        foreground="black", font=('Arial', 10, 'bold'))
        style.map("TButton",
                  background=[('active', '#66BB6A'), ('pressed', '#388E3C')],
                  foreground=[('active', 'white'), ('pressed', 'white')])

        # Estilo para Entry e Combobox (normalmente têm sua própria cor de fundo do sistema)
        # Para forçar cores escuras em Entry/Combobox, é preciso mexer em seus "elements"
        # Isso pode ser mais complexo e variar entre plataformas.
        # Uma abordagem mais simples é apenas definir o foreground (cor do texto).
        style.configure("TEntry", fieldbackground="#3C3C3C",
                        foreground=FG_COLOR, bordercolor=BORDER_COLOR)
        style.map("TEntry", fieldbackground=[
                  ('focus', '#5C5C5C')])  # Cor ao focar

        style.configure("TCombobox", fieldbackground="#3C3C3C", foreground=FG_COLOR,
                        selectbackground="#5C5C5C", selectforeground=FG_COLOR, bordercolor=BORDER_COLOR)
        style.map("TCombobox",
                  # Cor de fundo quando readonly
                  fieldbackground=[('readonly', '#3C3C3C')],
                  # Cor de seleção quando readonly
                  selectbackground=[('readonly', '#5C5C5C')],
                  # Cor do texto selecionado quando readonly
                  selectforeground=[('readonly', FG_COLOR)],
                  # Cor do dropdown ao passar o mouse
                  background=[('active', '#5C5C5C')])

        # Estilo para Notebook (abas)
        style.configure("TNotebook", background=BG_COLOR,
                        bordercolor=BORDER_COLOR)
        style.configure("TNotebook.Tab", background=BG_COLOR,
                        foreground=FG_COLOR, bordercolor=BORDER_COLOR)
        style.map("TNotebook.Tab",
                  background=[('selected', ACCENT_COLOR)],
                  foreground=[('selected', 'black')],
                  # Expande levemente a aba selecionada
                  expand=[('selected', [1, 1, 1, 0])])

        # --- Fim das Alterações de Estilos ---

        # Notebook para as abas
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Abas
        self.tab_cadastro = ttk.Frame(self.notebook)
        self.tab_relatorios = ttk.Frame(self.notebook)
        self.tab_conexao = ttk.Frame(self.notebook)

        self.notebook.add(self.tab_cadastro, text="Cadastros")
        self.notebook.add(self.tab_relatorios, text="Relatórios")
        self.notebook.add(self.tab_conexao, text="Conexão DB")

        self.setup_cadastro_tab()
        self.setup_relatorios_tab()
        self.setup_conexao_tab()

    def setup_conexao_tab(self):
        """Configura a aba de conexão com banco"""
        # Usar as cores definidas na classe para consistência
        frame = ttk.LabelFrame(
            self.tab_conexao, text="Configuração do Banco de Dados")
        frame.pack(fill=tk.BOTH, expand=True, padx=20,
                   pady=20)  # Aumenta padding

        ttk.Label(frame, text="Host:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.host_var = tk.StringVar(value=self.db_config['host'])
        ttk.Entry(frame, textvariable=self.host_var, width=35).grid(  # Aumenta largura
            row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Database:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.db_var = tk.StringVar(value=self.db_config['database'])
        ttk.Entry(frame, textvariable=self.db_var, width=35).grid(  # Aumenta largura
            row=1, column=1, padx=5, pady=5)

        # Campo de entrada para o usuário
        ttk.Label(frame, text="Usuário:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.user_var = tk.StringVar(value=self.db_config['user'])
        ttk.Entry(frame, textvariable=self.user_var, width=35).grid(
            row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Senha:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.pass_var = tk.StringVar(value=self.db_config['password'])
        ttk.Entry(frame, textvariable=self.pass_var, width=35,  # Aumenta largura
                  show="*").grid(row=3, column=1, padx=5, pady=5)

        # Botões (ajustados para a próxima linha)
        ttk.Button(frame, text="Testar Conexão", command=self.test_connection).grid(
            row=4, column=0, padx=5, pady=15, sticky="ew")  # Preenche horizontalmente
        ttk.Button(frame, text="Salvar Configuração", command=self.save_config).grid(
            row=4, column=1, padx=5, pady=15, sticky="ew")  # Preenche horizontalmente

        self.status_label = ttk.Label(
            frame, text="Status: Não conectado", font=('Segoe UI', 10, 'bold'))
        self.status_label.grid(row=5, column=0, columnspan=2, pady=10)
        # Configuração de cor do status_label será feita dinamicamente em test_connection

        # Centralizar colunas
        frame.grid_columnconfigure(0, weight=1)
        frame.grid_columnconfigure(1, weight=1)

    def test_connection(self):
        """Testa a conexão com o banco"""
        self.update_config()
        if self.connect_db():
            self.status_label.config(
                text="Status: Conectado com sucesso!", foreground="#00FF00")  # Verde para sucesso
            messagebox.showinfo("Sucesso", "Conexão estabelecida com sucesso!")
            # Atualizar combos que dependem de dados do banco
            self.atualizar_todos_os_combos()
        else:
            self.status_label.config(
                text="Status: Erro na conexão", foreground="#FF0000")  # Vermelho para erro

    def save_config(self):
        """Salva a configuração do banco"""
        self.update_config()
        messagebox.showinfo("Sucesso", "Configuração salva!")

    def update_config(self):
        """Atualiza a configuração do banco"""
        self.db_config.update({
            'host': self.host_var.get(),
            'database': self.db_var.get(),
            'user': self.user_var.get(),
            'password': self.pass_var.get()
        })

    def setup_cadastro_tab(self):
        """Configura a aba de cadastros"""
        cadastro_notebook = ttk.Notebook(self.tab_cadastro)
        cadastro_notebook.pack(fill=tk.BOTH, expand=True)

        self.tab_conflitos = ttk.Frame(cadastro_notebook)
        self.tab_grupos = ttk.Frame(cadastro_notebook)
        self.tab_divisoes = ttk.Frame(cadastro_notebook)
        self.tab_lideres = ttk.Frame(cadastro_notebook)
        self.tab_chefes = ttk.Frame(cadastro_notebook)

        cadastro_notebook.add(self.tab_conflitos, text="Conflitos")
        cadastro_notebook.add(self.tab_grupos, text="Grupos Militares")
        cadastro_notebook.add(self.tab_divisoes, text="Divisões")
        cadastro_notebook.add(self.tab_lideres, text="Líderes Políticos")
        cadastro_notebook.add(self.tab_chefes, text="Chefes Militares")

        self.setup_conflitos_form()
        self.setup_grupos_form()
        self.setup_divisoes_form()
        self.setup_lideres_form()
        self.setup_chefes_form()

    def setup_conflitos_form(self):
        """Formulário de cadastro de conflitos com seções dinâmicas para detalhes."""
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"
        SELECT_BG_COLOR = "#5C5C5C"  # Cor de fundo para itens selecionados em Listbox

        main_frame = ttk.Frame(self.tab_conflitos)
        main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Frame superior para dados gerais e listas de seleção
        top_frame = ttk.LabelFrame(main_frame, text="Dados Gerais do Conflito")
        top_frame.pack(fill=tk.X, expand=False, pady=(0, 10))

        # --- Configuração do Grid ---
        # Coluna dos campos de entrada
        top_frame.grid_columnconfigure(1, weight=1)
        # Coluna para a lista de países
        top_frame.grid_columnconfigure(2, weight=1)
        # Coluna para a lista de grupos
        top_frame.grid_columnconfigure(3, weight=1)

        # --- Widgets de Entrada ---
        ttk.Label(top_frame, text="Nome do Conflito:").grid(
            row=0, column=0, sticky=tk.W, pady=5, padx=5)
        self.conflito_nome = tk.StringVar()
        ttk.Entry(top_frame, textvariable=self.conflito_nome, width=50).grid(
            row=0, column=1, sticky="ew", pady=5)

        ttk.Label(top_frame, text="Tipo de Conflito:").grid(
            row=1, column=0, sticky=tk.W, pady=5, padx=5)
        self.conflito_tipo = tk.StringVar()
        tipo_combo = ttk.Combobox(top_frame, textvariable=self.conflito_tipo,
                                  values=['territorial', 'religioso',
                                          'economico', 'racial'],
                                  state="readonly", width=48)
        tipo_combo.grid(row=1, column=1, sticky="ew", pady=5)
        tipo_combo.bind("<<ComboboxSelected>>",
                        self.handle_conflito_tipo_change)

        ttk.Label(top_frame, text="Número de Mortos:").grid(
            row=2, column=0, sticky=tk.W, pady=5, padx=5)
        self.conflito_mortos = tk.IntVar(value=0)
        ttk.Entry(top_frame, textvariable=self.conflito_mortos,
                  width=20).grid(row=2, column=1, sticky="w", pady=5)

        ttk.Label(top_frame, text="Número de Feridos:").grid(
            row=3, column=0, sticky=tk.W, pady=5, padx=5)
        self.conflito_feridos = tk.IntVar(value=0)
        ttk.Entry(top_frame, textvariable=self.conflito_feridos,
                  width=20).grid(row=3, column=1, sticky="w", pady=5)

        ttk.Button(top_frame, text="Atualizar Todas as Listas", command=self.atualizar_todos_os_combos).grid(
            row=4, column=1, padx=5, pady=10, sticky="w")

        # --- Lista de Países Afetados ---
        paises_frame = ttk.LabelFrame(
            top_frame, text="Países Afetados (Ctrl+Click)")
        paises_frame.grid(row=0, column=2, rowspan=5,
                          padx=10, pady=5, sticky="nsew")
        paises_frame.grid_rowconfigure(0, weight=1)
        paises_frame.grid_columnconfigure(0, weight=1)

        self.paises_listbox = tk.Listbox(
            paises_frame, selectmode=tk.EXTENDED, height=8, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.paises_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar_paises = ttk.Scrollbar(
            paises_frame, orient=tk.VERTICAL, command=self.paises_listbox.yview)
        scrollbar_paises.grid(row=0, column=1, sticky="ns")
        self.paises_listbox.config(yscrollcommand=scrollbar_paises.set)

        # --- NOVA: Lista de Grupos Armados Envolvidos ---
        grupos_frame = ttk.LabelFrame(
            top_frame, text="Grupos Armados (Ctrl+Click)")
        grupos_frame.grid(row=0, column=3, rowspan=5,  # Adicionado na nova coluna 3
                          padx=10, pady=5, sticky="nsew")
        grupos_frame.grid_rowconfigure(0, weight=1)
        grupos_frame.grid_columnconfigure(0, weight=1)

        self.grupos_listbox = tk.Listbox(
            grupos_frame, selectmode=tk.EXTENDED, height=8, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.grupos_listbox.grid(row=0, column=0, sticky="nsew")
        scrollbar_grupos = ttk.Scrollbar(
            grupos_frame, orient=tk.VERTICAL, command=self.grupos_listbox.yview)
        scrollbar_grupos.grid(row=0, column=1, sticky="ns")
        self.grupos_listbox.config(yscrollcommand=scrollbar_grupos.set)

        # Frame inferior para os detalhes dinâmicos (sem alterações)
        self.dynamic_details_frame = ttk.Frame(main_frame)
        self.dynamic_details_frame.pack(fill=tk.X, expand=False, pady=5)

        self.frame_conflito_territorial = ttk.LabelFrame(
            self.dynamic_details_frame, text="Regiões Afetadas")
        self.regioes_listbox = tk.Listbox(
            self.frame_conflito_territorial, selectmode=tk.EXTENDED, height=5, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.regioes_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.frame_conflito_territorial.grid(row=0, column=0, sticky="ew")

        self.frame_conflito_religioso = ttk.LabelFrame(
            self.dynamic_details_frame, text="Religiões Envolvidas")
        self.religioes_listbox = tk.Listbox(
            self.frame_conflito_religioso, selectmode=tk.EXTENDED, height=5, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.religioes_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.frame_conflito_religioso.grid(row=0, column=0, sticky="ew")

        self.frame_conflito_economico = ttk.LabelFrame(
            self.dynamic_details_frame, text="Matérias-Primas Disputadas")
        self.materias_primas_listbox = tk.Listbox(
            self.frame_conflito_economico, selectmode=tk.EXTENDED, height=5, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.materias_primas_listbox.pack(
            fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.frame_conflito_economico.grid(row=0, column=0, sticky="ew")

        self.frame_conflito_racial = ttk.LabelFrame(
            self.dynamic_details_frame, text="Etnias Enfrentadas")
        self.etnias_listbox = tk.Listbox(
            self.frame_conflito_racial, selectmode=tk.EXTENDED, height=5, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.etnias_listbox.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        self.frame_conflito_racial.grid(row=0, column=0, sticky="ew")

        self.handle_conflito_tipo_change()  # Esconde todos no início

        ttk.Button(main_frame, text="Cadastrar Conflito Completo",
                   command=self.cadastrar_conflito).pack(pady=10)

    def setup_grupos_form(self):
        """Formulário de cadastro de grupos militares com associação a múltiplos conflitos."""
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"
        SELECT_BG_COLOR = "#5C5C5C"

        # Dicionário para guardar as entradas de data que serão criadas dinamicamente
        self.date_entries = {}

        frame = ttk.LabelFrame(
            self.tab_grupos, text="Cadastro de Grupos Militares e Participação em Conflito")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- Frame para Dados do Grupo e Listas ---
        left_frame = ttk.Frame(frame)
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))

        # --- Frame para as Datas Dinâmicas ---
        self.datas_frame = ttk.LabelFrame(
            frame, text="Datas de Incorporação (AAAA-MM-DD)")
        self.datas_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # --- Campos de Nome, Líder e Apoios (no frame da esquerda) ---
        ttk.Label(left_frame, text="Nome do Grupo:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.grupo_nome = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.grupo_nome, width=40).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(left_frame, text="Nome do Líder Inicial:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.grupo_lider = tk.StringVar()
        ttk.Entry(left_frame, textvariable=self.grupo_lider, width=40).grid(
            row=1, column=1, padx=5, pady=5)

        ttk.Label(left_frame, text="Apoios/Descrição do Líder:").grid(row=2,
                                                                      column=0, sticky=tk.W, padx=5, pady=5)
        self.grupo_apoios = scrolledtext.ScrolledText(
            left_frame, width=40, height=5, bg="#3C3C3C", fg=FG_COLOR, insertbackground=FG_COLOR)
        self.grupo_apoios.grid(row=2, column=1, padx=5, pady=5)

        # --- NOVA: Lista de Conflitos para Associação ---
        conflitos_list_frame = ttk.LabelFrame(
            left_frame, text="Associar aos Conflitos (Ctrl+Click)")
        conflitos_list_frame.grid(
            row=3, column=0, columnspan=2, pady=10, sticky="ew")

        self.conflitos_listbox_grupo = tk.Listbox(
            conflitos_list_frame, selectmode=tk.EXTENDED, height=6, exportselection=False,
            bg=BG_COLOR, fg=FG_COLOR, selectbackground=SELECT_BG_COLOR, selectforeground=FG_COLOR,
            borderwidth=1, relief="solid")
        self.conflitos_listbox_grupo.pack(
            side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Evento que chama a função para criar as entradas de data quando a seleção muda
        self.conflitos_listbox_grupo.bind(
            "<<ListboxSelect>>", self.atualizar_entradas_data_conflito)

        scrollbar_conflitos = ttk.Scrollbar(
            conflitos_list_frame, orient=tk.VERTICAL, command=self.conflitos_listbox_grupo.yview)
        scrollbar_conflitos.pack(side=tk.RIGHT, fill=tk.Y)
        self.conflitos_listbox_grupo.config(
            yscrollcommand=scrollbar_conflitos.set)

        ttk.Button(left_frame, text="Atualizar Lista de Conflitos",
                   command=self.atualizar_conflitos_listbox_grupo).grid(row=4, column=0, columnspan=2, pady=5)

        # --- Botão de Cadastro (agora dentro do frame principal) ---
        ttk.Button(frame, text="Cadastrar Grupo e Associar a Conflitos",
                   command=self.cadastrar_grupo).pack(side=tk.BOTTOM, pady=20)

    def setup_divisoes_form(self):
        """Formulário de cadastro de divisões e seu primeiro chefe militar."""
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"

        frame = ttk.LabelFrame(
            self.tab_divisoes, text="Cadastro de Nova Divisão com Chefe de Comando")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # --- DADOS DA DIVISÃO ---
        ttk.Label(frame, text="--- Dados da Divisão ---", font=("Arial", 10, "bold"), background=BG_COLOR, foreground=FG_COLOR).grid(
            row=0, column=0, columnspan=3, pady=(5, 10))

        ttk.Label(frame, text="Grupo da Divisão:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.divisao_grupo = ttk.Combobox(frame, width=38, state="readonly")
        self.divisao_grupo.grid(row=1, column=1, padx=5, pady=5)
        # Evento que chama a função para filtrar os líderes quando um grupo é selecionado
        self.divisao_grupo.bind("<<ComboboxSelected>>",
                                self.atualizar_lideres_para_divisao)

        ttk.Label(frame, text="N° Barcos:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=2)
        self.divisao_barcos = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=self.divisao_barcos, width=15).grid(
            row=2, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(frame, text="N° Tanques:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=2)
        self.divisao_tanques = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=self.divisao_tanques, width=15).grid(
            row=3, column=1, sticky=tk.W, padx=5, pady=2)

        ttk.Label(frame, text="N° Aviões:").grid(
            row=2, column=2, sticky=tk.W, padx=5, pady=2)
        self.divisao_avioes = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=self.divisao_avioes, width=15).grid(
            row=2, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(frame, text="N° Homens:").grid(
            row=3, column=2, sticky=tk.W, padx=5, pady=2)
        self.divisao_homens = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=self.divisao_homens, width=15).grid(
            row=3, column=3, sticky=tk.W, padx=5, pady=2)

        ttk.Label(frame, text="N° Baixas:").grid(
            row=4, column=0, sticky=tk.W, padx=5, pady=2)
        self.divisao_baixas = tk.IntVar(value=0)
        ttk.Entry(frame, textvariable=self.divisao_baixas, width=15).grid(
            row=4, column=1, sticky=tk.W, padx=5, pady=2)

        # --- DADOS DO NOVO CHEFE MILITAR ---
        ttk.Label(frame, text="--- Dados do Novo Chefe de Comando ---", font=("Arial", 10, "bold"), background=BG_COLOR, foreground=FG_COLOR).grid(
            row=5, column=0, columnspan=3, pady=(20, 10))

        ttk.Label(frame, text="Nome do Novo Chefe:").grid(
            row=6, column=0, sticky=tk.W, padx=5, pady=5)
        self.divisao_nome_chefe = tk.StringVar()
        ttk.Entry(frame, textvariable=self.divisao_nome_chefe, width=40).grid(
            row=6, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame, text="Faixa Hierárquica:").grid(
            row=7, column=0, sticky=tk.W, padx=5, pady=5)
        self.divisao_faixa_chefe = tk.StringVar()
        ttk.Combobox(frame, textvariable=self.divisao_faixa_chefe,
                     values=['General', 'Coronel', 'Major', 'Capitão', 'Comandante'], state="readonly", width=38).grid(
                         row=7, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Label(frame, text="Obedece ao Líder:").grid(
            row=8, column=0, sticky=tk.W, padx=5, pady=5)
        self.divisao_lider_combo = ttk.Combobox(
            frame, width=38, state="readonly")
        self.divisao_lider_combo.grid(
            row=8, column=1, columnspan=2, sticky=tk.W, padx=5, pady=5)

        ttk.Button(frame, text="Atualizar Listas", command=self.handle_atualizar_divisao_listas).grid(
            row=1, column=2, padx=5, pady=5)

        # --- BOTÃO DE CADASTRO ---
        ttk.Button(frame, text="Cadastrar Divisão e Chefe", command=self.cadastrar_divisao).grid(
            row=9, column=0, columnspan=4, pady=25)

    def setup_lideres_form(self):
        """Formulário de cadastro de líderes políticos"""
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"

        frame = ttk.LabelFrame(
            self.tab_lideres, text="Cadastro de Líderes Políticos")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Nome do Líder:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.lider_nome = tk.StringVar()
        ttk.Entry(frame, textvariable=self.lider_nome, width=40).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Grupo Liderado:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.lider_grupo = ttk.Combobox(
            frame, width=38, state="readonly")
        self.lider_grupo.grid(row=1, column=1, padx=5, pady=5)
        ttk.Button(frame, text="Atualizar Grupos",
                   command=self.atualizar_grupos_combo_lider).grid(row=1, column=2, padx=5, pady=5)

        ttk.Label(frame, text="Apoios/Descrição:").grid(row=2,
                                                        column=0, sticky=tk.W, padx=5, pady=5)
        self.lider_apoios = scrolledtext.ScrolledText(
            frame, width=40, height=5, bg="#3C3C3C", fg=FG_COLOR, insertbackground=FG_COLOR)
        self.lider_apoios.grid(row=2, column=1, padx=5, pady=5)

        ttk.Button(frame, text="Cadastrar Líder",
                   command=self.cadastrar_lider).grid(row=3, column=0, columnspan=2, padx=5, pady=10)

    def setup_chefes_form(self):
        """Formulário de cadastro de chefes militares"""
        BG_COLOR = "#2B2B2B"
        FG_COLOR = "#FFFFFF"

        frame = ttk.LabelFrame(
            self.tab_chefes, text="Cadastro de Chefes Militares")
        frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        ttk.Label(frame, text="Nome do Chefe:").grid(
            row=0, column=0, sticky=tk.W, padx=5, pady=5)
        self.chefe_nome = tk.StringVar()
        ttk.Entry(frame, textvariable=self.chefe_nome, width=40).grid(
            row=0, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Faixa Hierárquica:").grid(
            row=1, column=0, sticky=tk.W, padx=5, pady=5)
        self.chefe_faixa = tk.StringVar()
        combo_faixa = ttk.Combobox(frame, textvariable=self.chefe_faixa,
                                   values=['General', 'Coronel', 'Major', 'Capitão', 'Comandante'], state="readonly")
        combo_faixa.grid(row=1, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Líder Político:").grid(
            row=2, column=0, sticky=tk.W, padx=5, pady=5)
        self.chefe_lider = ttk.Combobox(
            frame, width=38, state="readonly")
        self.chefe_lider.grid(row=2, column=1, padx=5, pady=5)

        ttk.Label(frame, text="Divisão Liderada:").grid(
            row=3, column=0, sticky=tk.W, padx=5, pady=5)
        self.chefe_divisao = ttk.Combobox(
            frame, width=38, state="readonly")
        self.chefe_divisao.grid(row=3, column=1, padx=5, pady=5)

        # Botão para atualizar combos de líderes e divisões
        ttk.Button(frame, text="Atualizar Listas",
                   command=self.atualizar_combos_chefes).grid(row=2, column=2, rowspan=2, padx=5, pady=5, sticky=tk.W)

        ttk.Button(frame, text="Cadastrar Chefe",
                   command=self.cadastrar_chefe).grid(row=4, column=0, columnspan=2, padx=5, pady=10)

    def setup_relatorios_tab(self):
        """Configura a aba de relatórios"""
        BG_COLOR = "#2B2B2B"

        # Frame para botões
        btn_frame_container = ttk.Frame(self.tab_relatorios)
        btn_frame_container.pack(fill=tk.X, padx=10, pady=5)

        # Botões dos relatórios - Primeira Linha
        btn_frame_line1 = ttk.Frame(btn_frame_container)
        btn_frame_line1.pack(fill=tk.X)

        ttk.Button(btn_frame_line1, text="Gráfico: Tipos de Conflito",
                   command=self.grafico_tipos_conflito).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(btn_frame_line1, text="Traficantes (Barrett/M200)",
                   command=self.relatorio_traficantes_barrett).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(btn_frame_line1, text="Top 5 Conflitos (Mortos)",
                   command=self.relatorio_top_conflitos_mortos).pack(side=tk.LEFT, padx=5, pady=2)

        # Botões dos relatórios - Segunda Linha
        btn_frame_line2 = ttk.Frame(btn_frame_container)
        # Adiciona um pady para separar as linhas de botões
        btn_frame_line2.pack(fill=tk.X, pady=5)

        ttk.Button(btn_frame_line2, text="Top 5 Organizações (Mediações)",
                   command=self.relatorio_top_organizacoes).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(btn_frame_line2, text="Top 5 Grupos (Armas Recebidas)",
                   command=self.relatorio_top_grupos_armas).pack(side=tk.LEFT, padx=5, pady=2)
        ttk.Button(btn_frame_line2, text="País com Mais Conflitos Religiosos",
                   command=self.relatorio_paises_religiosos).pack(side=tk.LEFT, padx=5, pady=2)

        # Frame para resultados
        self.result_frame = ttk.Frame(self.tab_relatorios)
        self.result_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

    # --- MÉTODOS DE CADASTRO ---
    def cadastrar_conflito(self):
        """Cadastra um novo conflito com todos os seus detalhes em uma única transação."""
        tipo_conflito = self.conflito_tipo.get()
        paises_indices = self.paises_listbox.curselection()
        grupos_indices = self.grupos_listbox.curselection()  # Pega os grupos selecionados

        # --- VALIDAÇÃO PRINCIPAL ---
        if not all([self.conflito_nome.get(), tipo_conflito]) or not paises_indices:
            messagebox.showerror(
                "Erro de Validação", "Nome, Tipo e pelo menos um País são obrigatórios!")
            return

        if len(grupos_indices) < 2:
            messagebox.showerror(
                "Erro de Validação", "Um conflito deve ter pelo menos dois grupos armados selecionados.")
            return

        try:
            num_mortos = self.conflito_mortos.get()
            num_feridos = self.conflito_feridos.get()
        except tk.TclError:
            messagebox.showerror(
                "Erro de Validação", "Número de mortos e feridos devem ser números inteiros válidos.")
            return

        if tipo_conflito == 'religioso' and not self.religioes_listbox.curselection():
            messagebox.showerror(
                "Erro de Validação", "Para conflitos religiosos, selecione ao menos uma religião.")
            return
        if tipo_conflito == 'economico' and not self.materias_primas_listbox.curselection():
            messagebox.showerror(
                "Erro de Validação", "Para conflitos econômicos, selecione ao menos uma matéria-prima.")
            return
        if tipo_conflito == 'racial' and not self.etnias_listbox.curselection():
            messagebox.showerror(
                "Erro de Validação", "Para conflitos raciais, selecione ao menos uma etnia.")
            return

        cursor = None
        try:
            if not self.conn or self.conn.closed:
                if not self.connect_db():
                    return

            cursor = self.conn.cursor()

            # 1. Cria o conflito principal usando a Stored Procedure
            sp_params = (self.conflito_nome.get(),
                         tipo_conflito, num_mortos, num_feridos)
            cursor.execute(
                "SELECT sp_criar_conflito_com_tipo(%s, %s, %s, %s)", sp_params)
            novo_cod_conflito = cursor.fetchone()[0]

            # 2. Associa os países afetados
            for index in paises_indices:
                cod_pais = int(self.paises_listbox.get(
                    index).split('-')[0].strip())
                cursor.execute("INSERT INTO Conflito_Afeta_Pais (cod_conflito_fk, cod_pais_fk) VALUES (%s, %s)",
                               (novo_cod_conflito, cod_pais))

            # 3. Associa os grupos armados participantes
            data_hoje = datetime.date.today()
            for index in grupos_indices:
                cod_grupo = int(self.grupos_listbox.get(
                    index).split('-')[0].strip())
                cursor.execute(
                    """
                    INSERT INTO Grupo_Armado_Participa_Conflito 
                    (cod_grupo_fk, cod_conflito_fk, data_incorporacao) 
                    VALUES (%s, %s, %s)
                    """,
                    (cod_grupo, novo_cod_conflito, data_hoje)
                )

            # 4. Insere detalhes específicos do tipo de conflito
            if tipo_conflito == 'religioso':
                for index in self.religioes_listbox.curselection():
                    id_religiao = int(self.religioes_listbox.get(
                        index).split('-')[0].strip())
                    cursor.execute("INSERT INTO Conflito_Religioso_Afeta_Religiao (cod_conflito_religioso_fk, id_religiao_fk) VALUES (%s, %s)",
                                   (novo_cod_conflito, id_religiao))
            elif tipo_conflito == 'economico':
                for index in self.materias_primas_listbox.curselection():
                    id_materia = int(self.materias_primas_listbox.get(
                        index).split('-')[0].strip())
                    cursor.execute("INSERT INTO Conflito_Economico_Afeta_MateriaPrima (cod_conflito_economico_fk, id_materia_prima_fk) VALUES (%s, %s)",
                                   (novo_cod_conflito, id_materia))
            elif tipo_conflito == 'racial':
                for index in self.etnias_listbox.curselection():
                    id_etnia = int(self.etnias_listbox.get(
                        index).split('-')[0].strip())
                    cursor.execute("INSERT INTO Conflito_Racial_Afeta_Etnia (cod_conflito_racial_fk, id_etnia_fk) VALUES (%s, %s)",
                                   (novo_cod_conflito, id_etnia))

            self.conn.commit()

            messagebox.showinfo(
                "Sucesso", f"Conflito '{self.conflito_nome.get()}' (ID: {novo_cod_conflito}) e todos os seus detalhes foram cadastrados com sucesso!")
            self.limpar_form_conflito()

        except Exception as e:
            if self.conn:
                self.conn.rollback()
            messagebox.showerror(
                "Erro na Transação", f"A operação falhou e foi totalmente revertida: {str(e)}")

        finally:
            if cursor:
                cursor.close()

    def cadastrar_grupo(self):
        """
        Cadastra um novo grupo, seu líder, sua primeira divisão e o associa
        a um ou mais conflitos com suas respectivas datas de incorporação.
        Tudo é feito em uma única transação.
        """
        # --- Validações Iniciais ---
        if not all([self.grupo_nome.get(), self.grupo_lider.get()]):
            messagebox.showerror(
                "Erro de Validação", "Nome do Grupo e Nome do Líder são obrigatórios!")
            return

        if not self.date_entries:
            messagebox.showerror(
                "Erro de Validação", "Selecione pelo menos um conflito para associar o grupo.")
            return

        # Valida as datas e as armazena em um dicionário
        participacoes = {}
        for cod_conflito, entry_widget in self.date_entries.items():
            data_str = entry_widget.get()
            if not data_str:
                messagebox.showerror(
                    "Erro de Validação", f"A data para o conflito ID {cod_conflito} é obrigatória.")
                return
            try:
                data_incorporacao = datetime.date.fromisoformat(data_str)
                participacoes[cod_conflito] = data_incorporacao
            except ValueError:
                messagebox.showerror(
                    "Erro de Formato", f"A data '{data_str}' é inválida. Use o formato AAAA-MM-DD.")
                return

        # --- Lógica da Transação ---
        cursor = None
        try:
            if not self.conn or self.conn.closed:
                if not self.connect_db():
                    return

            cursor = self.conn.cursor()

            # 1. Cria o grupo, líder e primeira divisão usando a Stored Procedure
            sp_params = (self.grupo_nome.get(), self.grupo_lider.get(),
                         self.grupo_apoios.get("1.0", tk.END).strip())
            cursor.execute(
                "SELECT sp_criar_grupo_armado_completo(%s, %s, %s)", sp_params)

            result_sp = cursor.fetchone()
            if not result_sp:
                raise psycopg2.DatabaseError(
                    "O procedimento armazenado não retornou um ID para o novo grupo.")

            novo_cod_grupo = result_sp[0]

            # 2. Associa o novo grupo aos conflitos selecionados com as datas fornecidas
            insert_query = """
                INSERT INTO Grupo_Armado_Participa_Conflito
                (cod_grupo_fk, cod_conflito_fk, data_incorporacao)
                VALUES (%s, %s, %s)
            """
            for cod_conflito, data_incorporacao in participacoes.items():
                insert_params = (novo_cod_grupo, cod_conflito,
                                 data_incorporacao)
                cursor.execute(insert_query, insert_params)

            # 3. Se tudo correu bem, efetiva a transação
            self.conn.commit()
            messagebox.showinfo(
                "Sucesso", f"Grupo '{self.grupo_nome.get()}' (ID: {novo_cod_grupo}) foi criado e associado aos conflitos com sucesso!")

            self.limpar_form_grupo()
            self.atualizar_todos_os_combos()

        except psycopg2.Error as e:
            if self.conn:
                self.conn.rollback()  # Garante que nada seja salvo em caso de erro
            messagebox.showerror(
                "Erro no Banco de Dados", f"Falha ao cadastrar grupo: {str(e)}")

        finally:
            if cursor:
                cursor.close()

    def cadastrar_divisao(self):
        """Cadastra uma nova divisão e seu primeiro chefe militar em uma única transação."""
        # --- Validação dos dados de entrada ---
        if not all([self.divisao_grupo.get(), self.divisao_nome_chefe.get(),
                    self.divisao_faixa_chefe.get(), self.divisao_lider_combo.get()]):
            messagebox.showerror(
                "Erro de Validação", "Todos os campos para a divisão e para o novo chefe são obrigatórios!")
            return

        try:
            cod_grupo_str = self.divisao_grupo.get().split('-')[0].strip()
            cod_grupo = int(cod_grupo_str)

            id_lider_str = self.divisao_lider_combo.get().split('-')[0].strip()
            id_lider = int(id_lider_str)
        except (ValueError, IndexError):
            messagebox.showerror(
                "Erro de Formato", "O formato do Grupo ou do Líder selecionado é inválido.")
            return

        # --- Início da Transação ---
        cursor = None
        try:
            if not self.conn or self.conn.closed:
                if not self.connect_db():
                    return

            cursor = self.conn.cursor()

            # 1. INSERE a divisão e retorna o número gerado pelo trigger do banco
            divisao_params = (
                cod_grupo, self.divisao_barcos.get(), self.divisao_tanques.get(),
                self.divisao_avioes.get(), self.divisao_homens.get(), self.divisao_baixas.get()
            )
            insert_divisao_query = """
                INSERT INTO Divisao
                (cod_grupo_fk, num_barcos, num_tanques, num_avioes, num_homens, num_baixas_divisao)
                VALUES (%s, %s, %s, %s, %s, %s)
                RETURNING num_divisao
            """
            cursor.execute(insert_divisao_query, divisao_params)
            novo_num_divisao = cursor.fetchone()[0]

            # 2. INSERE o novo chefe, já associando à divisão recém-criada
            chefe_params = (
                self.divisao_nome_chefe.get(), self.divisao_faixa_chefe.get(),
                id_lider, cod_grupo, novo_num_divisao
            )
            insert_chefe_query = """
                INSERT INTO Chefe_Militar
                (nome_chefe, faixa_hierarquica, id_lider_politico_obedece_fk,
                 cod_grupo_divisao_liderada_fk, num_divisao_liderada_fk)
                VALUES (%s, %s, %s, %s, %s)
            """
            cursor.execute(insert_chefe_query, chefe_params)

            # 3. Se tudo deu certo, efetiva a transação
            self.conn.commit()

            messagebox.showinfo("Sucesso",
                                f"Divisão N° {novo_num_divisao} e seu chefe '{self.divisao_nome_chefe.get()}' foram cadastrados com sucesso!")

            self.limpar_form_divisao()
            self.atualizar_todos_os_combos()

        except psycopg2.Error as e:
            if self.conn:
                self.conn.rollback()  # Reverte tudo em caso de erro
            messagebox.showerror(
                "Erro na Transação", f"A operação falhou e foi totalmente revertida: {str(e)}")

        finally:
            if cursor:
                cursor.close()

    def cadastrar_lider(self):
        """Cadastra um novo líder político"""
        if not self.lider_nome.get() or not self.lider_grupo.get():
            messagebox.showerror(
                "Erro de Validação", "Nome do Líder e Grupo Liderado são obrigatórios!")
            return

        try:
            cod_grupo_str = self.lider_grupo.get().split('-')[0].strip()
            cod_grupo = int(cod_grupo_str)
        except ValueError:
            messagebox.showerror(
                "Erro de Validação", "Código do grupo inválido. Selecione um grupo da lista.")
            return
        except IndexError:
            messagebox.showerror(
                "Erro de Validação", "Formato do grupo selecionado é inválido. Atualize a lista de grupos.")
            return

        query = """INSERT INTO Lider_Politico
                     (nome_lider, cod_grupo_liderado_fk, apoios_descricao)
                     VALUES (%s, %s, %s)"""
        params = (self.lider_nome.get(), cod_grupo,
                  self.lider_apoios.get("1.0", tk.END).strip())

        if self.execute_query(query, params, fetch=False):
            messagebox.showinfo(
                "Sucesso", "Líder político cadastrado com sucesso!")
            self.limpar_form_lider()
            self.atualizar_combos_chefes()  # Atualiza combo de líderes para chefes
        # else:
            # messagebox.showerror("Erro", "Falha ao cadastrar líder político.")

    def cadastrar_chefe(self):
        """Cadastra um novo chefe militar"""
        if not self.chefe_nome.get() or not self.chefe_lider.get() or not self.chefe_faixa.get():  # Faixa também é importante
            messagebox.showerror(
                "Erro de Validação", "Nome do Chefe, Faixa Hierárquica e Líder Político são obrigatórios!")
            return

        try:
            id_lider_str = self.chefe_lider.get().split('-')[0].strip()
            id_lider = int(id_lider_str)
        except (ValueError, IndexError):
            messagebox.showerror(
                "Erro de Validação", "Formato do líder selecionado é inválido. Atualize a lista de líderes.")
            return

        cod_grupo_div = None
        num_div = None
        if self.chefe_divisao.get():
            try:
                div_parts = self.chefe_divisao.get().split('-')
                cod_grupo_div_str = div_parts[0].strip()
                cod_grupo_div = int(cod_grupo_div_str)

                # Extrai o número da divisão: "Divisão X (Nome Grupo)" -> "Divisão X " -> "X"
                num_div_str = div_parts[1].split(
                    '(')[0].replace("Divisão", "").strip()
                num_div = int(num_div_str)
            except (ValueError, IndexError):
                messagebox.showerror(
                    "Erro de Validação", "Formato da divisão selecionada é inválido. Atualize a lista de divisões.")
                return

        query = """INSERT INTO Chefe_Militar
                     (nome_chefe, faixa_hierarquica, id_lider_politico_obedece_fk,
                      cod_grupo_divisao_liderada_fk, num_divisao_liderada_fk)
                     VALUES (%s, %s, %s, %s, %s)"""
        params = (self.chefe_nome.get(), self.chefe_faixa.get(), id_lider,
                  cod_grupo_div, num_div)

        if self.execute_query(query, params, fetch=False):
            messagebox.showinfo(
                "Sucesso", "Chefe militar cadastrado com sucesso!")
            self.limpar_form_chefe()
        # else:
            # messagebox.showerror("Erro", "Falha ao cadastrar chefe militar.")

    # --- MÉTODOS AUXILIARES PARA LIMPAR FORMULÁRIOS ---
    def limpar_form_conflito(self):
        self.conflito_nome.set("")
        self.conflito_tipo.set("")
        self.conflito_mortos.set(0)
        self.conflito_feridos.set(0)
        if hasattr(self, 'paises_listbox'):
            self.paises_listbox.selection_clear(0, tk.END)
        if hasattr(self, 'grupos_listbox'):
            self.grupos_listbox.selection_clear(0, tk.END)
        if hasattr(self, 'religioes_listbox'):
            self.religioes_listbox.selection_clear(0, tk.END)
        if hasattr(self, 'materias_primas_listbox'):
            self.materias_primas_listbox.selection_clear(0, tk.END)
        if hasattr(self, 'etnias_listbox'):
            self.etnias_listbox.selection_clear(0, tk.END)
        self.handle_conflito_tipo_change()

    def limpar_form_grupo(self):
        self.grupo_nome.set("")
        self.grupo_lider.set("")
        self.grupo_apoios.delete("1.0", tk.END)
        # Limpa a seleção da listbox, o que também aciona o evento para limpar os campos de data
        self.conflitos_listbox_grupo.selection_clear(0, tk.END)
        self.conflitos_listbox_grupo.event_generate("<<ListboxSelect>>")

    def limpar_form_divisao(self):
        self.divisao_grupo.set("")
        self.divisao_barcos.set(0)
        self.divisao_tanques.set(0)
        self.divisao_avioes.set(0)
        self.divisao_homens.set(0)
        self.divisao_baixas.set(0)
        self.divisao_nome_chefe.set("")
        self.divisao_faixa_chefe.set("")
        self.divisao_lider_combo.set("")
        self.divisao_lider_combo['values'] = []

    def limpar_form_lider(self):
        self.lider_nome.set("")
        self.lider_grupo.set("")  # Limpa a seleção do combobox
        self.lider_apoios.delete("1.0", tk.END)

    def limpar_form_chefe(self):
        self.chefe_nome.set("")
        self.chefe_faixa.set("")
        self.chefe_lider.set("")  # Limpa a seleção do combobox
        self.chefe_divisao.set("")  # Limpa a seleção do combobox

    # --- MÉTODOS PARA ATUALIZAR COMBOS ---
    def atualizar_todos_os_combos(self):
        """Chama todas as funções de atualização de combos e listboxes."""
        if self.conn and not self.conn.closed:
            self.atualizar_grupos_combo_lider()
            self.atualizar_combos_chefes()
            self.atualizar_conflitos_listbox_grupo()
            self.handle_atualizar_divisao_listas()
            self.atualizar_paises_listbox()
            self.atualizar_religioes_listbox()
            self.atualizar_materias_primas_listbox()
            self.atualizar_etnias_listbox()
            self.atualizar_regioes_listbox()
            self.atualizar_grupos_listbox()
        else:
            print("Não é possível atualizar combos: Sem conexão com o banco.")

    def atualizar_grupos_combo_divisao(self):
        """Atualiza o combo de grupos na aba de divisões"""
        query = "SELECT cod_grupo, nome_grupo FROM Grupo_Armado ORDER BY nome_grupo"
        result = self.execute_query(query)
        if result and result[0]:  # result[0] contém as linhas
            grupos = [f"{row[0]} - {row[1]}" for row in result[0]]
            self.divisao_grupo['values'] = grupos
            if grupos:
                # Seleciona o primeiro por padrão
                self.divisao_grupo.current(0)
        else:
            self.divisao_grupo['values'] = []

    def atualizar_grupos_combo_lider(self):
        """Atualiza o combo de grupos na aba de líderes"""
        query = "SELECT cod_grupo, nome_grupo FROM Grupo_Armado ORDER BY nome_grupo"
        result = self.execute_query(query)
        if result and result[0]:
            grupos = [f"{row[0]} - {row[1]}" for row in result[0]]
            self.lider_grupo['values'] = grupos
            if grupos:
                self.lider_grupo.current(0)
        else:
            self.lider_grupo['values'] = []

    def atualizar_conflitos_listbox_grupo(self):
        """Atualiza a ListBox de conflitos na aba de cadastro de grupos."""
        # Limpa a lista e dispara o evento para limpar as entradas de data
        self.conflitos_listbox_grupo.delete(0, tk.END)
        self.conflitos_listbox_grupo.event_generate("<<ListboxSelect>>")

        query = "SELECT cod_conflito, nome_conflito FROM Conflito ORDER BY nome_conflito"
        result = self.execute_query(query)
        if result and result[0]:
            conflitos = [f"{row[0]} - {row[1]}" for row in result[0]]
            for c in conflitos:
                self.conflitos_listbox_grupo.insert(tk.END, c)

    def atualizar_entradas_data_conflito(self, event=None):
        """Cria campos de entrada de data dinamicamente com base nos conflitos selecionados."""
        # Limpa o frame de datas e o dicionário de widgets de entrada
        for widget in self.datas_frame.winfo_children():
            widget.destroy()
        self.date_entries.clear()

        # Obtém os índices e os textos dos itens selecionados na listbox
        indices_selecionados = self.conflitos_listbox_grupo.curselection()
        itens_selecionados = [self.conflitos_listbox_grupo.get(
            i) for i in indices_selecionados]

        if not itens_selecionados:
            ttk.Label(self.datas_frame, text="Selecione um ou mais conflitos na lista.").pack(
                padx=10, pady=10)
            return

        # Para cada conflito selecionado, cria um label e uma entrada de data
        for i, item_texto in enumerate(itens_selecionados):
            try:
                # Extrai o ID e o nome do conflito do texto do item
                cod_conflito = int(item_texto.split('-')[0].strip())
                nome_conflito = item_texto.split('-')[1].strip()

                # Cria um frame para cada linha (label + entry)
                row_frame = ttk.Frame(self.datas_frame)
                row_frame.pack(fill=tk.X, padx=5, pady=2)

                label = ttk.Label(
                    row_frame, text=f"{nome_conflito}:", width=30, anchor="w")
                label.pack(side=tk.LEFT)

                entry = ttk.Entry(row_frame, width=20)
                entry.pack(side=tk.LEFT)

                # Armazena o widget de entrada no dicionário usando o código do conflito como chave
                self.date_entries[cod_conflito] = entry
            except (ValueError, IndexError):
                # Ignora itens mal formatados se houver
                continue

    def atualizar_combos_chefes(self):
        """Atualiza os combos na aba de chefes militares (Líderes e Divisões)"""
        # Atualizar Líderes
        query_lideres = """
            SELECT lp.id_lider_politico, lp.nome_lider, ga.nome_grupo
            FROM Lider_Politico lp
            JOIN Grupo_Armado ga ON lp.cod_grupo_liderado_fk = ga.cod_grupo
            ORDER BY lp.nome_lider
        """
        result_lideres = self.execute_query(query_lideres)
        if result_lideres and result_lideres[0]:
            lideres = [
                f"{row[0]} - {row[1]} ({row[2]})" for row in result_lideres[0]]
            self.chefe_lider['values'] = lideres
            if lideres:
                self.chefe_lider.current(0)
        else:
            self.chefe_lider['values'] = []

        # Atualizar Divisões
        query_divisoes = """
            SELECT d.cod_grupo_fk, d.num_divisao, ga.nome_grupo
            FROM Divisao d
            JOIN Grupo_Armado ga ON d.cod_grupo_fk = ga.cod_grupo
            ORDER BY ga.nome_grupo, d.num_divisao
        """
        result_divisoes = self.execute_query(query_divisoes)
        if result_divisoes and result_divisoes[0]:
            divisoes = [
                f"{row[0]} - Divisão {row[1]} ({row[2]})" for row in result_divisoes[0]]
            self.chefe_divisao['values'] = divisoes
            if divisoes:
                self.chefe_divisao.current(0)
        else:
            self.chefe_divisao['values'] = []

    def atualizar_lideres_para_divisao(self, event=None):
        """Filtra e atualiza o combo de líderes na aba de divisões com base no grupo selecionado."""
        if not self.divisao_grupo.get():
            self.divisao_lider_combo['values'] = []
            return

        try:
            cod_grupo_str = self.divisao_grupo.get().split('-')[0].strip()
            cod_grupo = int(cod_grupo_str)
        except (ValueError, IndexError):
            self.divisao_lider_combo['values'] = []
            return

        query = "SELECT id_lider_politico, nome_lider FROM Lider_Politico WHERE cod_grupo_liderado_fk = %s ORDER BY nome_lider"
        result = self.execute_query(query, (cod_grupo,))

        if result and result[0]:
            lideres = [f"{row[0]} - {row[1]}" for row in result[0]]
            self.divisao_lider_combo['values'] = lideres
            if lideres:
                self.divisao_lider_combo.current(0)
        else:
            self.divisao_lider_combo['values'] = []
            self.divisao_lider_combo.set("")

    def handle_atualizar_divisao_listas(self):
        """
        Função intermediária para o botão 'Atualizar Listas' da aba Divisões.
        Atualiza a lista de grupos e, em seguida, a lista de líderes baseada no grupo selecionado.
        """
        # 1. Atualiza a lista de grupos. Isso vai selecionar o primeiro item por padrão.
        self.atualizar_grupos_combo_divisao()

        # 2. Em seguida, atualiza a lista de líderes, que depende do grupo agora selecionado.
        self.atualizar_lideres_para_divisao()

    def atualizar_grupos_listbox(self):
        """Atualiza o Listbox de grupos armados na aba de conflitos."""
        self.grupos_listbox.delete(0, tk.END)
        query = "SELECT cod_grupo, nome_grupo FROM Grupo_Armado ORDER BY nome_grupo"
        result = self.execute_query(query)
        if result and result[0]:
            for row in result[0]:
                self.grupos_listbox.insert(tk.END, f"{row[0]} - {row[1]}")

    def atualizar_paises_listbox(self):
        """Atualiza o Listbox de países na aba de conflitos."""
        # Limpa a lista antes de preencher
        self.paises_listbox.delete(0, tk.END)

        query = "SELECT cod_pais, nome_pais FROM Pais ORDER BY nome_pais"
        result = self.execute_query(query)

        if result and result[0]:
            self.lista_de_paises = result[0]  # Armazena para referência futura
            for cod_pais, nome_pais in self.lista_de_paises:
                self.paises_listbox.insert(tk.END, f"{cod_pais} - {nome_pais}")
        else:
            self.lista_de_paises = []

    def atualizar_regioes_listbox(self):
        """Atualiza o Listbox de regiões."""
        self.regioes_listbox.delete(0, tk.END)
        query = "SELECT id_regiao, nome_regiao FROM Regiao ORDER BY nome_regiao"
        result = self.execute_query(query)
        if result and result[0]:
            for row in result[0]:
                self.regioes_listbox.insert(tk.END, f"{row[0]} - {row[1]}")

    def atualizar_religioes_listbox(self):
        """Atualiza o Listbox de religiões."""
        self.religioes_listbox.delete(0, tk.END)
        query = "SELECT id_religiao, nome_religiao FROM Religiao_Entidade ORDER BY nome_religiao"
        result = self.execute_query(query)
        if result and result[0]:
            for row in result[0]:
                self.religioes_listbox.insert(tk.END, f"{row[0]} - {row[1]}")

    def atualizar_materias_primas_listbox(self):
        """Atualiza o Listbox de matérias-primas."""
        self.materias_primas_listbox.delete(0, tk.END)
        query = "SELECT id_materia_prima, nome_materia_prima FROM Materia_Prima ORDER BY nome_materia_prima"
        result = self.execute_query(query)
        if result and result[0]:
            for row in result[0]:
                self.materias_primas_listbox.insert(
                    tk.END, f"{row[0]} - {row[1]}")

    def atualizar_etnias_listbox(self):
        """Atualiza o Listbox de etnias."""
        self.etnias_listbox.delete(0, tk.END)
        query = "SELECT id_etnia, nome_etnia FROM Etnia ORDER BY nome_etnia"
        result = self.execute_query(query)
        if result and result[0]:
            for row in result[0]:
                self.etnias_listbox.insert(tk.END, f"{row[0]} - {row[1]}")

    def handle_conflito_tipo_change(self, event=None):
        """Mostra ou esconde os frames de detalhes com base no tipo de conflito selecionado."""
        selected_type = self.conflito_tipo.get()

        # Primeiro, esconde todos os frames de detalhes
        self.frame_conflito_territorial.grid_remove()
        self.frame_conflito_religioso.grid_remove()
        self.frame_conflito_economico.grid_remove()
        self.frame_conflito_racial.grid_remove()

        # Depois, mostra o frame correto
        if selected_type == 'territorial':
            self.frame_conflito_territorial.grid()
        elif selected_type == 'religioso':
            self.frame_conflito_religioso.grid()
        elif selected_type == 'economico':
            self.frame_conflito_economico.grid()
        elif selected_type == 'racial':
            self.frame_conflito_racial.grid()

    # --- MÉTODOS DE RELATÓRIOS ---

    def limpar_result_frame(self):
        """Limpa o frame de resultados"""
        for widget in self.result_frame.winfo_children():
            widget.destroy()

    def exibir_resultados_tabela(self, data, columns):
        """Exibe os resultados em uma Treeview."""
        self.limpar_result_frame()
        if not data:
            ttk.Label(self.result_frame, text="Nenhum resultado encontrado.").pack(
                padx=10, pady=10)
            return

        tree_frame = ttk.Frame(self.result_frame)
        tree_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        tree_scroll_y = ttk.Scrollbar(tree_frame, orient=tk.VERTICAL)
        tree_scroll_x = ttk.Scrollbar(tree_frame, orient=tk.HORIZONTAL)

        # Estilo para o Treeview
        style = ttk.Style()
        style.configure("Treeview",
                        background="#3C3C3C",  # Fundo da área de dados
                        foreground="#FFFFFF",  # Cor do texto dos dados
                        # Fundo da área de dados (geralmente o mesmo do background)
                        fieldbackground="#3C3C3C",
                        bordercolor="#4A4A4A")  # Cor da borda
        style.map("Treeview", background=[
                  ('selected', '#5C5C5C')])  # Cor de seleção

        style.configure("Treeview.Heading",
                        background="#4A4A4A",  # Fundo do cabeçalho
                        foreground="#FFFFFF",  # Cor do texto do cabeçalho
                        font=('Arial', 10, 'bold'))
        style.map("Treeview.Heading", background=[('active', '#5A5A5A')])

        tree = ttk.Treeview(tree_frame, columns=columns, show='headings',
                            yscrollcommand=tree_scroll_y.set, xscrollcommand=tree_scroll_x.set)

        tree_scroll_y.config(command=tree.yview)
        tree_scroll_x.config(command=tree.xview)

        tree_scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        tree_scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        tree.pack(fill=tk.BOTH, expand=True)

        # Usar enumerate para ter índice e nome
        for col_idx, col_name in enumerate(columns):
            tree.heading(col_name, text=col_name)
            tree.column(col_name, anchor=tk.W, width=150)

        for row in data:
            tree.insert("", tk.END, values=row)

    def grafico_tipos_conflito(self):
        """Gera gráfico por tipo de conflito"""
        self.limpar_result_frame()
        query = """
            SELECT 'Territorial' AS tipo, COUNT(*) AS numero FROM Conflito_Territorial
            UNION ALL
            SELECT 'Religioso' AS tipo, COUNT(*) AS numero FROM Conflito_Religioso
            UNION ALL
            SELECT 'Econômico' AS tipo, COUNT(*) AS numero FROM Conflito_Economico
            UNION ALL
            SELECT 'Racial' AS tipo, COUNT(*) AS numero FROM Conflito_Racial;
        """
        result = self.execute_query(query)
        if result and result[0]:
            data, _ = result
            df = pd.DataFrame(
                data, columns=['Tipo de Conflito', 'Número de Conflitos'])

            if df.empty or df['Número de Conflitos'].sum() == 0:
                ttk.Label(self.result_frame, text="Não há dados suficientes para gerar o gráfico.").pack(
                    padx=10, pady=10)
                return

            # Configurações para o gráfico Matplotlib
            plt.style.use('dark_background')  # Tema escuro para o Matplotlib
            fig, ax = plt.subplots(figsize=(8, 6))
            df.plot(kind='bar', x='Tipo de Conflito', y='Número de Conflitos', ax=ax, legend=False,
                    color=['skyblue', 'lightcoral', 'lightgreen', 'gold'])
            ax.set_title('Número de Conflitos por Tipo', color='white')
            ax.set_xlabel('Tipo de Conflito', color='white')
            ax.set_ylabel('Número de Conflitos', color='white')
            # Cor dos ticks do eixo X
            ax.tick_params(axis='x', rotation=45, colors='white')
            ax.tick_params(axis='y', colors='white')  # Cor dos ticks do eixo Y
            # Cor dos spines (bordas do gráfico)
            ax.spines['bottom'].set_color('white')
            ax.spines['top'].set_color('white')
            ax.spines['right'].set_color('white')
            ax.spines['left'].set_color('white')

            for container in ax.containers:  # Adiciona os valores no topo das barras
                # Cor dos labels nas barras
                ax.bar_label(container, color='white')
            plt.tight_layout()

            canvas = FigureCanvasTkAgg(fig, master=self.result_frame)
            canvas_widget = canvas.get_tk_widget()
            canvas_widget.pack(fill=tk.BOTH, expand=True)
            canvas.draw()
        # Se result não é None, mas result[0] está vazio (nenhum tipo de conflito existe)
        elif result is not None:
            ttk.Label(self.result_frame, text="Nenhum conflito cadastrado para gerar o gráfico.").pack(
                padx=10, pady=10)
        # Se result for None, execute_query já mostrou o erro

    def relatorio_traficantes_barrett(self):
        """i. Listar os traficantes e os grupos armados (Nome) para os quais os traficantes
              fornecem armas “Barrett M82” ou “M200 Intervention”."""
        query = """
            SELECT DISTINCT t.nome_traficante, ga.nome_grupo
            FROM Traficante_Armas t
            JOIN Fornecimento_Arma_Grupo fag ON t.id_traficante = fag.id_traficante_fk
            JOIN Grupo_Armado ga ON fag.cod_grupo_fk = ga.cod_grupo
            WHERE fag.nome_arma_fk IN ('Barrett M82', 'M200 Intervention')
            ORDER BY t.nome_traficante, ga.nome_grupo;
        """
        result = self.execute_query(query)
        if result:  # execute_query retorna (dados, colunas) ou None
            data, columns = result
            # Garante que 'columns' não seja None, mesmo que não haja descrição (improvável aqui)
            self.exibir_resultados_tabela(data, columns if columns else [
                                          "Traficante", "Grupo Armado"])
        # Se result for None, execute_query já mostrou o erro. Se data for [], exibir_resultados_tabela trata.

    def relatorio_top_conflitos_mortos(self):
        """ii. Listar os 5 maiores conflitos em número de mortos."""
        query = """
            SELECT nome_conflito, num_mortos_atual
            FROM Conflito
            ORDER BY num_mortos_atual DESC
            LIMIT 5;
        """
        result = self.execute_query(query)
        if result:
            data, columns = result
            self.exibir_resultados_tabela(data, columns if columns else [
                                          "Conflito", "Número de Mortos"])

    def relatorio_top_organizacoes(self):
        """iii. Listar as 5 maiores organizações em número de mediações."""
        query = """
            SELECT om.nome_org, COUNT(oic.cod_conflito_fk) AS numero_mediacoes
            FROM Organizacao_Mediadora om
            LEFT JOIN Organizacao_Intervem_Conflito oic ON om.cod_org = oic.cod_org_fk
            GROUP BY om.nome_org
            ORDER BY numero_mediacoes DESC
            LIMIT 5;
        """  # Usar LEFT JOIN para incluir organizações sem mediações, se desejado (teriam 0)
        # Se só as com mediações, INNER JOIN (ou apenas JOIN) é ok. O problema pede "em número de mediações",
        # então as com 0 podem não ser relevantes para "maiores". O COUNT(oic.cod_conflito_fk) já lida com isso.
        result = self.execute_query(query)
        if result:
            data, columns = result
            self.exibir_resultados_tabela(data, columns if columns else [
                                          "Organização", "Número de Mediações"])

    def relatorio_top_grupos_armas(self):
        """iv. Listar os 5 maiores grupos armados com maior número de armas fornecidas."""
        query = """
            SELECT ga.nome_grupo, COALESCE(SUM(fag.quantidade_fornecida), 0) AS total_armas_recebidas
            FROM Grupo_Armado ga
            LEFT JOIN Fornecimento_Arma_Grupo fag ON ga.cod_grupo = fag.cod_grupo_fk
            GROUP BY ga.nome_grupo
            ORDER BY total_armas_recebidas DESC
            LIMIT 5;
        """  # Usar LEFT JOIN e COALESCE para incluir grupos que não receberam armas (com 0 armas)
        # se eles devem ser considerados para o "top 5" (embora com 0 não ficariam no topo).
        result = self.execute_query(query)
        if result:
            data, columns = result
            self.exibir_resultados_tabela(data, columns if columns else [
                                          "Grupo Armado", "Total de Armas Recebidas"])

    def relatorio_paises_religiosos(self):
        """v. Listar o país e número de conflitos com maior número de conflitos religiosos."""
        # Esta query encontra os países empatados no topo
        query = """
            WITH ConflitosReligiososPorPais AS (
                SELECT
                    p.nome_pais,
                    COUNT(DISTINCT cr.cod_conflito_fk) AS numero_conflitos_religiosos
                FROM Pais p
                JOIN Conflito_Afeta_Pais cap ON p.cod_pais = cap.cod_pais_fk
                JOIN Conflito c ON cap.cod_conflito_fk = c.cod_conflito
                JOIN Conflito_Religioso cr ON c.cod_conflito = cr.cod_conflito_fk
                GROUP BY p.nome_pais
            ),
            MaxConflitosReligiosos AS (
                SELECT MAX(numero_conflitos_religiosos) AS max_cr
                FROM ConflitosReligiososPorPais
                WHERE numero_conflitos_religiosos > 0 -- Adicionado para garantir que haja pelo menos um
            )
            SELECT crpp.nome_pais, crpp.numero_conflitos_religiosos
            FROM ConflitosReligiososPorPais crpp, MaxConflitosReligiosos mcr
            WHERE crpp.numero_conflitos_religiosos = mcr.max_cr AND crpp.numero_conflitos_religiosos > 0
            ORDER BY crpp.nome_pais;
        """
        result = self.execute_query(query)
        if result:
            data, columns = result
            self.exibir_resultados_tabela(data, columns if columns else [
                                          "País", "Número de Conflitos Religiosos"])


if __name__ == '__main__':
    root = tk.Tk()
    app = ConflictosBelicosApp(root)
    root.mainloop()
