import sys
import datetime
import requests
import streamlit as st
import pandas as pd
import plotly.express as px

st.set_page_config(
    page_title="Estudio Mesa | Studio Financiero", 
    page_icon="🥖", 
    layout="wide",
    initial_sidebar_state="expanded"
)

SHEET_ID = "1skUG3vKZwXve0kvDSVUAl1Qhzke-oLH0UNYwMdP9SAc"
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbxFcWtq7oIgD_LiupwWhaJ5HD_wxJmtbnNJQXQ_wJC99rz4_b8QA0I3-Gz6IkVXfIHnMw/exec"

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }
    
    .main {
        background-color: #F8F9FA;
    }
    
    .kpi-card {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 20px 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #ECEEF1;
        transition: transform 0.2s ease;
        margin-bottom: 12px;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
    }
    .kpi-title {
        color: #718096;
        font-size: 0.82rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        margin-bottom: 6px;
    }
    .kpi-value {
        color: #1A202C;
        font-size: 1.75rem;
        font-weight: 800;
        margin-bottom: 4px;
    }
    .kpi-subtitle {
        font-size: 0.8rem;
        font-weight: 600;
    }
    .kpi-pos { color: #2E7D32; }
    .kpi-neg { color: #C62828; }
    .kpi-neu { color: #4A5568; }

    div[data-testid="stForm"] {
        background: #FFFFFF;
        border-radius: 16px;
        padding: 24px;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.04);
        border: 1px solid #ECEEF1;
    }
    
    button[kind="primary"], .stButton > button {
        background-color: #2D3748 !important;
        color: #FFFFFF !important;
        border-radius: 10px !important;
        border: none !important;
        font-weight: 600 !important;
        padding: 8px 16px !important;
    }
</style>
""", unsafe_allow_html=True)

def cargar_tabla(nombre_pestaña):
    pestaña_url = nombre_pestaña.replace(" ", "%20")
    url = f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/gviz/tq?tqx=out:csv&sheet={pestaña_url}"
    df = pd.read_csv(url)
    df.columns = df.columns.astype(str).str.strip()
    return df

def limpiar_numero(columna):
    return columna.astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

def enviar_registro(pestaña, fila):
    try:
        payload = {"accion": "agregar", "pestaña": pestaña, "fila": fila}
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return resp.json().get("status") == "success"
    except Exception:
        return False

def borrar_fila_remota(pestaña, fila_index):
    try:
        payload = {"accion": "borrar", "pestaña": pestaña, "fila_index": fila_index}
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        return resp.json().get("status") == "success"
    except Exception:
        return False

# --- BARRA LATERAL (SIDEBAR) ---
st.sidebar.markdown("### ✨ **Estudio Mesa**")
st.sidebar.caption("Panel de Control Financiero & Operativo")

# Botón directo para abrir Google Sheets en una nueva pestaña
st.sidebar.link_button(
    "📊 Abrir Google Sheets", 
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit", 
    use_container_width=True
)

if st.sidebar.button("🔄 Sincronizar Datos", use_container_width=True):
    st.cache_data.clear()

tab_dashboard, tab_registro = st.tabs(["📊 Balance Financiero", "📝 Registrar / Gestionar Operaciones"])

# --- PESTAÑA: REGISTRO Y GESTIÓN ---
with tab_registro:
    st.markdown("#### 📝 Registro Rápido de Operaciones")
    col_form1, col_form2 = st.columns(2)

    with col_form1:
        st.markdown("##### 🥖 Registrar Venta / Entrega")
        with st.form("form_venta", clear_on_submit=True):
            fecha_venta = st.date_input("Fecha", datetime.date.today(), key="v_fecha")
            cliente_venta = st.text_input("Cliente", placeholder="Ej. Ernestina Castro", key="v_cli")
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                prod_venta = st.selectbox("Producto", ["PROD01"], key="v_prod")
            with col_v2:
                unidades_venta = st.number_input("Unidades", min_value=1, step=1, value=1, key="v_cant")
            precio_venta = st.number_input("Precio Cobrado Unitario ($)", min_value=0.0, step=0.10, value=2.20, key="v_precio")
            submit_venta = st.form_submit_button("💾 Guardar Venta", use_container_width=True)

            if submit_venta:
                if cliente_venta:
                    if enviar_registro("Ventas", [str(fecha_venta), cliente_venta, prod_venta, int(unidades_venta), float(precio_venta)]):
                        st.success(f"✅ Venta registrada: {unidades_venta} u. para {cliente_venta}")
                        st.cache_data.clear()
                    else:
                        st.error("Error al registrar la venta.")
                else:
                    st.error("Ingresa el nombre del cliente.")

    with col_form2:
        st.markdown("##### 🛒 Registrar Compra / Gasto")
        
        col_btn_mo, _ = st.columns([1.5, 1])
        with col_btn_mo:
            if st.button("⚡ Registrar Mano de Obra de Lote ($20.00)", use_container_width=True):
                fecha_hoy = str(datetime.date.today())
                if enviar_registro("Gastos_Diarios", [fecha_hoy, "Operativos", "Mano de obra lote", 20.0]):
                    st.success("✅ Pago de $20.00 registrado exitosamente.")
                    st.cache_data.clear()
                else:
                    st.error("Error al registrar el pago de mano de obra.")

        with st.form("form_gasto", clear_on_submit=True):
            fecha_gasto = st.date_input("Fecha", datetime.date.today(), key="g_fecha")
            categoria_gasto = st.selectbox("Categoría", ["Insumos", "Empaques", "Operativos", "Servicios", "Otros"], key="g_cat")
            desc_gasto = st.text_input("Descripción", placeholder="Ej. Harina, empaques, gas", key="g_desc")
            monto_gasto = st.number_input("Monto Total Pagado ($)", min_value=0.0, step=0.50, key="g_monto")
            submit_gasto = st.form_submit_button("💾 Guardar Gasto", use_container_width=True)

            if submit_gasto:
                if desc_gasto and monto_gasto > 0:
                    if enviar_registro("Gastos_Diarios", [str(fecha_gasto), categoria_gasto, desc_gasto, float(monto_gasto)]):
                        st.success(f"✅ Gasto guardado: ${monto_gasto:.2f}")
                        st.cache_data.clear()
                    else:
                        st.error("Error al registrar el gasto.")
                else:
                    st.error("Completa la descripción y el monto.")

    st.markdown("---")
    
    st.markdown("#### 🗑️ Corregir / Eliminar Registros Recientes")
    col_del_v, col_del_g = st.columns(2)

    with col_del_v:
        st.markdown("##### Últimas Ventas Registradas")
        try:
            v_df = cargar_tabla("Ventas")
            if not v_df.empty:
                v_df_vista = v_df.tail(5).copy()
                st.dataframe(v_df_vista, use_container_width=True)
                
                idx_ultima_venta = len(v_df) + 1
                if st.button(f"🗑️ Eliminar Última Venta (Fila #{idx_ultima_venta})", key="del_v", use_container_width=True):
                    if borrar_fila_remota("Ventas", idx_ultima_venta):
                        st.warning("⚠️ Última venta eliminada correctamente.")
                        st.cache_data.clear()
                    else:
                        st.error("No se pudo eliminar la fila.")
            else:
                st.info("No hay ventas registradas.")
        except Exception as e:
            st.error(f"Error al leer ventas: {e}")

    with col_del_g:
        st.markdown("##### Últimos Gastos Registrados")
        try:
            g_df = cargar_tabla("Gastos_Diarios")
            if not g_df.empty:
                g_df_vista = g_df.tail(5).copy()
                st.dataframe(g_df_vista, use_container_width=True)
                
                idx_ultimo_gasto = len(g_df) + 1
                if st.button(f"🗑️ Eliminar Último Gasto (Fila #{idx_ultimo_gasto})", key="del_g", use_container_width=True):
                    if borrar_fila_remota("Gastos_Diarios", idx_ultimo_gasto):
                        st.warning("⚠️ Último gasto eliminado correctamente.")
                        st.cache_data.clear()
                    else:
                        st.error("No se pudo eliminar la fila.")
            else:
                st.info("No hay gastos registrados.")
        except Exception as e:
            st.error(f"Error al leer gastos: {e}")

# --- PESTAÑA: DASHBOARD FINANCIERO ---
with tab_dashboard:
    try:
        ventas_df = cargar_tabla("Ventas")
        costos_fijos_df = cargar_tabla("Costos fijos")
        
        try:
            gastos_diarios_df = cargar_tabla("Gastos_Diarios")
            gastos_diarios_df['monto'] = limpiar_numero(gastos_diarios_df['monto'])
            gastos_diarios_df['fecha'] = pd.to_datetime(gastos_diarios_df['fecha'])
        except Exception:
            gastos_diarios_df = pd.DataFrame(columns=['fecha', 'categoria', 'descripcion', 'monto'])

        ventas_df['precio_venta_sin_iva'] = limpiar_numero(ventas_df['precio_venta_sin_iva'])
        ventas_df['unidades_vendidas'] = pd.to_numeric(ventas_df['unidades_vendidas'], errors='coerce').fillna(0)
        ventas_df['fecha'] = pd.to_datetime(ventas_df['fecha'])
        costos_fijos_df['monto_mensual'] = limpiar_numero(costos_fijos_df['monto_mensual'])

        ventas_df['mes_año'] = ventas_df['fecha'].dt.strftime('%Y-%m')
        if not gastos_diarios_df.empty:
            gastos_diarios_df['mes_año'] = gastos_diarios_df['fecha'].dt.strftime('%Y-%m')

        meses_disponibles = sorted(ventas_df['mes_año'].unique(), reverse=True)
        mes_seleccionado = st.sidebar.selectbox("Periodo a Consultar:", meses_disponibles)

        ventas_mes = ventas_df[ventas_df['mes_año'] == mes_seleccionado]
        gastos_mes = gastos_diarios_df[gastos_diarios_df['mes_año'] == mes_seleccionado] if not gastos_diarios_df.empty else pd.DataFrame()

        unidades_vendidas = int(ventas_mes['unidades_vendidas'].sum())
        precio_unidad = ventas_mes['precio_venta_sin_iva'].iloc[0] if not ventas_mes.empty else 2.20
        ingresos_totales = unidades_vendidas * precio_unidad
        
        costos_fijos_mes = costos_fijos_df['monto_mensual'].sum()
        gastos_compras_mes = gastos_mes['monto'].sum() if not gastos_mes.empty else 0.0
        egresos_totales = costos_fijos_mes + gastos_compras_mes
        utilidad_neta = ingresos_totales - egresos_totales

        punto_equilibrio = int(egresos_totales / precio_unidad) if precio_unidad > 0 else 1
        pct_cobertura = min(100.0, (unidades_vendidas / punto_equilibrio * 100)) if punto_equilibrio > 0 else 0

        k1, k2, k3, k4 = st.columns(4)
        with k1:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Ingresos Totales</div>
                <div class="kpi-value">${ingresos_totales:,.2f}</div>
                <div class="kpi-subtitle kpi-neu">{unidades_vendidas} unidades entregadas</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Egresos Totales</div>
                <div class="kpi-value">${egresos_totales:,.2f}</div>
                <div class="kpi-subtitle kpi-neu">Fijos: ${costos_fijos_mes:,.2f} | Compras: ${gastos_compras_mes:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            color_clase = "kpi-pos" if utilidad_neta >= 0 else "kpi-neg"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Utilidad Neta Real</div>
                <div class="kpi-value {color_clase}">${utilidad_neta:,.2f}</div>
                <div class="kpi-subtitle {color_clase}">Flujo de caja libre</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Punto de Equilibrio</div>
                <div class="kpi-value">{unidades_vendidas} / {punto_equilibrio} u.</div>
                <div class="kpi-subtitle kpi-neu">{pct_cobertura:.1f}% de cobertura alcanzada</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        g1, g2 = st.columns([1, 1])
        with g1:
            st.markdown("##### 🎯 Cobertura de Costos del Mes")
            df_pie = pd.DataFrame({
                "Concepto": ["Cubierto", "Faltante"],
                "Unidades": [unidades_vendidas, max(0, punto_equilibrio - unidades_vendidas)]
            })
            fig_pie = px.pie(
                df_pie, 
                values="Unidades", 
                names="Concepto", 
                hole=0.6,
                color="Concepto",
                color_discrete_map={"Cubierto": "#2E7D32", "Faltante": "#D32F2F"}
            )
            fig_pie.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
            st.plotly_chart(fig_pie, use_container_width=True)

        with g2:
            st.markdown("##### 📈 Calendario de Entregas")
            if not ventas_mes.empty:
                ventas_mes_graf = ventas_mes.copy()
                ventas_mes_graf['fecha_str'] = ventas_mes_graf['fecha'].dt.strftime('%d %b')
                fig_bar = px.bar(
                    ventas_mes_graf, 
                    x="fecha_str", 
                    y="unidades_vendidas", 
                    text="unidades_vendidas",
                    labels={"fecha_str": "Fecha", "unidades_vendidas": "Porciones"},
                    color_discrete_sequence=["#1E293B"]
                )
                fig_bar.update_layout(margin=dict(t=20, b=20, l=20, r=20), height=300)
                st.plotly_chart(fig_bar, use_container_width=True)

        if not gastos_mes.empty:
            st.markdown("##### 📋 Compras y Gastos del Periodo")
            gastos_mostrar = gastos_mes.copy()
            gastos_mostrar['fecha'] = gastos_mostrar['fecha'].dt.strftime('%Y-%m-%d')
            st.dataframe(gastos_mostrar[['fecha', 'categoria', 'descripcion', 'monto']], use_container_width=True)

    except Exception as err:
        st.error(f"Error al cargar datos: {err}")
