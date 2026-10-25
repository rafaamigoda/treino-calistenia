import streamlit as st
import sqlite3
import datetime
import os

VIDEO_DIR = "app-calistenia/videos"

st.set_page_config(
    page_title="VERSÃO RAFINHA 5.0 — Dark Red Performance",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

SENHA_CORRETA = "151123"

if "autenticado" not in st.session_state:
    st.session_state["autenticado"] = False

def verificar_senha():
    if st.session_state.get("input_senha", "") == SENHA_CORRETA:
        st.session_state["autenticado"] = True
    else:
        st.error("Senha incorreta. Acesso negado! 🔒")

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Orbitron:wght@600;800;900&family=Inter:wght@300;400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
        background-color: #050507 !important;
        color: #E2E8F0 !important;
    }

    .stApp {
        background: radial-gradient(circle at top right, #1a0509 0%, #050507 60%);
    }

    .hero-header {
        background: linear-gradient(135deg, rgba(220, 20, 60, 0.2) 0%, rgba(10, 10, 12, 0.8) 100%);
        border: 1px solid rgba(255, 0, 60, 0.4);
        border-radius: 16px;
        padding: 30px 20px;
        text-align: center;
        backdrop-filter: blur(10px);
        box-shadow: 0 10px 30px rgba(255, 0, 60, 0.15);
        margin-bottom: 25px;
    }
    .hero-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.1rem;
        font-weight: 900;
        background: linear-gradient(90deg, #FF003C, #FF3366, #FF6600);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-transform: uppercase;
        letter-spacing: 2px;
        margin: 0;
    }
    .hero-sub {
        color: #A0AEC0;
        font-size: 0.90rem;
        margin-top: 8px;
        font-weight: 400;
    }

    .login-box {
        max-width: 420px;
        margin: 40px auto;
        background: rgba(18, 18, 24, 0.85);
        border: 1px solid rgba(255, 0, 60, 0.5);
        border-radius: 16px;
        padding: 30px;
        backdrop-filter: blur(12px);
        box-shadow: 0 0 35px rgba(255, 0, 60, 0.25);
        text-align: center;
    }

    .exercise-card {
        background: rgba(18, 18, 24, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #FF003C;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 20px;
        backdrop-filter: blur(8px);
    }
    .ex-title {
        font-family: 'Orbitron', sans-serif;
        font-size: 1.2rem;
        color: #F8FAFC;
        font-weight: 700;
    }
    .badge-focus {
        background: linear-gradient(90deg, #FF003C, #FF4D6D);
        color: #FFF;
        padding: 4px 10px;
        border-radius: 20px;
        font-size: 0.75rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .stat-card {
        background: rgba(12, 12, 16, 0.85);
        border: 1px solid #FF003C;
        border-radius: 12px;
        padding: 20px;
        text-align: center;
        box-shadow: 0 0 15px rgba(255, 0, 60, 0.15);
    }
    .stat-number {
        font-family: 'Orbitron', sans-serif;
        font-size: 2.5rem;
        font-weight: 900;
        color: #FF003C;
    }
    .stat-label {
        color: #A0AEC0;
        font-size: 0.85rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .log-card {
        background: rgba(12, 12, 16, 0.9);
        border-left: 4px solid #FF003C;
        border-radius: 8px;
        padding: 12px 16px;
        margin-bottom: 12px;
    }

    .stButton>button {
        background: linear-gradient(90deg, #FF003C, #CC0031) !important;
        color: white !important;
        border: none !important;
        font-weight: bold !important;
        border-radius: 8px !important;
    }
    .stButton>button:hover {
        background: linear-gradient(90deg, #FF3366, #FF003C) !important;
        box-shadow: 0 0 15px rgba(255, 0, 60, 0.5);
    }
</style>
""", unsafe_allow_html=True)

if not st.session_state["autenticado"]:
    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">🔒 ACESSO RESTRITO</div>
        <div class="hero-sub">VERSÃO RAFINHA 5.0 — SISTEMA PRIVADO</div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 1.2, 1])
    with col2:
        st.markdown('<div class="login-box">', unsafe_allow_html=True)
        st.markdown("### 🔑 Digite sua senha de acesso:")
        st.text_input("Senha VIP:", type="password", key="input_senha", label_visibility="collapsed")
        
        if st.button("ENTRAR NO PAINEL 🚀", use_container_width=True):
            verificar_senha()
            if st.session_state["autenticado"]:
                st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

else:
    def init_db():
        conn = sqlite3.connect("treino_database.db")
        c = conn.cursor()
        c.execute("""
            CREATE TABLE IF NOT EXISTS conclusoes_exercicios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                semana TEXT,
                dia_treino TEXT,
                exercicio TEXT,
                series INT,
                reps INT,
                carga TEXT,
                concluido INT
            )
        """)
        c.execute("""
            CREATE TABLE IF NOT EXISTS sessoes_treino (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT,
                dia_treino TEXT,
                total_exercicios INT,
                observacoes TEXT
            )
        """)
        conn.commit()
        conn.close()

    init_db()

    def registrar_exercicio_concluido(dia_treino, exercicio, series, reps, carga):
        conn = sqlite3.connect("treino_database.db")
        c = conn.cursor()
        hoje = datetime.date.today()
        data_str = hoje.strftime("%Y-%m-%d")
        semana_str = f"Semana {hoje.isocalendar()[1]}"
        
        c.execute("""
            INSERT INTO conclusoes_exercicios (data, semana, dia_treino, exercicio, series, reps, carga, concluido)
            VALUES (?, ?, ?, ?, ?, ?, ?, 1)
        """, (data_str, semana_str, dia_treino, exercicio, series, reps, carga))
        conn.commit()
        conn.close()

    def registrar_sessao_completa(dia_treino, total_ex, obs=""):
        conn = sqlite3.connect("treino_database.db")
        c = conn.cursor()
        data_str = datetime.date.today().strftime("%Y-%m-%d")
        c.execute("""
            INSERT INTO sessoes_treino (data, dia_treino, total_exercicios, observacoes)
            VALUES (?, ?, ?, ?)
        """, (data_str, dia_treino, total_ex, obs))
        conn.commit()
        conn.close()

    st.markdown("""
    <div class="hero-header">
        <div class="hero-title">⚡ VERSÃO RAFINHA 5.0</div>
        <div class="hero-sub">PEITORAL SUPERIOR • CORE & ABDOMINAL EM "V" • DASHBOARD DE HIPERTROFIA</div>
    </div>
    """, unsafe_allow_html=True)

    aba_selecionada = st.tabs(["🏋️ TREINO DO DIA", "📈 RELATÓRIO & ESTATÍSTICAS", "📖 GUIA DOS EXERCÍCIOS"])

    def exibir_video_ou_link(video_filename, link_yt):
        video_path = os.path.join(VIDEO_DIR, video_filename)
        if os.path.exists(video_path):
            st.video(video_path)
        else:
            st.info(f"💡 Vídeo local ({video_filename}) carregando da pasta. [Assistir HD no YouTube]({link_yt})")

    with aba_selecionada[0]:
        dia_selecionado = st.selectbox(
            "SELECIONE A SESSÃO DE HOJE:",
            [
                "Segunda-Feira — Treino A: Peitoral Superior & Média Força",
                "Terça-Feira — Treino B: Ombros, Parte Superior & Abdômen",
                "Quarta-Feira — Treino C: Puxada Invertida, Peito & Tronco",
                "Quinta-Feira — Descanso Ativo",
                "Sexta-Feira — Treino D: Hipertrofia do Peito & Foco no V"
            ]
        )

        st.write("")

        if "Segunda" in dia_selecionado:
            st.subheader("🔥 Segunda-Feira — Treino A: Peitoral Superior")
            
            with st.container():
                st.markdown("""
                <div class="exercise-card">
                    <span class="badge-focus">Foco: Peitoral Superior / Clavicular</span>
                    <div class="ex-title">1. Flexão com Pés Elevados (Declinada)</div>
                    <p style="color: #A0AEC0; margin-top: 5px;">Meta: 3–4 séries × 6–10 repetições | Descanso: 2 min</p>
                </div>
                """, unsafe_allow_html=True)
                exibir_video_ou_link("flexao_pes_elevados.mp4", "http://www.youtube.com/watch?v=bpjqDjXBv-M")
                
                c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                s1 = c1.number_input("Séries", 1, 5, 3, key="s1")
                r1 = c2.number_input("Reps", 1, 30, 8, key="r1")
                cg1 = c3.text_input("Carga / Obs", "Peso do corpo", key="cg1")
                chk1 = c4.checkbox("✔️ Concluído", key="chk1")
                if chk1:
                    registrar_exercicio_concluido("Treino A", "Flexão com Pés Elevados", s1, r1, cg1)
                    st.success("Ex. 1 Salvo no Banco de Dados!")

            with st.container():
                st.markdown("""
                <div class="exercise-card">
                    <span class="badge-focus">Foco: Miolo do Peito & Tríceps</span>
                    <div class="ex-title">2. Flexão Diamante (Mãos Juntas)</div>
                    <p style="color: #A0AEC0; margin-top: 5px;">Meta: 3 séries × 8–12 repetições | Descanso: 90s</p>
                </div>
                """, unsafe_allow_html=True)
                exibir_video_ou_link("flexao_diamante.mp4", "http://www.youtube.com/watch?v=DfsWjEThmLY")
                
                c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                s2 = c1.number_input("Séries", 1, 5, 3, key="s2")
                r2 = c2.number_input("Reps", 1, 30, 10, key="r2")
                cg2 = c3.text_input("Carga / Obs", "Peso do corpo", key="cg2")
                chk2 = c4.checkbox("✔️ Concluído", key="chk2")
                if chk2:
                    registrar_exercicio_concluido("Treino A", "Flexão Diamante", s2, r2, cg2)
                    st.success("Ex. 2 Salvo no Banco de Dados!")

            with st.container():
                st.markdown("""
                <div class="exercise-card">
                    <span class="badge-focus">Foco: Volume & Base Geral</span>
                    <div class="ex-title">3. Flexão Tradicional com Pausa (1s)</div>
                    <p style="color: #A0AEC0; margin-top: 5px;">Meta: 2–3 séries × 8–12 repetições | Descanso: 90s</p>
                </div>
                """, unsafe_allow_html=True)
                exibir_video_ou_link("flexao_tradicional.mp4", "http://www.youtube.com/watch?v=xARTt_hMvj4")
                
                c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                s3 = c1.number_input("Séries", 1, 5, 3, key="s3")
                r3 = c2.number_input("Reps", 1, 30, 10, key="r3")
                cg3 = c3.text_input("Carga / Obs", "Peso do corpo", key="cg3")
                chk3 = c4.checkbox("✔️ Concluído", key="chk3")
                if chk3:
                    registrar_exercicio_concluido("Treino A", "Flexão Tradicional", s3, r3, cg3)
                    st.success("Ex. 3 Salvo no Banco de Dados!")

            with st.container():
                st.markdown("""
                <div class="exercise-card">
                    <span class="badge-focus">Foco: Linha do "V" & Infra Solo</span>
                    <div class="ex-title">4. Elevação de Pernas Deitado no Solo</div>
                    <p style="color: #A0AEC0; margin-top: 5px;">Meta: 3 séries × 12–15 repetições | Descanso: 60s</p>
                </div>
                """, unsafe_allow_html=True)
                exibir_video_ou_link("elevacao_pernas.mp4", "http://www.youtube.com/watch?v=UJvmRQFjD0A")
                
                c1, c2, c3, c4 = st.columns([1, 1, 1.5, 1.5])
                s4 = c1.number_input("Séries", 1, 5, 3, key="s4")
                r4 = c2.number_input("Reps", 1, 30, 15, key="r4")
                cg4 = c3.text_input("Carga / Obs", "Corporal", key="cg4")
                chk4 = c4.checkbox("✔️ Concluído", key="chk4")
                if chk4:
                    registrar_exercicio_concluido("Treino A", "Elevação de Pernas Deitado", s4, r4, cg4)
                    st.success("Ex. 4 Salvo no Banco de Dados!")

            st.divider()
            if st.button("🚀 FINALIZAR E CONCLUIR TREINO A DE HOJE", use_container_width=True):
                registrar_sessao_completa("Treino A", 4, "Sessão A concluída com sucesso!")
                st.balloons()
                st.success("Sessão Treino A gravada no seu Relatório de Performance!")

        elif "Terça" in dia_selecionado:
            st.subheader("⚡ Terça-Feira — Treino B: Ombros & Abdômen")
            exibir_video_ou_link("flexao_pike.mp4", "http://www.youtube.com/watch?v=7gEKqSbLYTM")
            if st.checkbox("✔️ Marcar Flexão Pike como Concluída", key="chkb1"):
                registrar_exercicio_concluido("Treino B", "Flexão Pike", 3, 10, "Corporal")
                st.success("Registrado!")

        elif "Quarta" in dia_selecionado:
            st.subheader("⚡ Quarta-Feira — Treino C: Costas & Postura")
            exibir_video_ou_link("remada_mesa.mp4", "http://www.youtube.com/watch?v=H_e8c1Mfh9g")
            if st.checkbox("✔️ Marcar Remada Invertida como Concluída", key="chkc1"):
                registrar_exercicio_concluido("Treino C", "Remada Invertida na Mesa", 3, 10, "Corporal")
                st.success("Registrado!")

        elif "Quinta" in dia_selecionado:
            st.info("🏃‍♂️ Quinta-Feira: Descanso Ativo (15 a 20 minutos de caminhada leve ou regeneração total).")

        elif "Sexta" in dia_selecionado:
            st.subheader("⚡ Sexta-Feira — Treino D: Hipertrofia do Tronco")
            exibir_video_ou_link("flexao_pes_elevados.mp4", "http://www.youtube.com/watch?v=bpjqDjXBv-M")
            if st.checkbox("✔️ Marcar Treino D como Concluído", key="chkd1"):
                registrar_exercicio_concluido("Treino D", "Flexão Pés Elevados", 4, 10, "Corporal")
                st.success("Registrado!")

    with aba_selecionada[1]:
        st.subheader("📊 Painel de Performance e Histórico")
        
        conn = sqlite3.connect("treino_database.db")
        c = conn.cursor()
        
        c.execute("SELECT COUNT(*) FROM sessoes_treino")
        total_sessoes = c.fetchone()[0]
        
        c.execute("SELECT COUNT(*) FROM conclusoes_exercicios WHERE concluido = 1")
        total_exercicios = c.fetchone()[0]
        
        m1, m2 = st.columns(2)
        with m1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_sessoes}</div>
                <div class="stat-label">Sessões Completas</div>
            </div>
            """, unsafe_allow_html=True)
            
        with m2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{total_exercicios}</div>
                <div class="stat-label">Exercícios Concluídos</div>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        st.subheader("📋 Log Registrado por Exercício")
        
        c.execute("SELECT data, dia_treino, exercicio, series, reps, carga FROM conclusoes_exercicios ORDER BY id DESC")
        linhas = c.fetchall()
        
        if linhas:
            for r in linhas:
                st.markdown(f"""
                <div class="log-card">
                    <span style="color: #FF003C; font-weight: bold;">📅 {r[0]} | {r[1]}</span><br>
                    <span style="font-size: 1.1rem; color: #FFF;">✔️ <b>{r[2]}</b></span> — {r[3]} séries × {r[4]} reps <span style="color: #A0AEC0;">({r[5]})</span>
                </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum registro no banco de dados ainda. Faça seu treino e marque o checklist!")

        conn.close()

    with aba_selecionada[2]:
        st.subheader("📖 Guia Muscular & Mecânica dos Exercícios")
        st.markdown("""
* **Flexão com Pés Elevados (Declinada):** Coloca o peitoral superior (porção clavicular) e deltoide anterior no ponto de maior tensão.
* **Flexão Diamante:** Enfatiza a porção interna (miolo do peito) e força do tríceps.
* **Flexão Pike:** Trabalha a cabeça lateral e anterior dos ombros para criar largura de ombros.
* **Elevação de Pernas Deitado:** Ao elevar o quadril no topo do movimento, isola perfeitamente a linha do "V" infra-abdominal.
* **Remada Invertida na Mesa:** Equilibra a força da musculatura dorsal e projeta o peitoral para a frente.
        """)
