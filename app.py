import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import os

# ================== Carga robusta de datos ================== #
def cargar_datos():
    try:
        # Intentar cargar el CSV
        print("🔍 Intentando cargar causas_raiz.csv...")
        
        # Método 1: Carga básica
        try:
            df = pd.read_csv("causas_raiz.csv")
            print("✓ Carga básica exitosa")
        except:
            # Método 2: Carga robusta
            df = pd.read_csv("causas_raiz.csv", 
                           sep=',',
                           encoding='utf-8',
                           on_bad_lines='skip',
                           engine='python',
                           quotechar='"',
                           skipinitialspace=True)
            print("✓ Carga robusta exitosa")
        
        print(f"📋 Columnas encontradas: {list(df.columns)}")
        print(f"📊 Forma del DataFrame: {df.shape}")
        
        # Mapear columnas automáticamente
        columnas_mapeadas = {}
        columnas_disponibles = df.columns.tolist()
        
        # Buscar columnas similares (case-insensitive y flexible)
        for col in columnas_disponibles:
            col_lower = col.lower().strip()
            
            # Mapear fechas
            if any(palabra in col_lower for palabra in ['fecha', 'date', 'time']):
                columnas_mapeadas['Fecha'] = col
            
            # Mapear equipos
            elif any(palabra in col_lower for palabra in ['equipo', 'equipment', 'machine', 'maquina']):
                columnas_mapeadas['Equipo'] = col
            
            # Mapear categorías
            elif any(palabra in col_lower for palabra in ['categoria', 'category', 'tipo', 'type', 'class']):
                columnas_mapeadas['Categoria'] = col
                
            # Mapear causas
            elif any(palabra in col_lower for palabra in ['causa', 'cause', 'reason', 'razon']):
                columnas_mapeadas['Causa'] = col
                
            # Mapear frecuencia
            elif any(palabra in col_lower for palabra in ['frecuencia', 'frequency', 'count', 'cantidad']):
                columnas_mapeadas['Frecuencia'] = col
                
            # Mapear fallas
            elif any(palabra in col_lower for palabra in ['falla', 'failure', 'error', 'problema', 'issue']):
                columnas_mapeadas['Falla'] = col
        
        print(f"🔗 Mapeo de columnas: {columnas_mapeadas}")
        
        # Renombrar columnas
        if columnas_mapeadas:
            df_renamed = df.rename(columns={v: k for k, v in columnas_mapeadas.items()})
        else:
            # Si no se puede mapear, usar las primeras columnas disponibles
            df_renamed = df.copy()
            if len(df.columns) >= 6:
                nuevos_nombres = ["Fecha", "Equipo", "Categoria", "Causa", "Frecuencia", "Falla"]
                df_renamed.columns = nuevos_nombres[:len(df.columns)]
        
        # Crear columnas faltantes con valores por defecto
        columnas_necesarias = ["Fecha", "Equipo", "Categoria", "Causa", "Frecuencia", "Falla"]
        for col in columnas_necesarias:
            if col not in df_renamed.columns:
                if col == "Fecha":
                    df_renamed[col] = pd.date_range("2024-01-01", periods=len(df_renamed))
                elif col == "Frecuencia":
                    df_renamed[col] = 1
                else:
                    df_renamed[col] = f"Valor_{col}"
        
        # Procesar fecha si existe
        if "Fecha" in df_renamed.columns:
            df_renamed["Fecha"] = pd.to_datetime(df_renamed["Fecha"], errors='coerce')
        
        # Asegurar que Frecuencia sea numérica
        if "Frecuencia" in df_renamed.columns:
            df_renamed["Frecuencia"] = pd.to_numeric(df_renamed["Frecuencia"], errors='coerce').fillna(1)
        
        # Limpiar datos nulos
        df_renamed = df_renamed.fillna("Sin datos")
        
        print(f"✅ Datos procesados: {len(df_renamed)} filas")
        return df_renamed
        
    except FileNotFoundError:
        print("📁 Archivo causas_raiz.csv no encontrado")
        return crear_datos_ejemplo()
    except Exception as e:
        print(f"❌ Error cargando CSV: {e}")
        return crear_datos_ejemplo()

def crear_datos_ejemplo():
    print("📝 Creando datos de ejemplo...")
    return pd.DataFrame({
        "Fecha": pd.date_range("2024-01-01", periods=30),
        "Equipo": (["Bomba Principal"] * 10 + ["Compresor A"] * 10 + ["Motor B"] * 10),
        "Categoria": (["Causa Física"] * 10 + ["Causa Técnica"] * 10 + ["Causa Operativa"] * 10),
        "Causa": (["Desgaste", "Vibración", "Sobrecalentamiento", "Desalineación", "Fatiga"] * 6),
        "Frecuencia": [5, 3, 2, 4, 1, 6, 3, 2, 4, 1] * 3,
        "Falla": [f"Falla crítica {i+1}" for i in range(30)]
    })

# Cargar datos
df = cargar_datos()

# Colores consistentes
color_map = {
    "Causa Física": "#636EFA",     # azul
    "Causa Técnica": "#EF553B",    # rojo
    "Causa Operativa": "#00CC96"   # verde
}

# ================== App ================== #
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
server = app.server  # Esta línea es CRUCIAL para Render

# ================== Layout ================== #
app.layout = html.Div([
    # Sidebar
    html.Div([
        html.H2("⚙️ Filtros", className="text-center mb-4"),

        dbc.Label("Selecciona un equipo:"),
        dcc.Dropdown(
            id="filtro-equipo",
            options=[{"label": eq, "value": eq} for eq in sorted(df["Equipo"].unique())],
            value=None,
            placeholder="Filtrar por equipo...",
            clearable=True,
            className="mb-3"
        ),

        dbc.Label("Selecciona una categoría:"),
        dcc.Dropdown(
            id="filtro-categoria",
            options=[{"label": cat, "value": cat} for cat in sorted(df["Categoria"].unique())],
            value=None,
            placeholder="Filtrar por categoría...",
            clearable=True
        ),
        
        # Info sobre los datos
        html.Hr(),
        html.P(f"📊 Total registros: {len(df)}", className="small text-muted"),
        html.P(f"📅 Desde: {df['Fecha'].min().strftime('%Y-%m-%d') if not df['Fecha'].isna().all() else 'N/A'}", 
               className="small text-muted"),
        html.P(f"📅 Hasta: {df['Fecha'].max().strftime('%Y-%m-%d') if not df['Fecha'].isna().all() else 'N/A'}", 
               className="small text-muted")

    ], style={
        "width": "20%",
        "padding": "20px",
        "backgroundColor": "#f8f9fa",
        "position": "fixed",
        "top": 0,
        "left": 0,
        "bottom": 0,
        "overflowY": "auto"
    }),

    # Main Content
    html.Div([
        html.H1("📊 Dashboard de Causa Raíz",
                className="text-center my-4",
                style={"color": "#2c3e50"}),

        dbc.Row([
            dbc.Col(dbc.Card([
                dbc.CardHeader("Pareto de Causas"),
                dbc.CardBody(dcc.Graph(id="pareto"))
            ], className="shadow-sm mb-4"), md=6),

            dbc.Col(dbc.Card([
                dbc.CardHeader("Distribución de Categorías"),
                dbc.CardBody(dcc.Graph(id="categorias_torta"))
            ], className="shadow-sm mb-4"), md=6),
        ]),
     
        html.H3("📋 Tabla de Datos", className="text-center mt-4"),
        dash_table.DataTable(
            id="tabla-datos",
            columns=[{"name": i, "id": i} for i in df.columns],
            data=df.to_dict("records"),
            page_size=10,
            sort_action="native",
            filter_action="native",
            style_table={"overflowX": "auto"},
            style_cell={"textAlign": "center", "padding": "5px"},
            style_header={"backgroundColor": "#e9ecef", "fontWeight": "bold"}
        )
    ], style={"marginLeft": "22%", "padding": "20px"})
])

# ================== Callbacks ================== #
@app.callback(
    [Output("pareto", "figure"),
     Output("categorias_torta", "figure"),
     Output("severidad_chart", "figure"),
     Output("tabla-datos", "data")],
    [Input("filtro-equipo", "value"),
     Input("filtro-categoria", "value")]
)
def actualizar_dashboard(equipo_seleccionado, categoria_seleccionada):
    dff = df.copy()

    # Filtros
    if equipo_seleccionado:
        dff = dff[dff["Equipo"] == equipo_seleccionado]
    if categoria_seleccionada:
        dff = dff[dff["Categoria"] == categoria_seleccionada]

    # Verificar que hay datos después del filtro
    if dff.empty:
        # Gráficos vacíos
        fig_pareto = px.bar(title="No hay datos para los filtros seleccionados")
        fig_torta = px.pie(title="No hay datos para los filtros seleccionados")
        fig_severidad = px.bar(title="No hay datos para los filtros seleccionados")
        return fig_pareto, fig_torta, fig_severidad, []

    # Pareto de Causas
    pareto = dff.groupby("Causa")["Frecuencia"].sum().reset_index().sort_values(by="Frecuencia", ascending=False)
    fig_pareto = px.bar(pareto, x="Causa", y="Frecuencia", 
                       title="Pareto de Causas",
                       color="Frecuencia",
                       color_continuous_scale="viridis")
    fig_pareto.update_layout(xaxis_tickangle=-45)

    # Categorías (torta)
    categoria_count = dff.groupby("Categoria")["Falla"].count().reset_index()
    categoria_count.rename(columns={"Falla": "Cantidad"}, inplace=True)
    fig_torta = px.pie(categoria_count, names="Categoria", values="Cantidad",
                       hole=0.3, color="Categoria", color_discrete_map=color_map,
                       title="Distribución por Categoría")
    fig_torta.update_traces(textinfo="percent+label+value")

    # Análisis de Severidad (nuevo)
    if "Severidad" in dff.columns:
        severidad_categoria = dff.groupby(["Categoria", "Severidad"]).size().reset_index(name="Cantidad")
        fig_severidad = px.bar(severidad_categoria, 
                              x="Categoria", y="Cantidad", 
                              color="Severidad",
                              title="Distribución de Severidad por Categoría",
                              color_continuous_scale="Reds")
    else:
        fig_severidad = px.bar(title="Datos de severidad no disponibles")

    return fig_pareto, fig_torta, fig_severidad, dff.to_dict("records")

# ================== Run ================== #
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8050))
    debug_mode = os.environ.get("ENVIRONMENT", "production") == "development"
    
    print(f"🚀 Iniciando aplicación en puerto {port}")
    print(f"🔧 Modo debug: {debug_mode}")
    
    app.run_server(debug=debug_mode, host="0.0.0.0", port=port)
