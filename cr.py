import dash
from dash import html, dcc, dash_table, Input, Output
import pandas as pd
import dash_bootstrap_components as dbc
import plotly.express as px

# ================== Datos ================== #
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
            options=[{"label": eq, "value": eq} for eq in df["Equipo"].unique()],
            value=None,
            placeholder="Filtrar por equipo...",
            clearable=True,
            className="mb-3"
        ),

        dbc.Label("Selecciona una categoría:"),
        dcc.Dropdown(
            id="filtro-categoria",
            options=[{"label": cat, "value": cat} for cat in df["Categoria"].unique()],
            value=None,
            placeholder="Filtrar por categoría...",
            clearable=True
        )

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

    # Pareto
    pareto = dff.groupby("Causa")["Frecuencia"].sum().reset_index().sort_values(by="Frecuencia", ascending=False)
    fig_pareto = px.bar(pareto, x="Causa", y="Frecuencia", title="Pareto de Causas")

    # Categorías (torta)
    categoria_count = dff.groupby("Categoria")["Falla"].count().reset_index()
    categoria_count.rename(columns={"Falla": "Cantidad"}, inplace=True)
    fig_torta = px.pie(categoria_count, names="Categoria", values="Cantidad",
                       hole=0.3, color="Categoria", color_discrete_map=color_map)
    fig_torta.update_traces(textinfo="percent+label+value")

    return fig_pareto, fig_torta, dff.to_dict("records")

# ================== Run ================== #
if __name__ == "__main__":
    app.run_server(debug=True)
