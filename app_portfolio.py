"""
Simulador de Portafolio de Inversión — Streamlit App
=====================================================
Interfaz para armar un portafolio con activos reales
y analizar retorno esperado, volatilidad y evolución histórica.

Autor: Curso Python
Versión: 1.1 - Fixes de compatibilidad con Streamlit 1.54 y Plotly 6.x
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
from portfolio_model import PortfolioAnalyzer, ACTIVOS

# ─────────────────────────────────────────────
# CONFIGURACIÓN DE PÁGINA
# ─────────────────────────────────────────────
st.set_page_config(
    page_title="Simulador de Portafolio",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=DM+Sans:wght@300;400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'DM Sans', sans-serif;
        background-color: #f7f5f0;
        color: #1a1a1a;
    }
    h1 {
        font-family: 'Syne', sans-serif;
        font-weight: 800;
        color: #1a1a1a;
        letter-spacing: -2px;
        font-size: 2.8rem;
    }
    h2, h3 { font-family: 'Syne', sans-serif; color: #1a1a1a; }

    .stButton>button {
        background-color: #1a1a1a;
        color: #f7f5f0;
        font-family: 'Syne', sans-serif;
        font-weight: 700;
        border: none;
        border-radius: 0px;
        padding: 0.75rem 2rem;
        width: 100%;
        font-size: 0.95rem;
        letter-spacing: 1px;
        text-transform: uppercase;
    }
    .stButton>button:hover { background-color: #333; }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e0ddd5;
        padding: 1.5rem;
        margin: 0.3rem 0;
    }
    .metric-value {
        font-family: 'Syne', sans-serif;
        font-size: 2.5rem;
        font-weight: 800;
        line-height: 1;
        margin: 0.3rem 0;
    }
    .metric-label {
        font-size: 0.75rem;
        letter-spacing: 2px;
        text-transform: uppercase;
        color: #888;
    }
    .positive { color: #1a7a4a; }
    .negative { color: #c0392b; }
    .neutral  { color: #1a1a1a; }
    .warning-text {
        font-size: 0.8rem;
        color: #888;
        font-style: italic;
        margin-top: 0.5rem;
    }
    </style>
""", unsafe_allow_html=True)

# ─────────────────────────────────────────────
# SIDEBAR
# ─────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📈 Configurar Portafolio")
    st.markdown("---")

    nombres_activos = list(ACTIVOS.keys())
    seleccionados = st.multiselect(
        "Seleccioná los activos",
        options=nombres_activos,
        default=["Apple (AAPL)", "MercadoLibre (MELI)", "Tesla (TSLA)"],
    )

    periodo = st.selectbox(
        "Período histórico",
        options=["6mo", "1y", "2y", "5y"],
        index=1,
        format_func=lambda x: {
            "6mo": "6 meses", "1y": "1 año", "2y": "2 años", "5y": "5 años"
        }[x],
    )

    st.markdown("---")

    pesos_input = {}
    if seleccionados:
        st.markdown("**Pesos del portafolio (%)**")
        peso_default = int(100 / len(seleccionados))
        total = 0
        for nombre in seleccionados:
            ticker = ACTIVOS[nombre]
            peso = st.slider(
                f"{nombre.split('(')[0].strip()}",
                min_value=0, max_value=100,
                value=peso_default, step=5,
                key=f"peso_{ticker}"
            )
            pesos_input[ticker] = peso
            total += peso

        if total != 100:
            st.warning(f"Los pesos suman {total}%. Se normalizarán automáticamente a 100%.")
        else:
            st.success("✓ Los pesos suman 100%")

    st.markdown("---")
    analizar = st.button("▶  ANALIZAR PORTAFOLIO")

# ─────────────────────────────────────────────
# ENCABEZADO
# ─────────────────────────────────────────────
st.markdown("# Simulador de Portafolio")
st.markdown("Datos reales desde Yahoo Finance · Curso Python")
st.markdown("---")

# ─────────────────────────────────────────────
# ANÁLISIS
# ─────────────────────────────────────────────
if analizar:
    if not seleccionados:
        st.warning("Seleccioná al menos un activo para continuar.")
    elif sum(pesos_input.values()) == 0:
        st.warning("Asigná pesos mayores a 0 para continuar.")
    else:
        tickers   = [ACTIVOS[n] for n in seleccionados]
        pesos_dec = {t: p / 100 for t, p in pesos_input.items()}

        with st.spinner("Descargando datos desde Yahoo Finance..."):
            try:
                analyzer  = PortfolioAnalyzer(tickers, periodo)
                resultado = analyzer.analizar_portafolio(pesos_dec)
                metricas  = analyzer.metricas_individuales()
                st.session_state.analyzer      = analyzer
                st.session_state.resultado     = resultado
                st.session_state.metricas      = metricas
                st.session_state.seleccionados = seleccionados
                st.session_state.pesos_input   = pesos_input
            except Exception as e:
                st.error(f"Error al descargar datos: {e}")
                st.stop()

# ─────────────────────────────────────────────
# RESULTADOS
# ─────────────────────────────────────────────
if "resultado" in st.session_state:
    r        = st.session_state.resultado
    ana      = st.session_state.analyzer
    metricas = st.session_state.metricas

    # KPIs
    col1, col2, col3, col4 = st.columns(4)
    ret_color  = "positive" if r["retorno_anual"] >= 0 else "negative"
    draw_color = "negative" if r["max_drawdown"]  < -15 else "neutral"

    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Retorno Anual Est.</p>
            <p class="metric-value {ret_color}">{r['retorno_anual']:+.1f}%</p>
        </div>""", unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Volatilidad Anual</p>
            <p class="metric-value neutral">{r['volatilidad']:.1f}%</p>
        </div>""", unsafe_allow_html=True)

    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Sharpe Ratio</p>
            <p class="metric-value neutral">{r['sharpe']:.2f}</p>
        </div>""", unsafe_allow_html=True)

    with col4:
        st.markdown(f"""
        <div class="metric-card">
            <p class="metric-label">Máx. Drawdown</p>
            <p class="metric-value {draw_color}">{r['max_drawdown']:.1f}%</p>
        </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["📈 Evolución", "📊 Activos Individuales", "🔗 Correlaciones"])

    # Tab 1
    with tab1:
        fig = go.Figure()
        fig.add_trace(go.Scatter(
            x=r["fechas"], y=r["evolucion"],
            mode="lines", name="Mi Portafolio",
            line=dict(color="#1a1a1a", width=3),
            fill="tozeroy", fillcolor="rgba(26,26,26,0.05)",
        ))
        fig.add_hline(y=100, line_dash="dot", line_color="#aaa",
                      annotation_text="Base 100", annotation_position="right")
        fig.update_layout(
            title="Evolución del Portafolio (Base 100)",
            xaxis_title="Fecha", yaxis_title="Valor (Base 100)",
            height=450, template="plotly_white", hovermode="x unified",
            legend=dict(orientation="h", yanchor="bottom", y=1.02),
        )
        st.plotly_chart(fig, width="stretch")
        st.markdown('<p class="warning-text">* Retorno histórico no garantiza rendimiento futuro. Solo con fines educativos.</p>',
                    unsafe_allow_html=True)

    # Tab 2
    with tab2:
        col_a, col_b = st.columns([2, 1])

        with col_a:
            # FIX 1: renombrar columna índice para compatibilidad con Plotly 6.x
            df_scatter = metricas.reset_index()
            df_scatter = df_scatter.rename(columns={df_scatter.columns[0]: "Ticker"})
            fig2 = px.scatter(
                df_scatter,
                x="Volatilidad Anual (%)", y="Retorno Anual (%)",
                text="Ticker",
                size=[20] * len(df_scatter),
                color="Sharpe Ratio", color_continuous_scale="RdYlGn",
                title="Retorno vs Riesgo por Activo",
            )
            fig2.update_traces(textposition="top center", marker=dict(sizemode="diameter"))
            fig2.add_hline(y=0, line_dash="dot", line_color="#ccc")
            fig2.update_layout(height=400, template="plotly_white")
            st.plotly_chart(fig2, width="stretch")

        with col_b:
            st.markdown("### Tabla de Métricas")
            # FIX 2: eliminado background_gradient (requiere matplotlib, no instalado en Streamlit Cloud)
            st.dataframe(
                metricas.style.format({
                    "Retorno Anual (%)":     "{:+.2f}%",
                    "Volatilidad Anual (%)": "{:.2f}%",
                    "Sharpe Ratio":          "{:.2f}",
                }),
                width="stretch",
            )

        pesos_norm  = st.session_state.pesos_input
        total_pesos = sum(pesos_norm.values())
        labels = [n.split("(")[0].strip() for n in st.session_state.seleccionados]
        values = [pesos_norm[ACTIVOS[n]] / total_pesos * 100 for n in st.session_state.seleccionados]

        fig3 = go.Figure(go.Pie(
            labels=labels, values=values, hole=0.45,
            marker=dict(colors=px.colors.qualitative.G10),
        ))
        fig3.update_layout(title="Composición del Portafolio", height=350, template="plotly_white")
        st.plotly_chart(fig3, width="stretch")

    # Tab 3
    with tab3:
        if len(ana.retornos.columns) > 1:
            corr = ana.matriz_correlacion()
            fig4 = px.imshow(
                corr, text_auto=True,
                color_continuous_scale="RdYlGn", zmin=-1, zmax=1,
                title="Matriz de Correlación entre Activos", aspect="auto",
            )
            fig4.update_layout(height=450, template="plotly_white")
            st.plotly_chart(fig4, width="stretch")
            st.info("💡 Correlaciones cercanas a -1 indican activos que se mueven en sentidos opuestos, lo que **reduce el riesgo** del portafolio.")
        else:
            st.info("Seleccioná más de un activo para ver correlaciones.")

else:
    st.markdown("""
    <div style="text-align:center; padding: 4rem 2rem; color:#bbb;">
        <p style="font-size:5rem; margin:0;">📈</p>
        <p style="font-family:'Syne',sans-serif; font-size:1.2rem; color:#aaa; margin-top:1rem;">
            Elegí los activos y los pesos en el panel izquierdo<br>
            y hacé clic en <strong style="color:#1a1a1a;">ANALIZAR PORTAFOLIO</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)

# ─────────────────────────────────────────────
# FOOTER
# ─────────────────────────────────────────────
st.markdown("---")
st.markdown("""
<p style="text-align:center; color:#aaa; font-size:0.75rem;">
    Simulador de Portafolio · Datos: Yahoo Finance · Solo con fines educativos
</p>
""", unsafe_allow_html=True)
