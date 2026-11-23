import base64
import datetime
import os
import sqlite3
import pandas as pd
import plotly.express as px
import streamlit as st

st.set_page_config(
    page_title="Painel Financeiro Pro",
    page_icon="💠",
    layout="wide",
    initial_sidebar_state="expanded",
)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "fluxo_pro.db")
ICON_DIR = os.path.join(BASE_DIR, "icones")

BANCOS_INFO = {
    "PicPay": {"emoji": "🟢", "arquivo": "picpay"},
    "Nubank": {"emoji": "🟣", "arquivo": "nubank"},
    "Inter": {"emoji": "🟧", "arquivo": "inter"},
    "Bradesco": {"emoji": "🔴", "arquivo": "bradesco"},
    "Itaú": {"emoji": "🟠", "arquivo": "itau"},
    "Mercado Pago": {"emoji": "🔵", "arquivo": "mercadopago"},
    "Caixa": {"emoji": "🔷", "arquivo": "caixa"},
    "Santander": {"emoji": "🔺", "arquivo": "santander"},
    "Dinheiro / Pix": {"emoji": "💵", "arquivo": "pix"},
    "Outro Banco": {"emoji": "🏦", "arquivo": "outro"},
}

CATEGORIAS = [
    "💳 Cartão de Crédito",
    "👨‍👩‍👦 Acertos / Família",
    "📚 Cursos & Estudos",
    "🎯 Metas & Reservas",
    "🍔 Alimentação",
    "🏠 Casa & Contas",
    "💻 PC & Eletrônicos",
    "📦 Outros",
]

MESES_PT = {
    1: "Janeiro",
    2: "Fevereiro",
    3: "Março",
    4: "Abril",
    5: "Maio",
    6: "Junho",
    7: "Julho",
    8: "Agosto",
    9: "Setembro",
    10: "Outubro",
    11: "Novembro",
    12: "Dezembro",
}

MES_NOME_PARA_NUM = {nome: num for num, nome in MESES_PT.items()}

st.markdown(
    """
    <style>
        .block-container {
            padding-top: 1.4rem;
            padding-bottom: 2rem;
        }
        div[data-testid="stMetric"] {
            background-color: #111827;
            border: 1px solid rgba(56, 189, 248, 0.32);
            border-radius: 12px;
            padding: 14px 18px;
        }
        div[data-testid="stMetricLabel"] > div {
            color: #94A3B8;
            font-size: 0.85rem;
        }
        div[data-testid="stMetricValue"] > div {
            color: #38BDF8;
            font-weight: 700;
        }
        .stButton > button, .stFormSubmitButton > button {
            border-radius: 8px;
            border: 1px solid #38BDF8;
            font-weight: 600;
        }
        section[data-testid="stSidebar"] {
            background-color: #0D1322;
            border-right: 1px solid rgba(56, 189, 248, 0.18);
        }
        .banco-badge {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
        }
        .banco-badge img {
            width: 22px;
            height: 22px;
            border-radius: 6px;
            object-fit: cover;
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def buscar_caminho_icone(banco_nome):
    info = BANCOS_INFO.get(banco_nome, {"arquivo": "outro"})
    base = info["arquivo"].lower()
    if not os.path.isdir(ICON_DIR):
        return None
    for nome_arq in os.listdir(ICON_DIR):
        nome_sem_ext, ext = os.path.splitext(nome_arq)
        if nome_sem_ext.lower() == base and ext.lower() in [".png", ".jpg", ".jpeg", ".webp"]:
            return os.path.join(ICON_DIR, nome_arq)
    return None


def render_banco_html(banco_nome):
    caminho = buscar_caminho_icone(banco_nome)
    emoji = BANCOS_INFO.get(banco_nome, {"emoji": "🏦"})["emoji"]
    if caminho:
        ext = os.path.splitext(caminho)[1].lower().replace(".", "")
        if ext == "jpg":
            ext = "jpeg"
        try:
            with open(caminho, "rb") as f:
                b64 = base64.b64encode(f.read()).decode("utf-8")
            if b64:
                return f'<span class="banco-badge"><img src="data:image/{ext};base64,{b64}"/> {banco_nome}</span>'
        except OSError:
            pass
    return f'<span class="banco-badge">{emoji} {banco_nome}</span>'


def get_conn():
    return sqlite3.connect(DB_FILE, check_same_thread=False)


def init_db():
    c = get_conn()
    cur = c.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS config (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            salario REAL NOT NULL
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS renda_mensal (
            ano INTEGER NOT NULL,
            mes INTEGER NOT NULL,
            meu_salario REAL NOT NULL DEFAULT 1800.0,
            usar_mulher INTEGER NOT NULL DEFAULT 0,
            salario_mulher REAL NOT NULL DEFAULT 0.0,
            PRIMARY KEY (ano, mes)
        )
        """
    )
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS lancamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data_lancamento TEXT NOT NULL,
            banco TEXT NOT NULL,
            categoria TEXT NOT NULL,
            nome TEXT NOT NULL,
            quantidade INTEGER NOT NULL DEFAULT 1,
            valor REAL NOT NULL,
            status TEXT NOT NULL DEFAULT 'Pendente'
        )
        """
    )
    cur.execute("INSERT OR IGNORE INTO config (id, salario) VALUES (1, 1800.0)")
    c.commit()
    c.close()


def get_salario_base():
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT salario FROM config WHERE id = 1")
    row = cur.fetchone()
    c.close()
    return float(row[0]) if row else 1800.0


def set_salario_base(valor):
    c = get_conn()
    cur = c.cursor()
    cur.execute("UPDATE config SET salario = ? WHERE id = 1", (float(valor),))
    c.commit()
    c.close()


def get_renda_mes(ano, mes):
    salario_padrao = get_salario_base()
    c = get_conn()
    cur = c.cursor()
    cur.execute("SELECT meu_salario, usar_mulher, salario_mulher FROM renda_mensal WHERE ano = ? AND mes = ?", (int(ano), int(mes)))
    row = cur.fetchone()
    c.close()
    if row:
        return {
            "meu_salario": float(row[0]),
            "usar_mulher": bool(row[1]),
            "salario_mulher": float(row[2]),
        }
    return {
        "meu_salario": salario_padrao,
        "usar_mulher": False,
        "salario_mulher": 0.0,
    }


def salvar_renda_mes(ano, mes, meu_salario, usar_mulher, salario_mulher):
    c = get_conn()
    cur = c.cursor()
    cur.execute(
        """
        INSERT INTO renda_mensal (ano, mes, meu_salario, usar_mulher, salario_mulher)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(ano, mes) DO UPDATE SET
            meu_salario = excluded.meu_salario,
            usar_mulher = excluded.usar_mulher,
            salario_mulher = excluded.salario_mulher
        """,
        (int(ano), int(mes), float(meu_salario), 1 if usar_mulher else 0, float(salario_mulher)),
    )
    c.commit()
    c.close()


def calcular_renda_total_mes(ano, mes):
    renda = get_renda_mes(ano, mes)
    meu = renda["meu_salario"]
    mulher = renda["salario_mulher"] if renda["usar_mulher"] else 0.0
    return meu + mulher, meu, mulher, renda["usar_mulher"]


def carregar_lancamentos():
    c = get_conn()
    df = pd.read_sql_query(
        """
        SELECT id, data_lancamento, banco, categoria, nome, quantidade, valor, status
        FROM lancamentos
        ORDER BY data_lancamento DESC, id DESC
        """,
        c,
    )
    c.close()
    if df.empty:
        return pd.DataFrame(
            columns=["id", "data_lancamento", "banco", "categoria", "nome", "quantidade", "valor", "total", "status", "ano", "mes", "mes_nome"]
        )
    df["data_dt"] = pd.to_datetime(df["data_lancamento"], errors="coerce")
    df["ano"] = df["data_dt"].dt.year.fillna(datetime.date.today().year).astype(int)
    df["mes"] = df["data_dt"].dt.month.fillna(datetime.date.today().month).astype(int)
    df["mes_nome"] = df["mes"].map(MESES_PT)
    df["total"] = df["quantidade"] * df["valor"]
    return df


def adicionar_lancamento(data_str, banco, categoria, nome, quantidade, valor, status):
    c = get_conn()
    cur = c.cursor()
    cur.execute(
        """
        INSERT INTO lancamentos (data_lancamento, banco, categoria, nome, quantidade, valor, status)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (data_str, banco, categoria, nome.strip(), int(quantidade), float(valor), status),
    )
    c.commit()
    c.close()


def alternar_status(item_id, status_atual):
    novo = "Pago" if status_atual == "Pendente" else "Pendente"
    c = get_conn()
    cur = c.cursor()
    cur.execute("UPDATE lancamentos SET status = ? WHERE id = ?", (novo, int(item_id)))
    c.commit()
    c.close()


def excluir_lancamento(item_id):
    c = get_conn()
    cur = c.cursor()
    cur.execute("DELETE FROM lancamentos WHERE id = ?", (int(item_id),))
    c.commit()
    c.close()


def excluir_varios_lancamentos(ids_lista):
    if not ids_lista:
        return
    ids_limpos = [int(x) for x in ids_lista]
    placeholders = ",".join("?" for _ in ids_limpos)
    c = get_conn()
    cur = c.cursor()
    cur.execute(f"DELETE FROM lancamentos WHERE id IN ({placeholders})", ids_limpos)
    c.commit()
    c.close()


def brl(v):
    return f"R$ {v:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


init_db()
df_all = carregar_lancamentos()
hoje = datetime.date.today()

if "aba_ativa" not in st.session_state:
    st.session_state["aba_ativa"] = "lancamentos"

with st.sidebar:
    st.markdown("## 💠 Controle Pro")
    st.caption("Salário padrão (VT já descontado)")
    salario_base_atual = get_salario_base()
    novo_salario_base = st.number_input(
        "Meu salário padrão (R$)",
        min_value=0.0,
        step=50.0,
        value=salario_base_atual,
        format="%.2f",
        key="cfg_salario_base",
    )
    if novo_salario_base != salario_base_atual:
        set_salario_base(novo_salario_base)
        st.rerun()

    st.markdown("---")
    if st.button("📋 Lançamentos & Bancos", width="stretch", type="primary" if st.session_state["aba_ativa"] == "lancamentos" else "secondary"):
        st.session_state["aba_ativa"] = "lancamentos"
        st.rerun()
    if st.button("📊 Gráficos Completos", width="stretch", type="primary" if st.session_state["aba_ativa"] == "graficos" else "secondary"):
        st.session_state["aba_ativa"] = "graficos"
        st.rerun()
    if st.button("📅 Histórico por Mês e Ano", width="stretch", type="primary" if st.session_state["aba_ativa"] == "historico" else "secondary"):
        st.session_state["aba_ativa"] = "historico"
        st.rerun()

    st.markdown("---")
    icones_detectados = sum(1 for b in BANCOS_INFO if buscar_caminho_icone(b) is not None)
    st.caption(f"🖼️ Ícones na pasta `icones/`: {icones_detectados} encontrados")
    st.caption("💾 Salvamento automático em `fluxo_pro.db`")

if st.session_state["aba_ativa"] == "lancamentos":
    st.markdown("## 📋 Lançamentos, Cartões e Classificações")

    anos_disp = sorted(list(set(df_all["ano"].tolist() + [hoje.year, hoje.year + 1])), reverse=True)
    f1, f2, _ = st.columns([1.2, 1.5, 3])
    ano_sel = f1.selectbox("Ano", anos_disp, index=0)
    mes_opcoes = ["Todos os meses"] + [MESES_PT[m] for m in range(1, 13)]
    mes_sel_nome = f2.selectbox("Mês de referência", mes_opcoes, index=hoje.month)

    mes_num_filtro = MES_NOME_PARA_NUM.get(mes_sel_nome, hoje.month)
    if mes_num_filtro == 12:
        data_padrao_form = datetime.date(ano_sel, 12, hoje.day if hoje.day <= 31 else 1)
    else:
        data_padrao_form = datetime.date(ano_sel, mes_num_filtro, min(hoje.day, 28))

    st.markdown(f"### 💰 Renda do Mês — {MESES_PT.get(mes_num_filtro, mes_sel_nome)}/{ano_sel}")
    if mes_sel_nome == "Todos os meses":
        renda_total_mes = sum(calcular_renda_total_mes(ano_sel, m)[0] for m in range(1, 13))
        st.caption("Somatório da renda configurada para cada mês do ano selecionado.")
    else:
        renda_atual_mes = get_renda_mes(ano_sel, mes_num_filtro)
        r_col1, r_col2, r_col3 = st.columns([1.5, 1.6, 1.5])
        with r_col1:
            meu_sal_mes = st.number_input(
                f"Meu salário em {MESES_PT[mes_num_filtro]} (R$)",
                min_value=0.0,
                step=50.0,
                value=float(renda_atual_mes["meu_salario"]),
                format="%.2f",
                key=f"meu_sal_{ano_sel}_{mes_num_filtro}",
            )
        with r_col2:
            st.write("")
            usar_mulher_mes = st.checkbox(
                "Somar salário da minha mulher nesse mês?",
                value=bool(renda_atual_mes["usar_mulher"]),
                key=f"chk_mulher_{ano_sel}_{mes_num_filtro}",
            )
        with r_col3:
            sal_mulher_mes = st.number_input(
                "Salário da mulher nesse mês (R$)",
                min_value=0.0,
                step=50.0,
                value=float(renda_atual_mes["salario_mulher"]),
                format="%.2f",
                disabled=not usar_mulher_mes,
                key=f"sal_mulher_{ano_sel}_{mes_num_filtro}",
            )

        if (
            float(meu_sal_mes) != float(renda_atual_mes["meu_salario"])
            or bool(usar_mulher_mes) != bool(renda_atual_mes["usar_mulher"])
            or float(sal_mulher_mes) != float(renda_atual_mes["salario_mulher"])
        ):
            salvar_renda_mes(ano_sel, mes_num_filtro, meu_sal_mes, usar_mulher_mes, sal_mulher_mes)
            st.rerun()

        renda_total_mes = float(meu_sal_mes) + (float(sal_mulher_mes) if usar_mulher_mes else 0.0)
        if usar_mulher_mes:
            st.caption(f"Renda conjunta salva só para {MESES_PT[mes_num_filtro]}/{ano_sel}: {brl(float(meu_sal_mes))} + {brl(float(sal_mulher_mes))} = **{brl(renda_total_mes)}**")
        else:
            st.caption(f"Renda salva só para {MESES_PT[mes_num_filtro]}/{ano_sel}: **{brl(renda_total_mes)}** (apenas seu salário)")

    df_filtrado = df_all[df_all["ano"] == ano_sel].copy()
    if mes_sel_nome != "Todos os meses":
        df_filtrado = df_filtrado[df_filtrado["mes_nome"] == mes_sel_nome]

    total_gastos = float(df_filtrado["total"].sum()) if not df_filtrado.empty else 0.0
    total_cartoes = float(df_filtrado[df_filtrado["categoria"] == "💳 Cartão de Crédito"]["total"].sum()) if not df_filtrado.empty else 0.0
    sobra = renda_total_mes - total_gastos
    pct_sobra = (sobra / renda_total_mes * 100) if renda_total_mes > 0 else 0.0

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Renda do Período", brl(renda_total_mes))
    m2.metric("Gastos no Período", brl(total_gastos))
    m3.metric("Dívida em Cartões", brl(total_cartoes))
    m4.metric("Sobra Livre", f"{brl(sobra)} ({pct_sobra:.1f}%)")

    st.divider()

    st.markdown("### ➕ Novo Lançamento")
    st.caption("Dica: para fatura de cartão que só fecha/cai no mês seguinte, escolha a data de vencimento/competência no campo Data (ex.: em dezembro).")
    with st.form("form_novo", clear_on_submit=True):
        c1, c2, c3, c4 = st.columns([1.3, 1.5, 1.7, 2.2])
        data_inp = c1.date_input("Data (mês do gasto/fatura)", value=data_padrao_form, format="DD/MM/YYYY")
        banco_inp = c2.selectbox("Banco / Carteira", list(BANCOS_INFO.keys()), format_func=lambda k: f"{BANCOS_INFO[k]['emoji']} {k}")
        cat_inp = c3.selectbox("Classificação", CATEGORIAS)
        nome_inp = c4.text_input("Nome do gasto", placeholder="Digite o nome...")

        c5, c6, c7, c8 = st.columns([1, 1.4, 1.4, 1.4])
        qtd_inp = c5.number_input("Qtd", min_value=1, step=1, value=1)
        val_inp = c6.number_input("Valor (R$)", min_value=0.0, step=10.0, value=0.0, format="%.2f")
        status_inp = c7.selectbox("Situação", ["Pendente", "Pago"])
        with c8:
            st.write("")
            st.write("")
            salvar_btn = st.form_submit_button("💾 Salvar", width="stretch")

        if salvar_btn:
            if nome_inp.strip():
                adicionar_lancamento(data_inp.isoformat(), banco_inp, cat_inp, nome_inp, qtd_inp, val_inp, status_inp)
                st.rerun()
            else:
                st.warning("Digite o nome do gasto antes de salvar.")

    st.divider()

    col_lista, col_resumos = st.columns([1.65, 1])

    with col_lista:
        cab_esq, cab_dir = st.columns([2.2, 1.2])
        with cab_esq:
            st.markdown("### 📑 Lista de Gastos (com lixeira direta ao lado)")
        with cab_dir:
            if not df_filtrado.empty:
                if st.button("🗑️ Excluir tudo do filtro", key="del_tudo_filtro", width="stretch"):
                    excluir_varios_lancamentos(df_filtrado["id"].tolist())
                    st.rerun()

        if df_filtrado.empty:
            st.info("Nenhum lançamento encontrado nesse filtro.")
        else:
            for _, r in df_filtrado.iterrows():
                item_id = int(r["id"])
                data_fmt = pd.to_datetime(r["data_lancamento"]).strftime("%d/%m/%Y")
                banco_html = render_banco_html(r["banco"])
                total_fmt = brl(float(r["total"]))
                qtd_int = int(r["quantidade"])
                status_str = str(r["status"])

                c_info, c_val, c_st, c_del = st.columns([3.3, 1.3, 1.1, 0.55])
                with c_info:
                    st.markdown(
                        f"**{r['nome']}** ({qtd_int}x) • `{data_fmt}`\n\n"
                        f"{banco_html} &nbsp;|&nbsp; {r['categoria']}",
                        unsafe_allow_html=True,
                    )
                with c_val:
                    st.markdown(f"**{total_fmt}**")
                with c_st:
                    icone_st = "✅ Pago" if status_str == "Pago" else "⏳ Pendente"
                    if st.button(icone_st, key=f"st_{item_id}", width="stretch"):
                        alternar_status(item_id, status_str)
                        st.rerun()
                with c_del:
                    if st.button("🗑️", key=f"del_{item_id}", help="Excluir este item"):
                        excluir_lancamento(item_id)
                        st.rerun()
                st.markdown("<hr style='margin:6px 0; border-color: rgba(148,163,184,0.15);'/>", unsafe_allow_html=True)

    with col_resumos:
        st.markdown("### 🏦 Total por Banco")
        if df_filtrado.empty:
            st.info("Sem dados.")
        else:
            por_banco = (
                df_filtrado.groupby("banco", as_index=False)["total"]
                .sum()
                .sort_values("total", ascending=False)
            )
            for _, rb in por_banco.iterrows():
                b_col1, b_col2 = st.columns([2, 1.2])
                with b_col1:
                    st.markdown(render_banco_html(rb["banco"]), unsafe_allow_html=True)
                with b_col2:
                    st.markdown(f"**{brl(float(rb['total']))}**")

        st.markdown("---")
        st.markdown("### 🗂️ Resumo por Classificação")
        if df_filtrado.empty:
            st.info("Sem dados.")
        else:
            por_cat = (
                df_filtrado.groupby("categoria", as_index=False)["total"]
                .sum()
                .sort_values("total", ascending=False)
            )
            por_cat["% Renda"] = por_cat["total"].map(
                lambda x: f"{(x / renda_total_mes * 100):.1f}%" if renda_total_mes > 0 else "0.0%"
            )
            por_cat["Valor"] = por_cat["total"].map(brl)
            st.dataframe(
                por_cat[["categoria", "Valor", "% Renda"]].rename(columns={"categoria": "Classificação"}),
                hide_index=True,
                width="stretch",
            )

elif st.session_state["aba_ativa"] == "graficos":
    st.markdown("## 📊 Painel de Gráficos")
    st.caption("Visualização separada dos gastos por banco, classificação e evolução mensal.")

    if df_all.empty:
        st.info("Cadastre lançamentos na primeira aba para visualizar os gráficos.")
    else:
        anos_disp = sorted(df_all["ano"].unique().tolist(), reverse=True)
        g1, g2, _ = st.columns([1.2, 1.5, 3])
        ano_g = g1.selectbox("Ano", anos_disp, index=0, key="ano_graf")
        meses_g = ["Todos os meses"] + [MESES_PT[m] for m in range(1, 13)]
        mes_g_nome = g2.selectbox("Mês", meses_g, index=0, key="mes_graf")

        df_g = df_all[df_all["ano"] == ano_g].copy()
        if mes_g_nome != "Todos os meses":
            df_g = df_g[df_g["mes_nome"] == mes_g_nome]

        if df_g.empty:
            st.warning("Sem lançamentos nesse período.")
        else:
            col_g1, col_g2 = st.columns(2)

            with col_g1:
                st.markdown("### 🏦 Total por Banco / Cartão")
                gb = df_g.groupby("banco", as_index=False)["total"].sum().sort_values("total", ascending=True)
                fig_banco = px.bar(
                    gb,
                    x="total",
                    y="banco",
                    orientation="h",
                    text_auto=".2f",
                    labels={"total": "Total (R$)", "banco": "Banco"},
                    color_discrete_sequence=["#38BDF8"],
                )
                fig_banco.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    font_color="#F8FAFC",
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=370,
                )
                st.plotly_chart(fig_banco, width="stretch")

            with col_g2:
                st.markdown("### 🗂️ Distribuição por Classificação")
                gc = df_g.groupby("categoria", as_index=False)["total"].sum()
                fig_cat = px.pie(
                    gc,
                    values="total",
                    names="categoria",
                    hole=0.52,
                    color_discrete_sequence=["#38BDF8", "#0EA5E9", "#0284C7", "#22D3EE", "#6366F1", "#10B981", "#F59E0B", "#EC4899"],
                )
                fig_cat.update_layout(
                    paper_bgcolor="#111827",
                    plot_bgcolor="#111827",
                    font_color="#F8FAFC",
                    margin=dict(l=10, r=10, t=20, b=10),
                    height=370,
                )
                st.plotly_chart(fig_cat, width="stretch")

            st.markdown("### 📈 Evolução de Gastos Mês a Mês no Ano")
            df_ano = df_all[df_all["ano"] == ano_g].copy()
            gm = df_ano.groupby(["mes", "mes_nome"], as_index=False)["total"].sum().sort_values("mes")
            fig_mes = px.bar(
                gm,
                x="mes_nome",
                y="total",
                text_auto=".2f",
                labels={"mes_nome": "Mês", "total": "Total Gasto (R$)"},
                color_discrete_sequence=["#0EA5E9"],
            )
            fig_mes.update_layout(
                paper_bgcolor="#111827",
                plot_bgcolor="#111827",
                font_color="#F8FAFC",
                margin=dict(l=10, r=10, t=20, b=10),
                height=340,
            )
            st.plotly_chart(fig_mes, width="stretch")

elif st.session_state["aba_ativa"] == "historico":
    st.markdown("## 📅 Histórico Completo por Ano, Mês e Dia")
    st.caption("Consulte quanto você gastou em cada mês e veja a lista completa por data.")

    if df_all.empty:
        st.info("Nenhum registro salvo ainda.")
    else:
        anos_hist = sorted(df_all["ano"].unique().tolist(), reverse=True)
        h1, h2, _ = st.columns([1.2, 1.8, 3])
        ano_h = h1.selectbox("Escolha o Ano", anos_hist, index=0, key="ano_hist")
        df_ano_h = df_all[df_all["ano"] == ano_h].copy()

        st.markdown(f"### 🗓️ Resumo Mensal de {ano_h}")
        resumo_mensal = (
            df_ano_h.groupby(["mes", "mes_nome"], as_index=False)
            .agg(qtd_itens=("id", "count"), total_gasto=("total", "sum"))
            .sort_values("mes")
        )
        def _sobra_mes(row):
            renda_m = calcular_renda_total_mes(ano_h, int(row["mes"]))[0]
            return brl(renda_m - float(row["total_gasto"]))
        def _renda_mes_fmt(row):
            return brl(calcular_renda_total_mes(ano_h, int(row["mes"]))[0])
        resumo_mensal["Renda do Mês"] = resumo_mensal.apply(_renda_mes_fmt, axis=1)
        resumo_mensal["Sobra Estimada"] = resumo_mensal.apply(_sobra_mes, axis=1)
        resumo_mensal["Total Gasto"] = resumo_mensal["total_gasto"].map(brl)
        st.dataframe(
            resumo_mensal[["mes_nome", "Renda do Mês", "qtd_itens", "Total Gasto", "Sobra Estimada"]].rename(
                columns={"mes_nome": "Mês", "qtd_itens": "Qtd. Lançamentos"}
            ),
            hide_index=True,
            width="stretch",
        )

        st.divider()

        meses_disponiveis = ["Todos"] + [MESES_PT[m] for m in sorted(df_ano_h["mes"].unique().tolist())]
        mes_h = h2.selectbox("Filtrar lista por Mês", meses_disponiveis, index=0)

        df_lista_h = df_ano_h.copy()
        if mes_h != "Todos":
            df_lista_h = df_lista_h[df_lista_h["mes_nome"] == mes_h]

        df_lista_h["Data"] = pd.to_datetime(df_lista_h["data_lancamento"]).dt.strftime("%d/%m/%Y")
        df_lista_h["Total"] = df_lista_h["total"].map(brl)

        st.markdown("### 🧾 Lista Detalhada por Data")
        st.dataframe(
            df_lista_h[["Data", "banco", "categoria", "nome", "quantidade", "Total", "status"]].rename(
                columns={
                    "banco": "Banco",
                    "categoria": "Classificação",
                    "nome": "Descrição",
                    "quantidade": "Qtd",
                    "status": "Status",
                }
            ),
            hide_index=True,
            width="stretch",
        )
