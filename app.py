import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px
import os

# ================== Carga robusta de datos ================== #
df = pd.read_csv("causas_raiz.csv")
df["Fecha"] = pd.to_datetime(df["Fecha"])

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
    
    app.run(debug=debug_mode, host="0.0.0.0", port=port)
