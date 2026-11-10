import sys
import datetime
import json
import re
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
WEBHOOK_URL = "https://script.google.com/macros/s/AKfycbwb3Ic2hUFlAhECZvmvSldS5olEiw3z4yJYlgGqe2JqsrCk95zqX3epfY7OTL_qE5k-3w/exec"

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
    df.columns = df.columns.astype(str).str.strip().str.lower()
    return df

def limpiar_numero(columna):
    return columna.astype(str).str.replace('$', '', regex=False).str.replace(',', '', regex=False).astype(float)

def enviar_registro(pestaña, fila):
    try:
        payload = {"accion": "agregar", "pestana": pestaña, "pestaña": pestaña, "fila": fila}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            WEBHOOK_URL, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        try:
            return resp.json().get("status") == "success"
        except Exception:
            return "success" in resp.text.lower()
    except Exception:
        return False

def actualizar_estado_factura(fila_index, nuevo_estado="Cobrada"):
    try:
        payload = {
            "accion": "marcar_pagada", 
            "pestana": "Ventas", 
            "pestaña": "Ventas", 
            "fila_index": int(fila_index), 
            "estado": nuevo_estado
        }
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            WEBHOOK_URL, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        
        try:
            res_json = resp.json()
            if res_json.get("status") == "success":
                return True, res_json.get("message", "Actualizado con éxito")
            else:
                return False, f"Respuesta de Google: {res_json.get('message')}"
        except Exception:
            if "success" in resp.text.lower():
                return True, "Actualizado correctamente"
            return False, f"Respuesta no válida del servidor ({resp.status_code}): {resp.text[:150]}"
            
    except Exception as err:
        return False, f"Error de conexión: {str(err)}"

def borrar_fila_remota(pestaña, fila_index):
    try:
        payload = {"accion": "borrar", "pestana": pestaña, "pestaña": pestaña, "fila_index": int(fila_index)}
        headers = {"Content-Type": "application/json"}
        resp = requests.post(
            WEBHOOK_URL, 
            data=json.dumps(payload), 
            headers=headers, 
            timeout=15,
            allow_redirects=True
        )
        try:
            res_json = resp.json()
            return res_json.get("status") == "success"
        except Exception:
            return "success" in resp.text.lower()
    except Exception:
        return False

# --- BARRA LATERAL ---
st.sidebar.markdown("### ✨ **Estudio Mesa**")
st.sidebar.caption("Panel de Control Financiero & Operativo")

st.sidebar.link_button(
    "📊 Abrir Google Sheets", 
    f"https://docs.google.com/spreadsheets/d/{SHEET_ID}/edit", 
    use_container_width=True
)

if st.sidebar.button("🔄 Sincronizar Datos", use_container_width=True):
    st.cache_data.clear()

tab_dashboard, tab_registro, tab_facturas = st.tabs([
    "📊 Balance Financiero", 
    "📝 Registrar Operación", 
    "📑 Facturación & Cobros"
])

# --- PESTAÑA: REGISTRO DE OPERACIONES ---
with tab_registro:
    st.markdown("#### 📝 Registro Rápido de Operaciones")
    col_form1, col_form2 = st.columns(2)

    with col_form1:
        st.markdown("##### 🥖 Registrar Entrega / Factura")
        
        siguiente_correlativo = "013-2026"
        try:
            v_check = cargar_tabla("Ventas")
            if 'cliente' in v_check.columns:
                numeros_encontrados = []
                for item in v_check['cliente'].dropna().astype(str):
                    match = re.search(r'(\d{3,4})-2026', item)
                    if match:
                        numeros_encontrados.append(int(match.group(1)))
                if numeros_encontrados:
                    max_num = max(numeros_encontrados)
                    siguiente_correlativo = f"{max_num + 1:03d}-2026"
        except Exception:
            siguiente_correlativo = "013-2026"

        with st.form("form_venta", clear_on_submit=True):
            col_fac1, col_fac2 = st.columns(2)
            with col_fac1:
                fecha_venta = st.date_input("Fecha de Entrega", datetime.date.today(), key="v_fecha")
            with col_fac2:
                num_factura = st.text_input("N° Correlativo", value=siguiente_correlativo, key="v_correlativo")

            cliente_venta = st.text_input("Cliente", value="Ernestina Castro", key="v_cli")
            
            col_v1, col_v2 = st.columns(2)
            with col_v1:
                prod_venta = st.selectbox("Producto", ["PROD01", "Cardenal"], key="v_prod")
            with col_v2:
                unidades_venta = st.number_input("Unidades Entregadas", min_value=1, step=1, value=35, key="v_cant")
            
            col_p1, col_p2 = st.columns(2)
            with col_p1:
                precio_venta = st.number_input("Precio Unitario ($)", min_value=0.0, step=0.10, value=2.20, key="v_precio")
            with col_p2:
                estado_cobro = st.selectbox("Estado Inicial", ["Pendiente", "Cobrada"], key="v_estado")

            submit_venta = st.form_submit_button("💾 Guardar Factura / Venta", use_container_width=True)

            if submit_venta:
                if cliente_venta:
                    cliente_completo = f"{cliente_venta} ({num_factura})" if num_factura else cliente_venta
                    if enviar_registro("Ventas", [str(fecha_venta), cliente_completo, prod_venta, int(unidades_venta), float(precio_venta), estado_cobro]):
                        st.success(f"✅ Factura {num_factura} registrada ({unidades_venta} u.) como {estado_cobro}")
                        st.cache_data.clear()
                    else:
                        st.error("Error al registrar la factura en Google Sheets.")
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
            categoria_gasto = st.selectbox(
                "Categoría", 
                ["Insumos", "Operativos", "Empaques", "Gastos Personales", "Otros"], 
                key="g_cat"
            )
            desc_gasto = st.text_input("Descripción", placeholder="Ej. Moldes 100u, Harina, Gasolina", key="g_desc")
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
                st.dataframe(v_df.tail(5), use_container_width=True)
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
                st.dataframe(g_df.tail(5), use_container_width=True)
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

# --- PESTAÑA: GESTIÓN RÁPIDA DE FACTURAS ---
with tab_facturas:
    st.markdown("#### 📑 Gestión Ágil de Facturación y Cobros")
    st.caption("Supervisa tus cuentas por cobrar y cambia el estado de cualquier factura con un clic.")

    try:
        v_fac_df = cargar_tabla("Ventas")
        if not v_fac_df.empty:
            if 'id_producto' in v_fac_df.columns:
                v_fac_df['producto_mostrado'] = v_fac_df['id_producto']
            elif 'producto' in v_fac_df.columns:
                v_fac_df['producto_mostrado'] = v_fac_df['producto']
            else:
                v_fac_df['producto_mostrado'] = v_fac_df.iloc[:, 2] if len(v_fac_df.columns) > 2 else "PROD01"

            if 'estado' not in v_fac_df.columns:
                v_fac_df['estado'] = 'Cobrada'
            else:
                v_fac_df['estado'] = v_fac_df['estado'].fillna('Cobrada')

            col_precio = [c for c in v_fac_df.columns if 'precio' in c]
            col_unidades = [c for c in v_fac_df.columns if 'unidad' in c or 'cant' in c]
            
            p_col_name = col_precio[0] if col_precio else v_fac_df.columns[4]
            u_col_name = col_unidades[0] if col_unidades else v_fac_df.columns[3]

            v_fac_df['precio_num'] = limpiar_numero(v_fac_df[p_col_name])
            v_fac_df['unidades_num'] = pd.to_numeric(v_fac_df[u_col_name], errors='coerce').fillna(0)
            v_fac_df['total_facturado'] = v_fac_df['unidades_num'] * v_fac_df['precio_num']
            v_fac_df['fila_sheet'] = range(2, len(v_fac_df) + 2)

            pendientes = v_fac_df[v_fac_df['estado'].astype(str).str.strip().str.lower() == 'pendiente']
            cobradas = v_fac_df[v_fac_df['estado'].astype(str).str.strip().str.lower() != 'pendiente']

            col_cf1, col_cf2 = st.columns(2)
            with col_cf1:
                total_pendiente = pendientes['total_facturado'].sum()
                st.metric("Cartera por Cobrar", f"${total_pendiente:,.2f}", f"{len(pendientes)} facturas pendientes", delta_color="inverse")
            with col_cf2:
                total_cobrado = cobradas['total_facturado'].sum()
                st.metric("Total Cobrado Histórico", f"${total_cobrado:,.2f}", f"{len(cobradas)} facturas saldadas")

            st.markdown("---")
            
            st.markdown("##### ⚡ Cambiar Estado de Factura")
            
            col_sel1, col_sel2 = st.columns([2.5, 1])
            with col_sel1:
                tipo_lista = st.radio("¿Qué facturas deseas listar para editar?", ["Pendientes de Cobro", "Todas las Facturas"], horizontal=True)
                
                df_para_editar = pendientes if tipo_lista == "Pendientes de Cobro" else v_fac_df
                
                if not df_para_editar.empty:
                    opciones_facturas = {
                        f"Fila #{row['fila_sheet']} | {row['fecha']} | {row['cliente']} | ${row['total_facturado']:,.2f} (Estado actual: {row['estado']})": (row['fila_sheet'], row['estado'])
                        for _, row in df_para_editar.iterrows()
                    }
                    factura_elegida = st.selectbox("Selecciona la entrega:", options=list(opciones_facturas.keys()))
                else:
                    factura_elegida = None
                    st.success("🎉 No hay facturas pendientes en este momento.")

            with col_sel2:
                if factura_elegida:
                    fila_destino, estado_actual = opciones_facturas[factura_elegida]
                    st.write("")
                    st.write("")
                    nuevo_estado = st.selectbox("Nuevo Estado:", ["Cobrada", "Pendiente"])
                    if st.button("💾 Aplicar Cambio", use_container_width=True):
                        exito, mensaje = actualizar_estado_factura(fila_destino, nuevo_estado)
                        if exito:
                            st.success(f"✅ {mensaje}")
                            st.cache_data.clear()
                        else:
                            st.error(f"❌ {mensaje}")

            st.markdown("---")
            st.markdown("##### 📜 Historial Completo de Entregas")
            
            tabla_vista = v_fac_df.rename(columns={
                'fecha': 'Fecha',
                'cliente': 'Cliente / Correlativo',
                'producto_mostrado': 'Producto',
                'unidades_num': 'Porciones',
                'precio_num': 'Precio ($)',
                'total_facturado': 'Total ($)',
                'estado': 'Estado'
            })
            columnas_finales = ['Fecha', 'Cliente / Correlativo', 'Producto', 'Porciones', 'Precio ($)', 'Total ($)', 'Estado']
            st.dataframe(tabla_vista[columnas_finales], use_container_width=True)

    except Exception as e:
        st.error(f"Error al cargar facturas: {e}")

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

        col_precio = [c for c in ventas_df.columns if 'precio' in c]
        col_unidades = [c for c in ventas_df.columns if 'unidad' in c or 'cant' in c]
        p_col_name = col_precio[0] if col_precio else ventas_df.columns[4]
        u_col_name = col_unidades[0] if col_unidades else ventas_df.columns[3]

        ventas_df['precio_venta_sin_iva'] = limpiar_numero(ventas_df[p_col_name])
        ventas_df['unidades_vendidas'] = pd.to_numeric(ventas_df[u_col_name], errors='coerce').fillna(0)
        ventas_df['fecha'] = pd.to_datetime(ventas_df['fecha'])
        costos_fijos_df['monto_mensual'] = limpiar_numero(costos_fijos_df['monto_mensual'])

        ventas_df['mes_año'] = ventas_df['fecha'].dt.strftime('%Y-%m')
        if not gastos_diarios_df.empty:
            gastos_diarios_df['mes_año'] = gastos_diarios_df['fecha'].dt.strftime('%Y-%m')

        meses_disponibles = sorted(ventas_df['mes_año'].unique(), reverse=True)
        mes_seleccionado = st.sidebar.selectbox("Periodo a Consultar:", meses_disponibles)

        ventas_mes = ventas_df[ventas_df['mes_año'] == mes_seleccionado]
        gastos_mes = gastos_diarios_df[gastos_diarios_df['mes_año'] == mes_seleccionado] if not gastos_diarios_df.empty else pd.DataFrame()

        def clasificar_gasto(row):
            cat = str(row['categoria']).lower()
            desc = str(row['descripcion']).lower()
            if 'personal' in cat or cat == 'otros' or any(p in desc for p in ['medicina', 'camisa', 'cena', 'temu', 'gasolina manuel', 'gas manuel']):
                return 'Gastos Personales'
            if cat in ['insumos', 'operativos', 'empaques', 'produccion'] or any(p in desc for p in ['lote', 'harina', 'huevo', 'leche', 'molde', 'empaque', 'baterias']):
                return 'Producción y Operativos'
            return 'Producción y Operativos'

        if not gastos_mes.empty:
            gastos_mes['bloque'] = gastos_mes.apply(clasificar_gasto, axis=1)
            gastos_prod_operativos = gastos_mes[gastos_mes['bloque'] == 'Producción y Operativos']
            gastos_personales = gastos_mes[gastos_mes['bloque'] == 'Gastos Personales']
        else:
            gastos_prod_operativos = pd.DataFrame()
            gastos_personales = pd.DataFrame()

        total_prod_operativos = gastos_prod_operativos['monto'].sum() if not gastos_prod_operativos.empty else 0.0
        total_personales = gastos_personales['monto'].sum() if not gastos_personales.empty else 0.0

        # Histórico: hasta 2026-10 incluye empaques ($241.50); desde 2026-11 solo Luz y Gas ($54.00)[cite: 1, 4]
        if mes_seleccionado <= '2026-10':
            costos_fijos_mes = costos_fijos_df['monto_mensual'].sum()
            df_fijos_vista = costos_fijos_df.copy()
        else:
            mask_servicios = costos_fijos_df['concepto'].astype(str).str.lower().str.contains('luz|gas')
            costos_fijos_mes = costos_fijos_df[mask_servicios]['monto_mensual'].sum()
            df_fijos_vista = costos_fijos_df[mask_servicios].copy()

        unidades_vendidas = int(ventas_mes['unidades_vendidas'].sum())
        precio_unidad = ventas_mes['precio_venta_sin_iva'].iloc[0] if not ventas_mes.empty else 2.20
        ingresos_totales = unidades_vendidas * precio_unidad
        
        egresos_totales_mes = costos_fijos_mes + total_prod_operativos + total_personales
        utilidad_neta_real = ingresos_totales - egresos_totales_mes

        punto_equilibrio = int(egresos_totales_mes / precio_unidad) if precio_unidad > 0 else 1
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
                <div class="kpi-value">${egresos_totales_mes:,.2f}</div>
                <div class="kpi-subtitle kpi-neu">Fijos: ${costos_fijos_mes:,.2f} | Compras: ${total_prod_operativos + total_personales:,.2f}</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            color_clase = "kpi-pos" if utilidad_neta_real >= 0 else "kpi-neg"
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-title">Utilidad Neta Real</div>
                <div class="kpi-value {color_clase}">${utilidad_neta_real:,.2f}</div>
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

        st.markdown("---")
        st.markdown(f"### 📋 Desglose de Gastos del Mes ({mes_seleccionado})")
        
        tab_b1, tab_b2, tab_b3 = st.tabs([
            f"🥖 Producción y Operativos (${total_prod_operativos:,.2f})", 
            f"🏢 Costos Fijos (${costos_fijos_mes:,.2f})", 
            f"👤 Gastos Personales / Retiros (${total_personales:,.2f})"
        ])

        with tab_b1:
            st.caption("Compras de materia prima, moldes, empaques y mano de obra por lote.")
            if not gastos_prod_operativos.empty:
                vista_po = gastos_prod_operativos.copy()
                vista_po['fecha'] = vista_po['fecha'].dt.strftime('%Y-%m-%d')
                st.dataframe(vista_po[['fecha', 'categoria', 'descripcion', 'monto']], use_container_width=True)
            else:
                st.info("No hay gastos operativos registrados en este periodo.")

        with tab_b2:
            st.caption("Gastos fijos base del negocio.")
            st.dataframe(df_fijos_vista, use_container_width=True)

        with tab_b3:
            st.caption("Retiros del negocio y consumos personales.")
            if not gastos_personales.empty:
                vista_per = gastos_personales.copy()
                vista_per['fecha'] = vista_per['fecha'].dt.strftime('%Y-%m-%d')
                st.dataframe(vista_per[['fecha', 'categoria', 'descripcion', 'monto']], use_container_width=True)
            else:
                st.info("No se han registrado retiros ni gastos personales en este periodo.")

    except Exception as err:
        st.error(f"Error al cargar datos: {err}")
