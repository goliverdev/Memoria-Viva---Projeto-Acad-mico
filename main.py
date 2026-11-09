# memoria_viva_app.py
# -*- coding: utf-8 -*-
"""
Memória Viva - Aplicativo Flet
Integra com database.py e emocao.py
"""

import asyncio
import sys


def _silenciar_erro_conexao_fechada(loop, context):
    excecao = context.get("exception")
    if isinstance(excecao, (ConnectionResetError, ConnectionAbortedError)):
        return
    loop.default_exception_handler(context)

if sys.platform.startswith("win"):
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:
        pass

_loop_original_new_event_loop = asyncio.new_event_loop

def _novo_loop_silencioso():
    loop = _loop_original_new_event_loop()
    loop.set_exception_handler(_silenciar_erro_conexao_fechada)
    return loop

asyncio.new_event_loop = _novo_loop_silencioso

import flet as ft
from database import (
    conectar, criar_banco, cadastrar_usuario, fazer_login, atualizar_usuario,
    salvar_memoria as db_salvar_memoria,
    buscar_memorias, buscar_memorias_publicas, pesquisar_memoria, editar_memoria, excluir_memoria
)
from emocao import analisar_texto, analisar_emocao

# Cores do tema
CORES = {
    "musgo": "#152019",
    "musgo_2": "#1c2b21",
    "floresta": "#2E5339",
    "floresta_clara": "#6FA37F",
    "floresta_viva": "#3E7052",
    "pergaminho": "#F6EFDD",
    "pergaminho_2": "#FBF7EE",
    "dourado": "#D8AE6B",
    "dourado_forte": "#C8933E",
    "vinho": "#7A3B46",
    "vinho_claro": "#9C5665",
    "tinta": "#26332B",
    "tinta_suave": "#5C6B63",
}

EMOCOES = {
    "alegria": {"label": "Alegria", "emoji": "😊", "cor": "#F2B705"},
    "tristeza": {"label": "Tristeza", "emoji": "😢", "cor": "#1E3A5F"},
    "raiva": {"label": "Raiva", "emoji": "😡", "cor": "#D62828"},
    "medo": {"label": "Medo", "emoji": "😨", "cor": "#8B6BB5"},
    "nojo": {"label": "Nojo", "emoji": "🤢", "cor": "#4CAF50"},
    "ansiedade": {"label": "Ansiedade", "emoji": "😰", "cor": "#F57C00"},
    "inveja": {"label": "Inveja", "emoji": "🩵", "cor": "#2FA9BD"},
    "tedio": {"label": "Tédio", "emoji": "😒", "cor": "#4527A0"},
    "vergonha": {"label": "Vergonha", "emoji": "😳", "cor": "#C2185B"},
    "nostalgia": {"label": "Nostalgia", "emoji": "🤎", "cor": "#8D6E63"},
    "orgulho": {"label": "Orgulho", "emoji": "🥲", "cor": "#00695C"},
    "gratidao": {"label": "Gratidão", "emoji": "🙏", "cor": "#C77D2E"},
}

CATEGORIAS = ["Família", "Viagem", "Infância", "Escola", "Trabalho", 
             "Amigos", "Conquistas", "Perdas", "Saúde", "Relacionamento", "Momentos especiais"]

USUARIOS_DEMO = [
    {"id": 1, "nome": "Gabriel Augusto", "email": "gabriel@memoriaviva.app", "avatar": "🧔"},
]


class MemoriaVivaApp:
    def __init__(self):
        self.user = None
        self.memorias_cache = []
        self.memorias_publicas_cache = []
        self.explorar_modo = "minhas"
        self.explorar_prefiltro_emocao = None
        self.selected_memoria_id = None
        self.selected_memoria_publica = False
        self.nova_emocao = None
        self.theme = "light"
        
        # Criar banco de dados se não existir
        criar_banco()
        self.seed_usuarios_demo()

    def seed_usuarios_demo(self):
        """Garante que os usuários de demonstração existam no banco"""
        for u in USUARIOS_DEMO:
            cadastrar_usuario(u["nome"], u["email"], "123456", u["avatar"])

    def main(self, page: ft.Page):
        self.page = page
        page.title = "🌳 Memória Viva"
        page.window.width = 400
        page.window.height = 780
        page.window.min_width = 360
        page.window.min_height = 600
        page.theme_mode = ft.ThemeMode.LIGHT
        page.bgcolor = CORES["pergaminho"]
        page.padding = 0
        page.fonts = {
            "Fraunces": "https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300;0,9..144,500;0,9..144,600;0,9..144,700;1,9..144,500&display=swap",
            "Manrope": "https://fonts.googleapis.com/css2?family=Manrope:wght@400;500;600;700;800&display=swap",
        }
        
        self.page.on_route_change = self.route_change
        
        # Container principal
        self.main_container = ft.Container(
            expand=True,
            bgcolor=page.bgcolor,
            padding=ft.padding.all(0),
        )
        
        # Stack para telas
        self.screens = ft.Stack(expand=True)
        self.main_container.content = self.screens
        page.add(self.main_container)
        
        # Inicializar telas
        self.splash_screen = self.create_splash_screen()
        self.login_screen = self.create_login_screen()
        self.cadastro_screen = self.create_cadastro_screen()
        self.home_screen = self.create_home_screen()
        self.explorar_screen = self.create_explorar_screen()
        self.nova_screen = self.create_nova_screen()
        self.memoria_screen = self.create_memoria_screen()
        self.perfil_screen = self.create_perfil_screen()
        
        # Camada própria para diálogos (confirmar exclusão, editar perfil).
        # Não usamos ft.AlertDialog/page.dialog porque essa versão do Flet
        # tem se mostrado instável com eles (tela ficando em branco ao
        # fechar). Em vez disso, usamos o mesmo mecanismo de
        # visible/opacity que já funciona de forma confiável no resto do
        # app para trocar de tela.
        self.modal_content_holder = ft.Container(alignment=ft.alignment.center)
        self.modal_overlay = ft.Container(
            expand=True,
            bgcolor="#00000099",
            alignment=ft.alignment.center,
            visible=False,
            opacity=1,
            content=self.modal_content_holder,
        )
        
        # Adicionar telas ao stack (o modal por último, para ficar por cima)
        self.screens.controls.extend([
            self.splash_screen,
            self.login_screen,
            self.cadastro_screen,
            self.home_screen,
            self.explorar_screen,
            self.nova_screen,
            self.memoria_screen,
            self.perfil_screen,
            self.modal_overlay,
        ])
        
        # Mostrar splash inicial
        self.show_screen("splash")
        self.run_splash_animation()

    def abrir_modal(self, conteudo):
        """Exibe um card centralizado sobre a tela atual (usado para
        confirmações e formulários rápidos, como excluir ou editar perfil)."""
        self.modal_content_holder.content = ft.Container(
            width=320,
            padding=ft.padding.all(20),
            bgcolor=ft.Colors.WHITE,
            border_radius=20,
            content=conteudo,
        )
        self.modal_overlay.opacity = 1
        self.modal_overlay.visible = True
        self.page.update()

    def fechar_modal(self):
        """Esconde o modal e volta a mostrar a tela normalmente."""
        self.modal_overlay.visible = False
        self.page.update()

    def create_screen_container(self, name):
        """Cria um container para cada tela"""
        return ft.Container(
            expand=True,
            bgcolor=self.page.bgcolor,
            padding=ft.padding.only(top=20, left=16, right=16, bottom=16),
            opacity=0,
            animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN_OUT),
            data=name,
        )

    # ==================== SPLASH ====================
    def create_splash_screen(self):
        container = self.create_screen_container("splash")
        container.content = ft.Column(
            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
            alignment=ft.MainAxisAlignment.CENTER,
            spacing=20,
            controls=[
                ft.Text("🌱", size=60, animate_size=ft.Animation(500, ft.AnimationCurve.EASE_OUT)),
                ft.Text(
                    "MEMÓRIA VIVA",
                    size=28,
                    weight=ft.FontWeight.BOLD,
                    font_family="Fraunces",
                    color=CORES["floresta"],
                    opacity=0,
                    animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN),
                ),
                ft.Text(
                    '"Porque toda história merece continuar viva."',
                    size=14,
                    color=CORES["tinta_suave"],
                    font_family="Fraunces",
                    italic=True,
                    opacity=0,
                    animate_opacity=ft.Animation(600, ft.AnimationCurve.EASE_IN),
                ),
                ft.ProgressRing(
                    width=24, height=24,
                    color=CORES["dourado"],
                    opacity=0,
                    animate_opacity=ft.Animation(400, ft.AnimationCurve.EASE_IN),
                )
            ]
        )
        return container

    def run_splash_animation(self):
        """Anima a tela de splash"""
        def animate():
            import time
            container = self.splash_screen
            tree = container.content.controls[0]
            title = container.content.controls[1]
            slogan = container.content.controls[2]
            ring = container.content.controls[3]
            
            time.sleep(0.3)
            tree.size = 68
            tree.update()
            
            time.sleep(0.5)
            tree.value = "🌿"
            tree.size = 74
            tree.update()
            
            time.sleep(0.3)
            title.opacity = 1
            title.update()
            
            time.sleep(0.3)
            slogan.opacity = 1
            slogan.update()
            
            time.sleep(0.2)
            ring.opacity = 1
            ring.update()
            
            time.sleep(0.3)
            tree.value = "🌳"
            tree.size = 90
            tree.update()
            
            time.sleep(0.8)
            self.show_screen("login")
        
        self.page.run_thread(animate)

    # ==================== LOGIN ====================
    def create_login_screen(self):
        container = self.create_screen_container("login")
        
        # Demo users
        demo_users = ft.Row(
            spacing=8,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        for u in USUARIOS_DEMO:
            avatar = ft.Container(
                content=ft.Text(u["avatar"], size=22),
                width=44, height=44,
                border_radius=22,
                bgcolor=CORES["floresta"] + "22",
                border=ft.border.all(1.5, CORES["floresta_clara"] + "44"),
                on_click=lambda e, email=u["email"]: self.preencher_login(email),
            )
            demo_users.controls.append(
                ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        avatar,
                        ft.Text(u["nome"].split()[0], size=9, color=CORES["tinta_suave"])
                    ]
                )
            )
        
        container.content = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Container(
                width=340,
                padding=ft.padding.all(28),
                bgcolor=ft.Colors.WHITE,
                border_radius=26,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=30,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=16,
                    controls=[
                        ft.Text("🌳", size=44),
                        ft.Text("MEMÓRIA VIVA", size=22, weight=ft.FontWeight.BOLD, font_family="Fraunces"),
                        ft.Text("Entre para continuar sua história.", size=13, color=CORES["tinta_suave"]),
                        
                        ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Text("Acessar como:", size=11, color=CORES["tinta_suave"], weight=ft.FontWeight.W_600),
                                demo_users,
                            ]
                        ),
                        
                        ft.Divider(height=1, color=CORES["floresta"] + "22"),
                        
                        ft.TextField(
                            label="E-mail",
                            hint_text="voce@memoriaviva.app",
                            prefix_icon=ft.Icons.EMAIL,
                            value="carlos@memoriaviva.app",
                            text_size=14,
                            height=50,
                            border_radius=14,
                            border_color=CORES["floresta"] + "33",
                            focused_border_color=CORES["floresta_clara"],
                            on_change=self.clear_login_error,
                        ),
                        ft.TextField(
                            label="Senha",
                            hint_text="••••••",
                            prefix_icon=ft.Icons.LOCK,
                            value="123456",
                            password=True,
                            can_reveal_password=True,
                            text_size=14,
                            height=50,
                            border_radius=14,
                            border_color=CORES["floresta"] + "33",
                            focused_border_color=CORES["floresta_clara"],
                            on_change=self.clear_login_error,
                        ),
                        ft.Text("", size=12, color=CORES["vinho"], data="login_err"),
                        
                        ft.ElevatedButton(
                            "Entrar",
                            width=280,
                            height=50,
                            bgcolor=CORES["floresta_viva"],
                            color=ft.Colors.WHITE,
                            style=ft.ButtonStyle(
                                shape=ft.RoundedRectangleBorder(radius=16),
                            ),
                            on_click=self.do_login,
                        ),
                        
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=4,
                            controls=[
                                ft.Text("Não tem conta?", size=13, color=CORES["tinta_suave"]),
                                ft.TextButton(
                                    "Criar conta",
                                    style=ft.ButtonStyle(
                                        color=CORES["dourado_forte"],
                                        text_style=ft.TextStyle(weight=ft.FontWeight.BOLD),
                                    ),
                                    on_click=lambda e: self.show_screen("cadastro"),
                                )
                            ]
                        )
                    ]
                )
            )
        )
        return container

    def preencher_login(self, email):
        """Preenche o campo de email com o usuário demo selecionado"""
        email_field = self.login_screen.content.content.content.controls[5]
        email_field.value = email
        self.page.update()

    def clear_login_error(self, e):
        err = self.login_screen.content.content.content.controls[7]
        err.value = ""
        err.update()

    def do_login(self, e):
        container = self.login_screen.content.content.content
        email = container.controls[5].value
        senha = container.controls[6].value
        err = container.controls[7]
        
        if not email or not senha:
            err.value = "⚠️ Preencha todos os campos."
            err.color = CORES["vinho"]
            self.page.update()
            return
        
        usuario = fazer_login(email, senha)
        if usuario:
            self.user = {
                "id": usuario[0],
                "nome": usuario[1],
                "email": usuario[2],
                "avatar": usuario[4] if len(usuario) > 4 and usuario[4] else "🙂",
                "data_cadastro": usuario[5] if len(usuario) > 5 and usuario[5] else "",
            }
            self.carregar_memorias()
            err.value = ""
            self.show_screen("home")
            self.toast(f"🌿 Bem-vindo(a), {usuario[1].split()[0]}!")
        else:
            err.value = "⚠️ E-mail ou senha incorretos."
            err.color = CORES["vinho"]
            self.page.update()

    # ==================== CADASTRO ====================
    def create_cadastro_screen(self):
        container = self.create_screen_container("cadastro")
        
        AVATARES_CADASTRO = ["🙂", "🌿", "🌳", "🍃", "🌸", "🌻", "🧔", "👩‍🎓", "🧑"]
        self.cadastro_avatar_escolhido = {"valor": AVATARES_CADASTRO[0]}
        self.cadastro_avatar_botoes = []
        
        def escolher_avatar_cadastro(av):
            self.cadastro_avatar_escolhido["valor"] = av
            for btn in self.cadastro_avatar_botoes:
                selecionado = btn.data == av
                btn.bgcolor = CORES["dourado"] if selecionado else CORES["floresta"] + "11"
            self.page.update()
        
        avatar_row_cadastro = ft.Row(spacing=8, wrap=True, alignment=ft.MainAxisAlignment.CENTER, controls=[])
        for av in AVATARES_CADASTRO:
            btn = ft.Container(
                content=ft.Text(av, size=18),
                width=38, height=38,
                border_radius=19,
                alignment=ft.alignment.center,
                bgcolor=CORES["dourado"] if av == self.cadastro_avatar_escolhido["valor"] else CORES["floresta"] + "11",
                data=av,
                on_click=lambda e, a=av: escolher_avatar_cadastro(a),
            )
            self.cadastro_avatar_botoes.append(btn)
            avatar_row_cadastro.controls.append(btn)
        
        self.cadastro_nome_field = ft.TextField(
            label="Nome",
            hint_text="Seu nome completo",
            prefix_icon=ft.Icons.PERSON,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        self.cadastro_email_field = ft.TextField(
            label="E-mail",
            hint_text="voce@email.com",
            prefix_icon=ft.Icons.EMAIL,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        self.cadastro_senha_field = ft.TextField(
            label="Senha",
            hint_text="••••••",
            prefix_icon=ft.Icons.LOCK,
            password=True,
            can_reveal_password=True,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        self.cadastro_confirma_field = ft.TextField(
            label="Confirmar senha",
            hint_text="••••••",
            prefix_icon=ft.Icons.LOCK_OUTLINE,
            password=True,
            can_reveal_password=True,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        self.cadastro_err_text = ft.Text("", size=12, color=CORES["vinho"])
        
        container.content = ft.Container(
            expand=True,
            alignment=ft.alignment.center,
            content=ft.Column(
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                controls=[
                    ft.Row(
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.ARROW_BACK,
                                icon_color=CORES["floresta"],
                                on_click=lambda e: self.show_screen("login"),
                            ),
                        ]
                    ),
                    ft.Container(
                        width=340,
                        padding=ft.padding.all(24),
                        bgcolor=ft.Colors.WHITE,
                        border_radius=26,
                        shadow=ft.BoxShadow(
                            spread_radius=0,
                            blur_radius=30,
                            color=ft.Colors.BLACK12,
                        ),
                        content=ft.Column(
                            horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                            spacing=12,
                            controls=[
                                ft.Text("🌱", size=38),
                                ft.Text("Criar Conta", size=22, weight=ft.FontWeight.BOLD, font_family="Fraunces"),
                                ft.Text("Comece a plantar sua árvore das memórias.", size=12, color=CORES["tinta_suave"]),
                                
                                self.cadastro_nome_field,
                                self.cadastro_email_field,
                                self.cadastro_senha_field,
                                self.cadastro_confirma_field,
                                
                                ft.Text("Escolha seu avatar", size=12, weight=ft.FontWeight.W_600, color=CORES["tinta_suave"]),
                                avatar_row_cadastro,
                                
                                self.cadastro_err_text,
                                
                                ft.ElevatedButton(
                                    "Criar conta 🌟",
                                    width=280,
                                    height=48,
                                    bgcolor=CORES["floresta_viva"],
                                    color=ft.Colors.WHITE,
                                    style=ft.ButtonStyle(
                                        shape=ft.RoundedRectangleBorder(radius=16),
                                    ),
                                    on_click=self.do_cadastro,
                                ),
                                
                                ft.TextButton(
                                    "Já tenho conta",
                                    style=ft.ButtonStyle(
                                        color=CORES["tinta_suave"],
                                    ),
                                    on_click=lambda e: self.show_screen("login"),
                                )
                            ]
                        )
                    )
                ]
            )
        )
        return container

    def do_cadastro(self, e):
        nome = self.cadastro_nome_field.value
        email = self.cadastro_email_field.value
        senha = self.cadastro_senha_field.value
        confirma = self.cadastro_confirma_field.value
        avatar = self.cadastro_avatar_escolhido["valor"]
        err = self.cadastro_err_text
        
        if not nome or not email or not senha:
            err.value = "⚠️ Preencha todos os campos."
            self.page.update()
            return
        
        if senha != confirma:
            err.value = "⚠️ As senhas não coincidem."
            self.page.update()
            return
        
        if len(senha) < 4:
            err.value = "⚠️ A senha deve ter pelo menos 4 caracteres."
            self.page.update()
            return
        
        if cadastrar_usuario(nome, email, senha, avatar):
            err.value = ""
            self.toast("🌱 Conta criada com sucesso!")
            self.show_screen("login")
            # Preencher login com o novo usuário
            email_field = self.login_screen.content.content.content.controls[5]
            email_field.value = email
            self.page.update()
        else:
            err.value = "⚠️ Este e-mail já está cadastrado."
            self.page.update()

    # ==================== HOME ====================
    def create_home_screen(self):
        container = self.create_screen_container("home")
        
        # Conteúdo dinâmico
        self.home_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        # NavBar
        self.home_nav = self.create_navbar("home")
        
        container.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    content=self.home_content,
                    padding=ft.padding.only(top=8, left=16, right=16, bottom=8),
                ),
                self.home_nav,
            ]
        )
        return container

    def create_navbar(self, active):
        """Cria a barra de navegação"""
        items = [
            {"key": "home", "icon": "🏠", "label": "início"},
            {"key": "explorar", "icon": "🔎", "label": "explorar"},
            {"key": "nova", "icon": "✧", "label": "novo", "fab": True},
            {"key": "perfil", "icon": "🙂", "label": "perfil"},
        ]
        
        row = ft.Row(
            alignment=ft.MainAxisAlignment.SPACE_AROUND,
            vertical_alignment=ft.CrossAxisAlignment.CENTER,
            spacing=0,
        )
        
        for item in items:
            is_active = item["key"] == active
            is_fab = item.get("fab", False)
            
            if is_fab:
                btn = ft.Container(
                    content=ft.Text(item["icon"], size=28),
                    width=52, height=52,
                    gradient=ft.LinearGradient(
                        begin=ft.alignment.top_left,
                        end=ft.alignment.bottom_right,
                        colors=[CORES["dourado"], CORES["dourado_forte"]],
                    ),
                    border_radius=26,
                    alignment=ft.alignment.center,
                    margin=ft.margin.only(top=-28),
                    shadow=ft.BoxShadow(
                        spread_radius=0,
                        blur_radius=20,
                        color=CORES["dourado"] + "66",
                    ),
                    on_click=lambda e, k=item["key"]: self.show_screen(k),
                )
                row.controls.append(btn)
            else:
                btn = ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=2,
                    controls=[
                        ft.Text(item["icon"], size=20),
                        ft.Text(item["label"], size=9, weight=ft.FontWeight.W_700),
                    ]
                )
                container = ft.Container(
                    content=btn,
                    padding=ft.padding.only(top=4, bottom=4, left=12, right=12),
                    border_radius=14,
                    on_click=lambda e, k=item["key"]: self.show_screen(k),
                )
                if is_active:
                    btn.controls[0].color = CORES["floresta_viva"]
                    btn.controls[1].color = CORES["floresta_viva"]
                else:
                    btn.controls[0].color = CORES["tinta_suave"]
                    btn.controls[1].color = CORES["tinta_suave"]
                
                row.controls.append(container)
        
        return ft.Container(
            content=row,
            padding=ft.padding.symmetric(horizontal=12, vertical=8),
            bgcolor=ft.Colors.WHITE,
            border=ft.border.all(1, CORES["floresta"] + "22"),
            border_radius=26,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=20,
                color=ft.Colors.BLACK12,
            ),
            margin=ft.margin.only(left=12, right=12, bottom=12),
        )

    def carregar_memorias(self):
        """Carrega as memórias do banco de dados"""
        if self.user:
            self.memorias_cache = buscar_memorias(self.user["id"])
        else:
            self.memorias_cache = []

    def carregar_memorias_publicas(self):
        """Carrega as memórias marcadas como públicas, de todos os usuários
        (usado na aba Comunidade da tela Explorar)."""
        self.memorias_publicas_cache = buscar_memorias_publicas()

    def render_home(self):
        """Renderiza a tela inicial"""
        if not self.user:
            self.show_screen("login")
            return
        
        memorias = self.memorias_cache
        nome = self.user["nome"]
        
        # Estatísticas de emoções
        stats = {}
        for m in memorias:
            emocao = m[5]  # índice 5 = emocao
            stats[emocao] = stats.get(emocao, 0) + 1
        
        # Montar cards de estatísticas
        stat_controls = []
        max_count = max(stats.values()) if stats else 1
        for emocao, count in sorted(stats.items(), key=lambda x: x[1], reverse=True)[:5]:
            emo = EMOCOES.get(emocao, {"emoji": "💭", "cor": CORES["floresta_clara"]})
            pct = (count / max_count) * 100
            stat_controls.append(
                ft.Container(
                    on_click=lambda e, k=emocao: self.ir_para_explorar_com_emocao(k),
                    border_radius=8,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Text(emo["emoji"], size=16, width=24),
                            ft.Text(emocao.capitalize(), size=11, color=CORES["tinta_suave"], width=64),
                            ft.Container(
                                height=6,
                                border_radius=4,
                                bgcolor=CORES["floresta"] + "22",
                                expand=True,
                                content=ft.ProgressBar(
                                    value=pct / 100,
                                    bgcolor="transparent",
                                    color=emo["cor"],
                                    bar_height=6,
                                )
                            ),
                            ft.Text(str(count), size=11, color=CORES["tinta_suave"], width=18),
                        ]
                    )
                )
            )
        
        # Últimas memórias
        ultimas = memorias[-6:] if len(memorias) > 6 else memorias
        ultimas = sorted(ultimas, key=lambda x: x[6], reverse=True)  # data
        mem_cards = []
        for m in ultimas[:6]:
            mem_cards.append(self.create_memoria_card(m))
        
        # Memória do dia (aleatória)
        memoria_dia = memorias[0] if memorias else None
        if memoria_dia:
            emo = EMOCOES.get(memoria_dia[5], {"emoji": "💭", "cor": CORES["floresta_clara"]})
            dia_card = ft.Container(
                padding=ft.padding.all(14),
                bgcolor=ft.Colors.WHITE,
                border_radius=18,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    spacing=4,
                    controls=[
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Text("🌟", size=14),
                                ft.Text("Memória do dia", size=12, weight=ft.FontWeight.W_600, color=CORES["floresta_viva"]),
                            ]
                        ),
                        ft.Text(
                            f'"{memoria_dia[4][:60]}..."',
                            size=13,
                            italic=True,
                            font_family="Fraunces",
                        ),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Text(f"{emo['emoji']} {emo['label']}", size=11, color=emo["cor"], weight=ft.FontWeight.W_600),
                                ft.Text("•", color=CORES["tinta_suave"]),
                                ft.Text(memoria_dia[3], size=11, color=CORES["tinta_suave"]),
                            ]
                        )
                    ]
                )
            )
        else:
            dia_card = ft.Container(
                padding=ft.padding.all(14),
                bgcolor=ft.Colors.WHITE,
                border_radius=18,
                content=ft.Text("Ainda não há memórias. Crie a primeira! 🌱", size=13),
            )
        
        # Montar conteúdo
        controls = [
            # Topbar
            ft.Row(
                controls=[
                    ft.Column(
                        spacing=2,
                        controls=[
                            ft.Text(f"Olá, {nome.split()[0]} 👋", size=20, weight=ft.FontWeight.BOLD),
                            ft.Text("Que bom te ver de volta.", size=12, color=CORES["tinta_suave"]),
                        ]
                    ),
                    ft.Row(
                        spacing=6,
                        controls=[
                            ft.IconButton(
                                icon=ft.Icons.SEARCH,
                                icon_size=20,
                                icon_color=CORES["tinta"],
                                on_click=lambda e: self.show_screen("explorar"),
                            ),
                            ft.IconButton(
                                icon=ft.Icons.ADD,
                                icon_size=20,
                                icon_color=ft.Colors.WHITE,
                                bgcolor=CORES["dourado"],
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                                on_click=lambda e: self.show_screen("nova"),
                            ),
                            ft.Container(
                                content=ft.Text(self.user.get("avatar", "🙂"), size=20),
                                width=40, height=40,
                                border_radius=20,
                                bgcolor=CORES["floresta"] + "22",
                                border=ft.border.all(1.5, CORES["floresta_clara"] + "44"),
                            )
                        ]
                    )
                ]
            ),
            
            # Memória do dia
            dia_card,
            
            # Estatísticas
            ft.Container(
                padding=ft.padding.all(14),
                bgcolor=ft.Colors.WHITE,
                border_radius=18,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    spacing=6,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("📊", size=14),
                                ft.Text("Emoções", size=14, weight=ft.FontWeight.W_600),
                            ]
                        ),
                    ] + stat_controls if stat_controls else [
                        ft.Text("Ainda não há dados suficientes.", size=12, color=CORES["tinta_suave"]),
                    ]
                )
            ),
            
            # Últimas memórias
            ft.Row(
                alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                controls=[
                    ft.Text("✨ Últimas memórias", size=14, weight=ft.FontWeight.W_600),
                    ft.TextButton(
                        "Ver todas →",
                        style=ft.ButtonStyle(
                            color=CORES["dourado_forte"],
                            text_style=ft.TextStyle(size=12),
                        ),
                        on_click=lambda e: self.show_screen("explorar"),
                    )
                ]
            ),
        ]
        
        # Cards das memórias em scroll horizontal
        if mem_cards:
            controls.append(
                ft.Row(
                    spacing=12,
                    scroll=ft.ScrollMode.AUTO,
                    controls=mem_cards,
                )
            )
        else:
            controls.append(
                ft.Container(
                    padding=ft.padding.all(30),
                    bgcolor=ft.Colors.WHITE,
                    border_radius=18,
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Text("🌱", size=40),
                            ft.Text("Nenhuma memória ainda.", size=14, color=CORES["tinta_suave"]),
                            ft.ElevatedButton(
                                "Criar primeira memória",
                                bgcolor=CORES["floresta_viva"],
                                color=ft.Colors.WHITE,
                                style=ft.ButtonStyle(
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                ),
                                on_click=lambda e: self.show_screen("nova"),
                            )
                        ]
                    )
                )
            )
        
        self.home_content.controls = controls
        self.page.update()

    def create_memoria_card(self, m):
        """Cria um card de memória"""
        emo = EMOCOES.get(m[5], {"emoji": "💭", "cor": CORES["floresta_clara"]})
        
        return ft.Container(
            width=180,
            padding=0,
            border_radius=16,
            bgcolor=ft.Colors.WHITE,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color=ft.Colors.BLACK12,
            ),
            on_click=lambda e, id=m[0]: self.abrir_memoria(id),
            content=ft.Column(
                spacing=0,
                controls=[
                    ft.Container(
                        height=60,
                        alignment=ft.alignment.center,
                        bgcolor=emo["cor"] + "44",
                        content=ft.Stack(
                            controls=[
                                ft.Text(emo["emoji"], size=30),
                                ft.Container(
                                    content=ft.Text(m[3][:8], size=8, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                                    padding=ft.padding.symmetric(horizontal=6, vertical=2),
                                    bgcolor=emo["cor"],
                                    border_radius=8,
                                    top=6,
                                    left=6,
                                )
                            ]
                        )
                    ),
                    ft.Container(
                        padding=ft.padding.all(10),
                        content=ft.Column(
                            spacing=3,
                            controls=[
                                ft.Text(m[2][:20] + ("..." if len(m[2]) > 20 else ""), 
                                       size=13, weight=ft.FontWeight.W_600),
                                ft.Text((m[4][:40] + ("..." if len(m[4]) > 40 else "")), 
                                       size=11, color=CORES["tinta_suave"]),
                                ft.Row(
                                    spacing=6,
                                    controls=[
                                        ft.Text(f"📂 {m[3]}" if m[3] else "📂", size=9, color=CORES["tinta_suave"]),
                                        ft.Text("•", size=9, color=CORES["tinta_suave"]),
                                        ft.Text(m[6], size=9, color=CORES["tinta_suave"]),
                                    ]
                                )
                            ]
                        )
                    )
                ]
            )
        )

    # ==================== EXPLORAR ====================
    def create_explorar_screen(self):
        container = self.create_screen_container("explorar")
        
        self.explorar_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        self.explorar_nav = self.create_navbar("explorar")
        
        container.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    content=self.explorar_content,
                    padding=ft.padding.only(top=8, left=16, right=16, bottom=8),
                ),
                self.explorar_nav,
            ]
        )
        return container

    def render_explorar(self):
        """Renderiza a tela de explorar"""
        if not self.user:
            self.show_screen("login")
            return
        
        # Filtros
        self.filtro_busca = ""
        self.filtro_categoria = None
        self.filtro_emocao = None
        
        # Se veio de um clique no mapa emocional do perfil, aplica esse
        # filtro de emoção automaticamente ao abrir a tela
        if self.explorar_prefiltro_emocao:
            self.filtro_emocao = self.explorar_prefiltro_emocao
            self.explorar_prefiltro_emocao = None
        
        # Campo de busca
        search_field = ft.TextField(
            hint_text="Pesquisar histórias...",
            prefix_icon=ft.Icons.SEARCH,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
            on_change=self.aplicar_filtros,
        )
        self.explorar_search_field = search_field
        
        # Alternar entre minhas memórias e a comunidade (memórias públicas
        # de todos os usuários)
        def selecionar_modo(modo):
            self.explorar_modo = modo
            if modo == "comunidade":
                self.carregar_memorias_publicas()
            btn_minhas.bgcolor = CORES["dourado"] if modo == "minhas" else "transparent"
            btn_minhas.content.color = ft.Colors.WHITE if modo == "minhas" else CORES["floresta"]
            btn_comunidade.bgcolor = CORES["dourado"] if modo == "comunidade" else "transparent"
            btn_comunidade.content.color = ft.Colors.WHITE if modo == "comunidade" else CORES["floresta"]
            self.aplicar_filtros(None)
        
        btn_minhas = ft.Container(
            content=ft.Text("📘 Minhas memórias", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border_radius=14,
            bgcolor=CORES["dourado"],
            expand=True,
            alignment=ft.alignment.center,
            on_click=lambda e: selecionar_modo("minhas"),
        )
        btn_comunidade = ft.Container(
            content=ft.Text("🌍 Comunidade", size=12, weight=ft.FontWeight.W_600, color=CORES["floresta"]),
            padding=ft.padding.symmetric(horizontal=14, vertical=8),
            border_radius=14,
            bgcolor="transparent",
            expand=True,
            alignment=ft.alignment.center,
            on_click=lambda e: selecionar_modo("comunidade"),
        )
        modo_row = ft.Container(
            padding=ft.padding.all(4),
            border_radius=16,
            bgcolor=CORES["floresta"] + "11",
            content=ft.Row(spacing=4, controls=[btn_minhas, btn_comunidade]),
        )
        self.explorar_modo = "minhas"
        
        # Chips de categoria
        cat_chips = ft.Row(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        for cat in CATEGORIAS:
            cat_chips.controls.append(
                ft.Container(
                    content=ft.Text(cat, size=11, weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=14,
                    bgcolor=CORES["floresta"] + "11",
                    border=ft.border.all(1, CORES["floresta"] + "22"),
                    on_click=lambda e, c=cat: self.filtrar_por_categoria(c),
                    data=cat,
                )
            )
        self.explorar_cat_chips = cat_chips
        
        # Chips de emoção
        emo_chips = ft.Row(
            spacing=6,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        for key, emo in EMOCOES.items():
            emo_chips.controls.append(
                ft.Container(
                    content=ft.Text(f"{emo['emoji']} {emo['label']}", size=11, weight=ft.FontWeight.W_500),
                    padding=ft.padding.symmetric(horizontal=10, vertical=4),
                    border_radius=14,
                    bgcolor=CORES["floresta"] + "11",
                    border=ft.border.all(1, CORES["floresta"] + "22"),
                    on_click=lambda e, k=key: self.filtrar_por_emocao(k),
                    data=key,
                )
            )
        self.explorar_emo_chips = emo_chips
        
        # Grid de memórias
        self.memoria_grid = ft.Column(spacing=12)
        
        self.explorar_content.controls = [
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=CORES["floresta"],
                        on_click=lambda e: self.show_screen("home"),
                    ),
                    ft.Text("🔎 Explorar Memórias", size=18, weight=ft.FontWeight.BOLD),
                ]
            ),
            modo_row,
            search_field,
            ft.Text("📂 Categorias", size=12, weight=ft.FontWeight.W_600, color=CORES["tinta_suave"]),
            cat_chips,
            ft.Text("🎭 Emoções", size=12, weight=ft.FontWeight.W_600, color=CORES["tinta_suave"]),
            emo_chips,
            self.memoria_grid,
        ]
        
        self.atualizar_chips()
        self.aplicar_filtros(None)

    def aplicar_filtros(self, e):
        """Aplica os filtros na lista de memórias"""
        busca = self.explorar_search_field.value or ""
        
        if self.explorar_modo == "comunidade":
            memorias = self.memorias_publicas_cache
        else:
            memorias = self.memorias_cache
        
        if busca:
            busca_lower = busca.lower()
            memorias = [m for m in memorias if 
                       busca_lower in m[2].lower() or 
                       busca_lower in m[4].lower() or
                       busca_lower in m[3].lower() or
                       busca_lower in EMOCOES.get(m[5], {}).get("label", "").lower()]
        
        if self.filtro_categoria:
            memorias = [m for m in memorias if m[3] == self.filtro_categoria]
        
        if self.filtro_emocao:
            memorias = [m for m in memorias if m[5] == self.filtro_emocao]
        
        # Atualizar grid
        grid = self.memoria_grid
        grid.controls = []
        
        if not memorias:
            grid.controls.append(
                ft.Container(
                    padding=ft.padding.all(40),
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=8,
                        controls=[
                            ft.Text("🍂", size=40),
                            ft.Text("Nenhuma memória encontrada.", size=14, color=CORES["tinta_suave"]),
                        ]
                    )
                )
            )
        else:
            for m in memorias:
                grid.controls.append(self.create_memoria_card_full(m))
        
        self.page.update()

    def create_memoria_card_full(self, m):
        """Cria um card de memória completo para a grid"""
        emo = EMOCOES.get(m[5], {"emoji": "💭", "cor": CORES["floresta_clara"]})
        
        return ft.Container(
            padding=ft.padding.all(12),
            bgcolor=ft.Colors.WHITE,
            border_radius=16,
            shadow=ft.BoxShadow(
                spread_radius=0,
                blur_radius=16,
                color=ft.Colors.BLACK12,
            ),
            on_click=lambda e, id=m[0]: self.abrir_memoria(id),
            content=ft.Column(
                spacing=4,
                controls=[
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Container(
                                content=ft.Text(emo["emoji"], size=20),
                                width=32, height=32,
                                border_radius=16,
                                bgcolor=emo["cor"] + "33",
                                alignment=ft.alignment.center,
                            ),
                            ft.Text(m[2], size=14, weight=ft.FontWeight.W_600, expand=True),
                        ]
                    ),
                    ft.Text(m[4][:80] + ("..." if len(m[4]) > 80 else ""), 
                           size=12, color=CORES["tinta_suave"]),
                    ft.Row(
                        spacing=8,
                        controls=[
                            ft.Text(f"📂 {m[3]}" if m[3] else "📂", size=10, color=CORES["tinta_suave"]),
                            ft.Text("•", size=10, color=CORES["tinta_suave"]),
                            ft.Text(m[6], size=10, color=CORES["tinta_suave"]),
                            ft.Text("•", size=10, color=CORES["tinta_suave"]),
                            ft.Text(f"{emo['label']}", size=10, color=emo["cor"], weight=ft.FontWeight.W_600),
                        ] + ([ft.Text("•", size=10, color=CORES["tinta_suave"]),
                              ft.Text(f"✍ {m[10]}", size=10, color=CORES["tinta_suave"])] 
                             if len(m) > 10 and m[10] else [])
                    )
                ]
            )
        )

    def filtrar_por_categoria(self, categoria):
        """Filtra por categoria"""
        if self.filtro_categoria == categoria:
            self.filtro_categoria = None
        else:
            self.filtro_categoria = categoria
        
        # Atualizar chips
        self.atualizar_chips()
        self.aplicar_filtros(None)

    def filtrar_por_emocao(self, emocao):
        """Filtra por emoção"""
        if self.filtro_emocao == emocao:
            self.filtro_emocao = None
        else:
            self.filtro_emocao = emocao
        
        self.atualizar_chips()
        self.aplicar_filtros(None)

    def ir_para_explorar_com_emocao(self, emocao):
        """Chamado ao clicar numa emoção na tela Início ou Perfil: leva até
        a tela Explorar já filtrada por essa emoção."""
        self.explorar_prefiltro_emocao = emocao
        self.show_screen("explorar")

    def atualizar_chips(self):
        """Atualiza a aparência (destaque) dos chips selecionados"""
        cat_row = self.explorar_cat_chips
        emo_row = self.explorar_emo_chips
        
        for chip in cat_row.controls:
            selecionado = chip.data == self.filtro_categoria
            chip.bgcolor = CORES["dourado"] if selecionado else CORES["floresta"] + "11"
            chip.border = ft.border.all(1, CORES["dourado_forte"] if selecionado else CORES["floresta"] + "22")
        
        for chip in emo_row.controls:
            selecionado = chip.data == self.filtro_emocao
            chip.bgcolor = CORES["dourado"] if selecionado else CORES["floresta"] + "11"
            chip.border = ft.border.all(1, CORES["dourado_forte"] if selecionado else CORES["floresta"] + "22")
        
        self.page.update()

    # ==================== NOVA MEMÓRIA ====================
    def create_nova_screen(self):
        container = self.create_screen_container("nova")
        
        self.nova_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        self.nova_nav = self.create_navbar("nova")
        
        container.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    content=self.nova_content,
                    padding=ft.padding.only(top=8, left=16, right=16, bottom=8),
                ),
                self.nova_nav,
            ]
        )
        return container

    def render_nova(self):
        """Renderiza a tela de criação de memória"""
        if not self.user:
            self.show_screen("login")
            return
        
        self.nova_emocao = None
        
        # Campos
        titulo_field = ft.TextField(
            label="Título",
            hint_text="Dê um nome a essa lembrança",
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        
        categoria_drop = ft.Dropdown(
            label="Categoria",
            hint_text="Selecione uma categoria",
            options=[ft.dropdown.Option(c) for c in CATEGORIAS],
            border_radius=14,
            border_color=CORES["floresta"] + "33",
        )
        
        local_field = ft.TextField(
            label="Local",
            hint_text="Onde isso aconteceu?",
            prefix_icon=ft.Icons.LOCATION_ON,
            text_size=14,
            height=46,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        
        texto_field = ft.TextField(
            label="Sua história",
            hint_text="Conte com detalhes...",
            multiline=True,
            min_lines=4,
            max_lines=8,
            text_size=14,
            border_radius=14,
            border_color=CORES["floresta"] + "33",
            focused_border_color=CORES["floresta_clara"],
        )
        
        # Picker de emoção
        self.emoji_picker = ft.Row(
            spacing=6,
            wrap=True,
            controls=[]
        )
        
        for key, emo in EMOCOES.items():
            self.emoji_picker.controls.append(
                ft.Container(
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        spacing=2,
                        controls=[
                            ft.Text(emo["emoji"], size=22),
                            ft.Text(emo["label"], size=8, color=CORES["tinta_suave"]),
                        ]
                    ),
                    padding=ft.padding.symmetric(horizontal=8, vertical=6),
                    border_radius=12,
                    border=ft.border.all(1.5, CORES["floresta"] + "22"),
                    bgcolor=ft.Colors.TRANSPARENT,
                    on_click=lambda e, k=key: self.selecionar_emocao(k),
                    data=key,
                )
            )
        
        # Visibilidade
        vis_publica = ft.Radio(
            value="publica",
            label="🌍 Pública",
            fill_color=CORES["floresta_viva"],
        )
        vis_privada = ft.Radio(
            value="privada",
            label="🔒 Privada",
            fill_color=CORES["floresta_viva"],
        )
        vis_group = ft.RadioGroup(
            content=ft.Row(
                spacing=16,
                controls=[vis_publica, vis_privada],
            ),
            value="privada",
        )
        
        # Mensagem de erro
        err_text = ft.Text("", size=12, color=CORES["vinho"])
        
        # Botão salvar
        btn_salvar = ft.ElevatedButton(
            "Salvar Memória 💾",
            width=200,
            height=48,
            bgcolor=CORES["floresta_viva"],
            color=ft.Colors.WHITE,
            style=ft.ButtonStyle(
                shape=ft.RoundedRectangleBorder(radius=16),
            ),
            on_click=lambda e: self.salvar_memoria(
                titulo_field, categoria_drop, local_field, 
                texto_field, vis_group, err_text
            ),
        )
        
        self.nova_content.controls = [
            ft.Container(
                padding=ft.padding.all(20),
                bgcolor=ft.Colors.WHITE,
                border_radius=24,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_color=CORES["floresta"],
                                    on_click=lambda e: self.show_screen("home"),
                                ),
                                ft.Text("✧ Nova Memória", size=20, weight=ft.FontWeight.BOLD),
                            ]
                        ),
                        ft.Text("Registre um novo capítulo da sua história.", 
                               size=12, color=CORES["tinta_suave"]),
                        titulo_field,
                        local_field,
                        ft.Text("📝 Sua história", size=13, weight=ft.FontWeight.W_600),
                        texto_field,
                        ft.Container(
                            padding=ft.padding.all(10),
                            border_radius=12,
                            bgcolor=CORES["floresta"] + "11",
                            content=ft.Row(
                                spacing=8,
                                controls=[
                                    ft.Text("🤖", size=16),
                                    ft.Text(
                                        "Ao salvar, o sistema analisa o texto sozinho e identifica a categoria e a emoção predominante — você não precisa escolher nada.",
                                        size=11, italic=True, color=CORES["tinta_suave"], expand=True,
                                    ),
                                ]
                            )
                        ),
                        ft.Text("🔒 Visibilidade", size=13, weight=ft.FontWeight.W_600),
                        vis_group,
                        err_text,
                        ft.Row(
                            alignment=ft.MainAxisAlignment.CENTER,
                            controls=[btn_salvar]
                        )
                    ]
                )
            )
        ]
        self.page.update()

    def selecionar_emocao(self, key):
        """Seleciona uma emoção para a nova memória"""
        self.nova_emocao = key
        
        # Atualizar aparência dos botões
        for control in self.emoji_picker.controls:
            if control.data == key:
                control.border = ft.border.all(2, EMOCOES[key]["cor"])
                control.bgcolor = EMOCOES[key]["cor"] + "33"
            else:
                control.border = ft.border.all(1.5, CORES["floresta"] + "22")
                control.bgcolor = ft.Colors.TRANSPARENT
        
        self.page.update()

    def salvar_memoria(self, titulo, categoria, local, texto, vis, err):
        """Salva uma nova memória no banco de dados.
        Nem a emoção nem a categoria são escolhidas manualmente: o sistema
        analisa o título + o texto (juntos, considerando o contexto) e
        identifica automaticamente categoria, emoção predominante,
        possível emoção secundária, intensidade e gera uma frase
        reflexiva conectada ao que foi escrito."""
        if not titulo.value:
            err.value = "⚠️ Dê um título à sua memória."
            err.update()
            return
        
        if not texto.value:
            err.value = "⚠️ Escreva sua história."
            err.update()
            return
        
        # Análise automática (considera título + texto + contexto)
        analise = analisar_texto(titulo.value, texto.value)
        emocao_detectada = analise["emocao"]
        categoria_detectada = analise["categoria"]
        frase_motivadora = analise["frase_motivadora"]
        explicacao = analise["explicacao"]
        
        if analise["confianca"] == "baixa" and emocao_detectada == "indefinida":
            err.value = "⚠️ " + frase_motivadora
            err.update()
            return
        
        # Salvar no banco
        from datetime import datetime
        data_atual = datetime.now().strftime("%d/%m/%Y")
        visibilidade_valor = vis.value if vis and vis.value else "privada"
        
        try:
            db_salvar_memoria(
                self.user["id"],
                titulo.value,
                categoria_detectada,
                texto.value,
                emocao_detectada,
                data_atual,
                frase_motivadora,
                explicacao,
                visibilidade_valor
            )
            
            self.carregar_memorias()
            emo_info = EMOCOES.get(emocao_detectada, {"label": emocao_detectada, "emoji": "💭"})
            self.toast(f"🌿 Salva! Emoção: {emo_info['emoji']} {emo_info['label']} · Categoria: {categoria_detectada}")
            self.show_screen("home")
        except Exception as e:
            err.value = f"⚠️ Erro ao salvar: {str(e)}"
            err.update()

    # ==================== MEMÓRIA (DETALHE) ====================
    def create_memoria_screen(self):
        container = self.create_screen_container("memoria")
        
        self.memoria_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        container.content = ft.Container(
            expand=True,
            content=self.memoria_content,
            padding=ft.padding.only(top=8, left=0, right=0, bottom=8),
        )
        return container

    def abrir_memoria(self, id_memoria):
        """Abre uma memória para visualização"""
        self.selected_memoria_id = id_memoria
        self.render_memoria()
        self.show_screen("memoria")

    def render_memoria(self):
        """Renderiza o detalhe de uma memória (própria ou pública de
        outra pessoa, vista pela Comunidade)."""
        m = None
        eh_publica_de_outro = False
        autor_nome = self.user["nome"] if self.user else ""
        
        for mem in self.memorias_cache:
            if mem[0] == self.selected_memoria_id:
                m = mem
                break
        
        if not m:
            # Não é sua — procura entre as memórias públicas da comunidade
            for mem in self.memorias_publicas_cache:
                if mem[0] == self.selected_memoria_id:
                    m = mem
                    eh_publica_de_outro = (mem[1] != self.user["id"]) if self.user else True
                    # Nas linhas de buscar_memorias_publicas(), nome vem no índice 10
                    autor_nome = mem[10] if len(mem) > 10 and mem[10] else "Alguém da comunidade"
                    break
        
        if not m:
            self.memoria_content.controls = [
                ft.Container(
                    padding=ft.padding.all(40),
                    alignment=ft.alignment.center,
                    content=ft.Column(
                        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                        controls=[
                            ft.Text("🍂", size=40),
                            ft.Text("Memória não encontrada.", size=14, color=CORES["tinta_suave"]),
                        ]
                    )
                )
            ]
            self.page.update()
            return
        
        emo = EMOCOES.get(m[5], {"emoji": "💭", "label": "Sentimento", "cor": CORES["floresta_clara"]})
        
        # Frase e explicação geradas no momento em que a memória foi salva
        # (considerando título + texto). Memórias antigas (de antes dessa
        # versão) podem não ter isso salvo — nesse caso, geramos na hora.
        if len(m) > 7 and m[7]:
            mensagem = m[7]
            explicacao = m[8] if len(m) > 8 and m[8] else ""
        else:
            analise_fallback = analisar_texto(m[2], m[4])
            mensagem = analise_fallback["frase_motivadora"]
            explicacao = analise_fallback["explicacao"]
        
        acoes_botoes = [
            ft.IconButton(
                icon=ft.Icons.SHARE,
                icon_size=20,
                icon_color=ft.Colors.WHITE70,
                on_click=lambda e: self.toast("🔗 Compartilhamento simulado"),
            ),
        ]
        if not eh_publica_de_outro:
            acoes_botoes.append(
                ft.IconButton(
                    icon=ft.Icons.DELETE_OUTLINE,
                    icon_size=20,
                    icon_color=ft.Colors.WHITE70,
                    on_click=lambda e: self.excluir_memoria(m[0]),
                )
            )
        
        self.memoria_content.controls = [
            # Cabeçalho com emoção
            ft.Container(
                height=180,
                padding=ft.padding.all(16),
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_center,
                    end=ft.alignment.bottom_center,
                    colors=[emo["cor"] + "88", emo["cor"] + "33"],
                ),
                border_radius=ft.border_radius.only(bottom_left=30, bottom_right=30),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.IconButton(
                                    icon=ft.Icons.ARROW_BACK,
                                    icon_size=24,
                                    icon_color=ft.Colors.WHITE,
                                    on_click=lambda e: self.show_screen(
                                        "explorar" if eh_publica_de_outro else "home"
                                    ),
                                ),
                                ft.Row(spacing=6, controls=acoes_botoes),
                            ]
                        ),
                        ft.Text(emo["emoji"], size=56),
                        ft.Text(emo["label"], size=14, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                    ]
                )
            ),
            
            # Conteúdo
            ft.Container(
                padding=ft.padding.all(16),
                content=ft.Column(
                    spacing=12,
                    controls=[
                        ft.Text(m[2], size=20, weight=ft.FontWeight.BOLD, font_family="Fraunces"),
                        ft.Row(
                            spacing=6,
                            controls=[
                                ft.Text(f"✍ {autor_nome}", size=12, color=CORES["tinta_suave"]),
                                ft.Text("•", size=12, color=CORES["tinta_suave"]),
                                ft.Text(f"📂 {m[3]}" if m[3] else "📂", size=12, color=CORES["tinta_suave"]),
                                ft.Text("•", size=12, color=CORES["tinta_suave"]),
                                ft.Text(m[6], size=12, color=CORES["tinta_suave"]),
                                ft.Text("🌍 Pública" if eh_publica_de_outro or (len(m) > 9 and m[9] == "publica") else "", 
                                       size=12, color=CORES["tinta_suave"]),
                            ]
                        ),
                        ft.Divider(height=1, color=CORES["floresta"] + "22"),
                        ft.Text(m[4], size=14, height=1.6),
                        
                        # Explicação da análise (o "porquê")
                        ft.Divider(height=1, color=CORES["floresta"] + "22"),
                        ft.Container(
                            padding=ft.padding.all(12),
                            border_radius=12,
                            bgcolor=CORES["floresta"] + "0A",
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("🔍 Por que essa análise?", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(explicacao, size=12, color=CORES["tinta_suave"]),
                                ]
                            )
                        ) if explicacao else ft.Container(height=0),
                        
                        # Mensagem da análise de emoção
                        ft.Container(
                            padding=ft.padding.all(12),
                            border_radius=12,
                            bgcolor=CORES["floresta"] + "11",
                            content=ft.Column(
                                spacing=4,
                                controls=[
                                    ft.Text("💭 Reflexão", size=13, weight=ft.FontWeight.W_600),
                                    ft.Text(mensagem, size=12, color=CORES["tinta_suave"], italic=True),
                                ]
                            )
                        ),
                        
                        ft.Divider(height=1, color=CORES["floresta"] + "22"),
                        ft.Row(
                            spacing=8,
                            controls=[
                                ft.Text("❤️ 0", size=13),
                                ft.Text("💬 0", size=13),
                            ]
                        ),
                    ]
                )
            ),
            ft.Container(height=20),
        ]
        self.page.update()

    def excluir_memoria(self, id_memoria):
        """Exclui uma memória"""
        def confirmar(e):
            self.fechar_modal()
            excluir_memoria(id_memoria)
            self.carregar_memorias()
            self.toast("🗑️ Memória excluída.")
            self.show_screen("home")
        
        def cancelar(e):
            self.fechar_modal()
        
        conteudo = ft.Column(
            tight=True,
            spacing=16,
            controls=[
                ft.Text("Excluir memória", size=16, weight=ft.FontWeight.BOLD),
                ft.Text("Tem certeza que deseja excluir esta memória? Esta ação não pode ser desfeita.", size=13),
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                    controls=[
                        ft.TextButton("Cancelar", on_click=cancelar),
                        ft.ElevatedButton("Excluir", bgcolor=CORES["vinho"], color=ft.Colors.WHITE, on_click=confirmar),
                    ]
                )
            ]
        )
        
        self.abrir_modal(conteudo)

    # ==================== PERFIL ====================
    def create_perfil_screen(self):
        container = self.create_screen_container("perfil")
        
        self.perfil_content = ft.Column(
            spacing=12,
            scroll=ft.ScrollMode.AUTO,
            controls=[]
        )
        
        self.perfil_nav = self.create_navbar("perfil")
        
        container.content = ft.Column(
            spacing=0,
            expand=True,
            controls=[
                ft.Container(
                    expand=True,
                    content=self.perfil_content,
                    padding=ft.padding.only(top=8, left=16, right=16, bottom=8),
                ),
                self.perfil_nav,
            ]
        )
        return container

    def render_perfil(self):
        """Renderiza a tela de perfil"""
        if not self.user:
            self.show_screen("login")
            return
        
        nome = self.user["nome"]
        email = self.user["email"]
        total = len(self.memorias_cache)
        
        # Estatísticas
        stats = {}
        for m in self.memorias_cache:
            emocao = m[5]
            stats[emocao] = stats.get(emocao, 0) + 1
        
        stat_controls = []
        max_count = max(stats.values()) if stats else 1
        ranking_emocional = sorted(stats.items(), key=lambda x: x[1], reverse=True)
        for emocao, count in ranking_emocional:
            emo = EMOCOES.get(emocao, {"emoji": "💭", "cor": CORES["floresta_clara"]})
            pct = (count / max_count) * 100
            stat_controls.append(
                ft.Container(
                    on_click=lambda e, k=emocao: self.ir_para_explorar_com_emocao(k),
                    border_radius=8,
                    content=ft.Row(
                        spacing=8,
                        controls=[
                            ft.Text(emo["emoji"], size=16, width=24),
                            ft.Text(emo.get("label", emocao.capitalize()), size=12, color=CORES["tinta_suave"], width=64),
                            ft.Container(
                                height=6,
                                border_radius=4,
                                bgcolor=CORES["floresta"] + "22",
                                expand=True,
                                content=ft.ProgressBar(
                                    value=pct / 100,
                                    bgcolor="transparent",
                                    color=emo["cor"],
                                    bar_height=6,
                                )
                            ),
                            ft.Text(str(count), size=12, color=CORES["tinta_suave"], width=20),
                        ]
                    )
                )
            )
        
        # Mapa emocional: qual sentimento mais define a pessoa, com base em
        # TODAS as memórias dela (públicas e privadas).
        if ranking_emocional:
            emocao_dominante, count_dominante = ranking_emocional[0]
            emo_dom = EMOCOES.get(emocao_dominante, {"emoji": "💭", "cor": CORES["floresta_clara"], "label": emocao_dominante.capitalize()})
            pct_dominante = round((count_dominante / total) * 100) if total else 0
            mapa_emocional_card = ft.Container(
                padding=ft.padding.all(20),
                border_radius=24,
                gradient=ft.LinearGradient(
                    begin=ft.alignment.top_left,
                    end=ft.alignment.bottom_right,
                    colors=[emo_dom["cor"] + "cc", emo_dom["cor"] + "77"],
                ),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text("🧭 Seu mapa emocional", size=13, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                        ft.Text(emo_dom["emoji"], size=48),
                        ft.Text(
                            f'Predominantemente {emo_dom.get("label", emocao_dominante.capitalize())}',
                            size=17, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE,
                        ),
                        ft.Text(
                            f"{count_dominante} de {total} memórias ({pct_dominante}%) carregam esse sentimento.",
                            size=11, color=ft.Colors.WHITE, italic=True,
                        ),
                    ]
                )
            )
        else:
            mapa_emocional_card = ft.Container(
                padding=ft.padding.all(20),
                border_radius=24,
                bgcolor=CORES["floresta"] + "11",
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=4,
                    controls=[
                        ft.Text("🧭 Seu mapa emocional", size=13, weight=ft.FontWeight.W_600),
                        ft.Text("🌱", size=40),
                        ft.Text("Escreva sua primeira memória para começar a ver seu mapa emocional.",
                               size=12, color=CORES["tinta_suave"], text_align=ft.TextAlign.CENTER),
                    ]
                )
            )
        
        self.perfil_content.controls = [
            ft.Row(
                controls=[
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK,
                        icon_color=CORES["floresta"],
                        on_click=lambda e: self.show_screen("home"),
                    ),
                    ft.Text("👤 Perfil", size=18, weight=ft.FontWeight.BOLD),
                ]
            ),
            # Header
            ft.Container(
                padding=ft.padding.all(24),
                bgcolor=ft.Colors.WHITE,
                border_radius=24,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    spacing=8,
                    controls=[
                        ft.Container(
                            content=ft.Text(self.user.get("avatar", "🙂"), size=36),
                            width=72, height=72,
                            border_radius=36,
                            bgcolor=CORES["floresta"] + "22",
                            border=ft.border.all(2, CORES["floresta_clara"] + "44"),
                        ),
                        ft.Text(nome, size=20, weight=ft.FontWeight.BOLD),
                        ft.Text(email, size=12, color=CORES["tinta_suave"]),
                        ft.Container(
                            content=ft.Text(f"{total} memórias registradas", size=12, weight=ft.FontWeight.W_600, color=ft.Colors.WHITE),
                            padding=ft.padding.symmetric(horizontal=16, vertical=6),
                            bgcolor=CORES["dourado"],
                            border_radius=20,
                        ),
                        ft.Text(
                            f"Membro desde {self.user.get('data_cadastro') or '—'}",
                            size=11, color=CORES["tinta_suave"]
                        ),
                        ft.Container(
                            content=ft.Text("✏️ Editar perfil", size=12, weight=ft.FontWeight.W_600, color=CORES["floresta"]),
                            padding=ft.padding.symmetric(horizontal=14, vertical=6),
                            border=ft.border.all(1, CORES["floresta"] + "44"),
                            border_radius=16,
                            on_click=lambda e: self.abrir_editar_perfil(),
                        ),
                    ]
                )
            ),
            
            # Mapa emocional (destaque)
            mapa_emocional_card,
            
            # Estatísticas
            ft.Container(
                padding=ft.padding.all(16),
                bgcolor=ft.Colors.WHITE,
                border_radius=24,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("📊", size=14),
                                ft.Text("Minhas emoções", size=14, weight=ft.FontWeight.W_600),
                            ]
                        ),
                    ] + (stat_controls if stat_controls else [
                        ft.Text("Ainda não há dados suficientes.", size=12, color=CORES["tinta_suave"]),
                    ])
                )
            ),
            
            # Configurações
            ft.Container(
                padding=ft.padding.all(16),
                bgcolor=ft.Colors.WHITE,
                border_radius=24,
                shadow=ft.BoxShadow(
                    spread_radius=0,
                    blur_radius=20,
                    color=ft.Colors.BLACK12,
                ),
                content=ft.Column(
                    spacing=8,
                    controls=[
                        ft.Row(
                            controls=[
                                ft.Text("⚙️", size=14),
                                ft.Text("Configurações", size=14, weight=ft.FontWeight.W_600),
                            ]
                        ),
                        ft.Row(
                            alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
                            controls=[
                                ft.Text("🌙 Tema escuro", size=13),
                                ft.Switch(
                                    value=self.theme == "dark",
                                    active_color=CORES["floresta_viva"],
                                    on_change=self.toggle_theme,
                                )
                            ]
                        ),
                        ft.Divider(height=1, color=CORES["floresta"] + "22"),
                        ft.Container(
                            content=ft.Text("⎋ Sair da conta", size=13, color=CORES["vinho"]),
                            on_click=lambda e: self.logout(),
                        )
                    ]
                )
            ),
            ft.Container(height=20),
        ]
        self.page.update()

    def abrir_editar_perfil(self):
        """Abre um painel para editar nome e avatar do usuário logado.
        A alteração é salva de verdade no banco (tabela usuarios) e
        permanece ao sair e entrar de novo na conta."""
        AVATARES = ["🙂", "🌿", "🌳", "🍃", "🌸", "🌻", "🧔", "👩‍🎓", "🧑"]

        nome_field = ft.TextField(
            label="Nome",
            value=self.user["nome"],
            border_radius=12,
            border_color=CORES["floresta"] + "33",
        )
        avatar_escolhido = {"valor": self.user.get("avatar", "🙂")}

        avatar_botoes = []

        def escolher_avatar(av):
            avatar_escolhido["valor"] = av
            for btn in avatar_botoes:
                selecionado = btn.data == av
                btn.bgcolor = CORES["dourado"] if selecionado else CORES["floresta"] + "11"
            self.page.update()

        for av in AVATARES:
            btn = ft.Container(
                content=ft.Text(av, size=20),
                width=42, height=42,
                border_radius=21,
                alignment=ft.alignment.center,
                bgcolor=CORES["dourado"] if av == avatar_escolhido["valor"] else CORES["floresta"] + "11",
                data=av,
                on_click=lambda e, a=av: escolher_avatar(a),
            )
            avatar_botoes.append(btn)

        erro_txt = ft.Text("", size=12, color=CORES["vinho"])

        def salvar(e):
            if not nome_field.value or not nome_field.value.strip():
                erro_txt.value = "⚠️ O nome não pode ficar em branco."
                self.page.update()
                return
            atualizar_usuario(self.user["id"], nome_field.value.strip(), avatar_escolhido["valor"])
            self.user["nome"] = nome_field.value.strip()
            self.user["avatar"] = avatar_escolhido["valor"]
            self.fechar_modal()
            self.render_perfil()
            self.toast("✅ Perfil atualizado!")

        def cancelar(e):
            self.fechar_modal()

        conteudo = ft.Column(
            tight=True,
            spacing=12,
            controls=[
                ft.Text("Editar perfil", size=16, weight=ft.FontWeight.BOLD),
                nome_field,
                ft.Text("Avatar", size=12, weight=ft.FontWeight.W_600),
                ft.Row(controls=avatar_botoes, wrap=True, spacing=8),
                erro_txt,
                ft.Row(
                    alignment=ft.MainAxisAlignment.END,
                    spacing=8,
                    controls=[
                        ft.TextButton("Cancelar", on_click=cancelar),
                        ft.ElevatedButton("Salvar", bgcolor=CORES["floresta"], color=ft.Colors.WHITE, on_click=salvar),
                    ]
                )
            ]
        )

        self.abrir_modal(conteudo)

    def toggle_theme(self, e):
        """Alterna entre tema claro e escuro"""
        self.theme = "dark" if e.control.value else "light"
        self.page.theme_mode = ft.ThemeMode.DARK if self.theme == "dark" else ft.ThemeMode.LIGHT
        self.page.bgcolor = CORES["musgo"] if self.theme == "dark" else CORES["pergaminho"]
        self.page.update()

    def logout(self):
        """Faz logout do usuário"""
        self.user = None
        self.memorias_cache = []
        self.memorias_publicas_cache = []
        self.show_screen("login")
        self.toast("Até logo!")

    # ==================== NAVEGAÇÃO ====================
    def show_screen(self, screen_name):
        """Mostra uma tela específica"""
        # Mapear telas para funções de renderização
        render_map = {
            "home": self.render_home,
            "explorar": self.render_explorar,
            "nova": self.render_nova,
            "memoria": self.render_memoria,
            "perfil": self.render_perfil,
        }
        
        # Verificar se é uma tela que requer login
        if screen_name in ["home", "explorar", "nova", "memoria", "perfil"] and not self.user:
            screen_name = "login"
        
        # Esconder todas as telas (o modal de diálogos fica fora dessa
        # lógica — ele é controlado só por abrir_modal/fechar_modal)
        for control in self.screens.controls:
            if control is self.modal_overlay:
                continue
            control.opacity = 0
            control.visible = False
        
        # Mostrar a tela desejada
        target = None
        for control in self.screens.controls:
            if control.data == screen_name:
                target = control
                break
        
        if target:
            target.visible = True
            target.opacity = 1
            # Renderizar conteúdo se necessário
            if screen_name in render_map:
                render_map[screen_name]()
        
        self.page.update()

    def route_change(self, route):
        """Gerencia mudanças de rota"""
        route_name = route.route.strip("/")
        if route_name in ["home", "explorar", "nova", "memoria", "perfil"]:
            self.show_screen(route_name)
        else:
            self.show_screen("home")

    # ==================== TOAST ====================
    def toast(self, message):
        """Exibe uma mensagem temporária"""
        snack = ft.SnackBar(
            content=ft.Text(message, color=ft.Colors.WHITE),
            bgcolor=CORES["floresta"],
            duration=2500,
        )
        self.page.overlay.append(snack)
        snack.open = True
        self.page.update()


def main():
    app = MemoriaVivaApp()
    ft.app(target=app.main)


if __name__ == "__main__":
    main()