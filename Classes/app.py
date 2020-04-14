import warnings
warnings.filterwarnings('ignore')

import pandas as pd
import numpy as np
import plotly.express as px
from plotly.subplots import make_subplots
import plotly.graph_objects as go

# Funções
def to_date(x):
    if "/" in x:
        return pd.to_datetime(x, format="%d/%m/%Y")
    else:
        return pd.to_datetime(x)

def group_by_month(col, mensal, base, ano):
    base["Mes"] = base[col].astype(str).apply(lambda x: x.split("\n")[0]).apply(lambda x: to_date(x).month)
    base["Ano"] = base[col].astype(str).apply(lambda x: x.split("\n")[0]).apply(lambda x: to_date(x).year)

    mensal = mensal.merge(base[base["Ano"] == ano].groupby("Mes").count()[[col]], left_index=True, right_index=True, how="left")

    base.drop(["Mes", "Ano"],axis=1, inplace=True)
    return mensal

def forum_priorizacao(x):
    l = []
    for n in x.split("\n"):
        l.append(to_date(n))
        
    return l
    
def fill_status(x):
    iniciativa = x[0]
    
    # Aberta
    if x[2] == 2020 and x[1] != np.nan:
        etapas_projetos.iloc[int(x[1])-1].loc[iniciativa] = 1
        
    # Iniciada
    if x[4] == 2020 and x[3] != np.nan:
        etapas_projetos.iloc[int(x[3])-1].loc[iniciativa] = 2
        
    # Finalizada
    if x[6] == 2020 and x[5] != np.nan:
        etapas_projetos.iloc[int(x[5])-1].loc[iniciativa] = 3
        
    # Cancelada
    if x[8] == 2020 and x[7] != np.nan:
        etapas_projetos.iloc[int(x[7])-1].loc[iniciativa] = 4

##########################################################################################
#                                       2020                                             #
##########################################################################################

controle_original = pd.read_excel("Projetos 2020.xlsx", sheet_name="Controle")

controle = controle_original.copy()

visao_mensal = pd.DataFrame(
    {"Mês": ["Janeiro", "Fevereiro", "Março", "Abril", 
            "Maio", "Junho", "Julho", "Agosto", "Setembro",
            "Outubro", "Novembro", "Dezembro"], "ID_mes":list(range(1,13))}
).set_index("ID_mes")


controle["Mes_rec_ficha"] = controle["Recebimento Ficha"].astype(str).apply(lambda x: x.split("\n")[0]).apply(lambda x: to_date(x).month)

visao_mensal = visao_mensal.merge(controle.groupby("Mes_rec_ficha").count()[["Recebimento Ficha"]], how="left", left_index=True, right_index=True) 

IN = controle.dropna(subset=["IN"])

# QTD Features por projeto
IN["Features"] = IN.merge(IN.groupby("IN").count()[["Feature"]], right_index=True, left_on="IN", how="left")["Feature_y"]

# QTD Reenvio de Features por projeto
IN["QTD Reenvio Ficha"] = IN["Recebimento Ficha"].astype(str).apply(lambda x: len(x.split("\n")) - 1)

# Última data de recibemento da ficha por negócio
IN["Recebimento Ficha"] = IN["Recebimento Ficha"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))

# Última data planejada de início de desenvolvimento
IN["Início Desenv."] = IN["Início Desenv."].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
IN["Início Desenv."] = IN.groupby("IN").transform(min)["Início Desenv."]

# Última data planejada de pós-implantação
IN["Pós-Implantação"] = IN["Pós-Implantação"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
IN["Pós-Implantação"] = IN.groupby("IN").transform(max)["Pós-Implantação"]

IN["VPL"] = IN.groupby("IN").transform(max)["VPL"]

IN_ = IN.copy()

IN = IN.drop_duplicates(subset=["IN"]).drop(["Feature", "Mes_rec_ficha", "Reenvio Ficha"], axis=1)

visao_mensal = group_by_month("Cancelamento", visao_mensal, IN, 2020)
canceladas = (~IN["Cancelamento"].isna()).sum()
IN = IN[IN.Cancelamento.isna()]

cols = ["Fórum de Construção", "AGR", "Abertura IN", "Início Desenv.", "Implantação", "Pós-Implantação"]
for c in cols:
    visao_mensal = group_by_month(c, visao_mensal, IN, 2020)

abertas = (~IN["Abertura IN"].isna()).sum()
iniciadas = (~IN["Início Desenv."].isna()).sum()
finalizadas = (~IN["Pós-Implantação"].isna()).sum()

backlog = abertas - iniciadas
execucao = iniciadas - finalizadas

visao_mensal.fillna(0, inplace=True)
visao_mensal.columns = ["Mês", "Fichas", "Canceladas", "Fórum de Construção", "AGR", "Abertas", "Iniciadas", "Implantadas", "Finalizadas"]
visao_mensal["Backlog"] = visao_mensal["Abertas"].cumsum() - visao_mensal["Iniciadas"].cumsum()
visao_mensal["Execução"] = visao_mensal["Iniciadas"].cumsum() - visao_mensal["Finalizadas"].cumsum()
visao_mensal["Carteira"] = visao_mensal[["Backlog", "Execução", "Finalizadas"]].sum(axis=1) + visao_mensal["Finalizadas"].cumsum()

datas_priorizacao = pd.DataFrame(IN["Fórum de Priorização"].astype(str).apply(forum_priorizacao).sum())
datas_priorizacao = datas_priorizacao[datas_priorizacao[0].apply(lambda x: x.year) == 2020]
datas_priorizacao["Mês"] = datas_priorizacao[0].apply(lambda x: x.month)
visao_mensal = visao_mensal.merge(datas_priorizacao.groupby("Mês").count(), right_index=True, left_index=True, how="left").fillna(0)
visao_mensal.columns = visao_mensal.columns[:-1].tolist() + ["Fórum de Priorização"]


# Categorias
categorias = IN.groupby("Categoria").count()[["IN"]].merge(IN[(IN["Pós-Implantação"] >= pd.to_datetime("01/01/2020", format="%d/%m/%Y"))].groupby("Categoria").count()[["IN"]], left_index=True, right_index=True)

vpl_total = IN["VPL"].sum()
vpl_entregue = IN[(IN["Pós-Implantação"] >= pd.to_datetime("01/01/2020", format="%d/%m/%Y"))]["VPL"].sum()

categorias.columns = ["Carteira", "Finalizadas"]
categorias.reset_index(inplace=True)
categorias = categorias.melt(id_vars="Categoria", value_name="Quantidade", var_name="Grupo")

fig_categorias = px.bar(categorias,
                        x="Categoria",
                        y="Quantidade",
                        color="Grupo",
                        barmode="group",
                        text="Quantidade",
                        color_discrete_map={"Carteira": "rgb(250, 132, 5)", "Finalizadas": "rgb(52, 110, 235)"})

fig_categorias.update_layout(
    annotations=[
        dict(
            x=-0.2,
            y=categorias[(categorias["Categoria"] == "Benefício") & (categorias["Grupo"] == "Carteira")]["Quantidade"][0] + 0.5,
            xref="x",
            yref="y",
            text=f"R$ {vpl_total:.2f}",
            showarrow=False
        ), 
        dict(
            x=0.2,
            y=categorias[(categorias["Categoria"] == "Benefício") & (categorias["Grupo"] == "Finalizadas")]["Quantidade"].reset_index(drop=True)[0] + 0.5,
            xref="x",
            yref="y",
            text=f"R$ {vpl_entregue:.2f}",
            showarrow=False
        ), 
    ]
)

# Carteira Visão Mensal
kpi_carteira = visao_mensal[["Mês", "Backlog", "Execução", "Finalizadas", "Canceladas"]]
kpi_carteira = kpi_carteira.melt(id_vars="Mês", var_name="Status", value_name="Quantidade")
fig_carteira = px.bar(kpi_carteira,
       y="Mês",
       x="Quantidade",
       color="Status", 
       text="Quantidade",
       orientation="h",
       color_discrete_map={"Backlog": "rgb(98, 102, 102)", "Execução": "rgb(73, 168, 39)", "Finalizadas": "rgb(52, 110, 235)", "Canceladas":"rgb(194, 48, 61)"},
       title="2020", height=600)

# Visão Features
def in2feature(coluna, dataset):
    dataset[coluna] = dataset[coluna].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
    dataset[coluna] = dataset.groupby("IN").transform(max)[coluna]

feature = controle.dropna(subset=["Feature"])
feature["Início Desenv."] = feature["Início Desenv."].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
feature["Pós-Implantação"] = feature["Pós-Implantação"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))

cols = ["Recebimento Ficha", "Fórum de Construção", "AGR", "Abertura IN", "Fórum de Priorização", "Cancelamento"]

for c in cols:
    in2feature(c, feature)
    
visao_mensal_feature = pd.DataFrame(
    {"Mês": ["Janeiro", "Fevereiro", "Março", "Abril", 
            "Maio", "Junho", "Julho", "Agosto", "Setembro",
            "Outubro", "Novembro", "Dezembro"], "ID_mes":list(range(1,13))}
).set_index("ID_mes")

visao_mensal_feature = group_by_month("Cancelamento", visao_mensal_feature, feature, 2020)
feature = feature[feature.Cancelamento.isna()]

cols = ["Abertura IN", "Início Desenv.", "Implantação", "Pós-Implantação"]
for c in cols:
    visao_mensal_feature = group_by_month(c, visao_mensal_feature, feature, 2020)
    
visao_mensal_feature.fillna(0, inplace=True)
visao_mensal_feature.columns = ["Mês", "Canceladas", "Abertas", "Iniciadas", "Implantadas", "Finalizadas"]
visao_mensal_feature["Backlog"] = visao_mensal_feature["Abertas"].cumsum() - visao_mensal_feature["Iniciadas"].cumsum()
visao_mensal_feature["Execução"] = visao_mensal_feature["Iniciadas"].cumsum() - visao_mensal_feature["Finalizadas"].cumsum()
visao_mensal_feature["Carteira"] = visao_mensal_feature[["Backlog", "Execução", "Finalizadas"]].sum(axis=1) + visao_mensal_feature["Finalizadas"].cumsum()

kpi_carteira = visao_mensal_feature[["Mês", "Backlog", "Execução", "Finalizadas", "Canceladas"]]
kpi_carteira = kpi_carteira.melt(id_vars="Mês", var_name="Status", value_name="Quantidade")
fig_carteira_feature = px.bar(kpi_carteira,
       y="Mês",
       x="Quantidade",
       color="Status", 
       text="Quantidade",
       orientation="h",
       color_discrete_map={"Backlog": "rgb(98, 102, 102)", "Execução": "rgb(73, 168, 39)", "Finalizadas": "rgb(52, 110, 235)", "Canceladas":"rgb(194, 48, 61)"},
       title="2020", height=600)

# Status - Visão Projeto
IN = IN_.copy()
etapas_projetos = pd.DataFrame(index=visao_mensal["Mês"], columns=IN.IN)

IN["Aberta_mes"] = IN["Abertura IN"].apply(lambda x: x.month)
IN["Aberta_ano"] = IN["Abertura IN"].apply(lambda x: x.year)
IN["Finalizada_mes"] = IN["Pós-Implantação"].apply(lambda x: x.month)
IN["Finalizada_ano"] = IN["Pós-Implantação"].apply(lambda x: x.year)
IN["Iniciada_mes"] = IN["Início Desenv."].apply(lambda x: x.month)
IN["Iniciada_ano"] = IN["Início Desenv."].apply(lambda x: x.year)
IN["Finalizada_mes"] = IN["Pós-Implantação"].apply(lambda x: x.month)
IN["Finalizada_ano"] = IN["Pós-Implantação"].apply(lambda x: x.year)
IN["Cancelada_mes"] = IN["Cancelamento"].apply(lambda x: x.month)
IN["Cancelada_ano"] = IN["Cancelamento"].apply(lambda x: x.year)

_ = IN[["IN",
        "Aberta_mes", "Aberta_ano",
        "Iniciada_mes", "Iniciada_ano",
        "Finalizada_mes", "Finalizada_ano",
        "Cancelada_mes", "Cancelada_ano"]].apply(fill_status, axis=1)

etapas_projetos = etapas_projetos.fillna(method="ffill").T


hover_df=etapas_projetos.replace({1: "Aberta", 2:"Iniciada", 3:"Finalizada", 4:"Cancelada"})
hovertext = etapas_projetos.copy()
for row in hover_df.index:
    for col in hover_df.columns:
        hovertext.loc[row,col] = f"IN:{row}<br>Mês:{col}<br>Status:{hover_df.loc[row,col]}"

hovertext = hovertext.values.tolist()

fig_status_projetos = go.Figure([go.Heatmap(
    z=etapas_projetos.values,
    x=etapas_projetos.columns,
    y=etapas_projetos.index, 
    colorscale=[[0,"rgb(98, 102, 102)"], [0.33,"rgb(73, 168, 39)"], [0.67,"rgb(52, 110, 235)"], [1,"rgb(194, 48, 61)"]],
    showscale=False, 
    xgap=1,
    ygap=1,
    hovertext=hovertext,
    hoverinfo="text",
    hoverongaps=False,
    zmin=1,
    zmax=4
)])

fig_status_projetos.update_layout(xaxis={"showgrid":False}, yaxis={"dtick":1, "showgrid":False}, height=700)

# Etapas
kpi_carteira = visao_mensal[["Mês", "Fórum de Construção", "AGR"]]
kpi_carteira = kpi_carteira.melt(id_vars="Mês", var_name="Fórum", value_name="Quantidade")

fig_etapas = make_subplots(rows=3, cols=2, subplot_titles=["Fichas", "Risco", "Fórum de Prorização", "Abertas", "Iniciadas", "Implantadas"])

fig_etapas.add_trace(px.bar(visao_mensal, x="Mês", y="Fichas", text="Fichas", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=1, col=1)
fig_etapas.add_trace(px.bar(kpi_carteira, x="Mês", y="Quantidade", text="Quantidade", color="Fórum", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=1, col=2)
fig_etapas.add_trace(px.bar(kpi_carteira, x="Mês", y="Quantidade", text="Quantidade", color="Fórum", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[1], row=1, col=2)
fig_etapas.add_trace(px.bar(visao_mensal, x="Mês", y="Fórum de Priorização", text="Fórum de Priorização", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=2, col=1)
fig_etapas.add_trace(px.bar(visao_mensal, x="Mês", y="Abertas", text="Abertas", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=2, col=2)
fig_etapas.add_trace(px.bar(visao_mensal, x="Mês", y="Iniciadas", text="Iniciadas", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=3, col=1)
fig_etapas.add_trace(px.bar(visao_mensal, x="Mês", y="Implantadas", text="Implantadas", color_discrete_sequence=["rgb(98, 102, 102)", "rgb(250, 132, 5)"]).data[0], row=3, col=2)
fig_etapas.update_layout(legend_orientation="h", height=700)

##########################################################################################
#                                       2019                                             #
##########################################################################################

controle_2019 = pd.read_excel("Projetos 2019.xlsx", sheet_name="Controle")

visao_mensal_2019 = pd.DataFrame(
    {"Mês": ["Janeiro", "Fevereiro", "Março", "Abril", 
            "Maio", "Junho", "Julho", "Agosto", "Setembro",
            "Outubro", "Novembro", "Dezembro"], "ID_mes":list(range(1,13))}
).set_index("ID_mes")

controle_2019["Mes_rec_ficha"] = controle_2019["Recebimento Ficha"].astype(str).apply(lambda x: x.split("\n")[0]).apply(lambda x: to_date(x).month)

visao_mensal_2019 = visao_mensal_2019.merge(controle_2019.groupby("Mes_rec_ficha").count()[["Recebimento Ficha"]], how="left", left_index=True, right_index=True) 

IN_2019 = controle_2019.dropna(subset=["IN"])

# QTD Features por projeto
IN_2019["Features"] = IN_2019.merge(IN_2019.groupby("IN").count()[["Feature"]], right_index=True, left_on="IN", how="left")["Feature_y"]

# QTD Reenvio de Features por projeto
IN_2019["QTD Reenvio Ficha"] = IN_2019["Recebimento Ficha"].astype(str).apply(lambda x: len(x.split("\n")) - 1)

# Última data de recibemento da ficha por negócio
IN_2019["Recebimento Ficha"] = IN_2019["Recebimento Ficha"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))

# Última data planejada de início de desenvolvimento
IN_2019["Início Desenv."] = IN_2019["Início Desenv."].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
IN_2019["Início Desenv."] = IN_2019.groupby("IN").transform(min)["Início Desenv."]

# Última data planejada de pós-implantação
IN_2019["Pós-Implantação"] = IN_2019["Pós-Implantação"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
IN_2019["Pós-Implantação"] = IN_2019.groupby("IN").transform(max)["Pós-Implantação"]

IN_2019["VPL"] = IN_2019.groupby("IN").transform(max)["VPL"]

IN_2019 = IN_2019.drop_duplicates(subset=["IN"]).drop(["Feature", "Mes_rec_ficha", "Reenvio Ficha"], axis=1)

visao_mensal_2019 = group_by_month("Cancelamento", visao_mensal_2019, IN_2019, 2019)
IN_2019 = IN_2019[IN_2019.Cancelamento.isna()]

cols = ["Fórum de Construção", "AGR", "Abertura IN", "Início Desenv.", "Implantação", "Pós-Implantação"]
for c in cols:
    visao_mensal_2019 = group_by_month(c, visao_mensal_2019, IN_2019, 2019)

visao_mensal_2019.fillna(0, inplace=True)
visao_mensal_2019.columns = ["Mês", "Fichas", "Canceladas", "Fórum de Construção", "AGR", "Abertas", "Iniciadas", "Implantadas", "Finalizadas"]
visao_mensal_2019["Backlog"] = visao_mensal_2019["Abertas"].cumsum() - visao_mensal_2019["Iniciadas"].cumsum()
visao_mensal_2019["Execução"] = visao_mensal_2019["Iniciadas"].cumsum() - visao_mensal_2019["Finalizadas"].cumsum()
visao_mensal_2019["Carteira"] = visao_mensal_2019[["Backlog", "Execução", "Finalizadas"]].sum(axis=1) + visao_mensal_2019["Finalizadas"].cumsum()

# Carteira Visão Mensal
kpi_carteira = visao_mensal_2019[["Mês", "Backlog", "Execução", "Finalizadas", "Canceladas"]]
kpi_carteira = kpi_carteira.melt(id_vars="Mês", var_name="Status", value_name="Quantidade")
fig_carteira_2019 = px.bar(kpi_carteira,
       y="Mês",
       x="Quantidade",
       color="Status", 
       text="Quantidade",
       orientation="h",
       color_discrete_map={"Backlog": "rgb(98, 102, 102)", "Execução": "rgb(73, 168, 39)", "Finalizadas": "rgb(52, 110, 235)", "Canceladas":"rgb(194, 48, 61)"},
       title="2019", height=600)

# Visão Features

feature_2019 = controle_2019.dropna(subset=["Feature"])
feature_2019["Início Desenv."] = feature_2019["Início Desenv."].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))
feature_2019["Pós-Implantação"] = feature_2019["Pós-Implantação"].astype(str).apply(lambda x: x.split("\n")[-1]).apply(lambda x: to_date(x))

cols = ["Recebimento Ficha", "Fórum de Construção", "AGR", "Abertura IN", "Fórum de Priorização", "Cancelamento"]

for c in cols:
    in2feature(c, feature_2019)
    
visao_mensal_feature_2019 = pd.DataFrame(
    {"Mês": ["Janeiro", "Fevereiro", "Março", "Abril", 
            "Maio", "Junho", "Julho", "Agosto", "Setembro",
            "Outubro", "Novembro", "Dezembro"], "ID_mes":list(range(1,13))}
).set_index("ID_mes")

visao_mensal_feature_2019 = group_by_month("Cancelamento", visao_mensal_feature_2019, feature_2019, 2019)
feature_2019 = feature_2019[feature_2019.Cancelamento.isna()]

cols = ["Abertura IN", "Início Desenv.", "Implantação", "Pós-Implantação"]
for c in cols:
    visao_mensal_feature_2019 = group_by_month(c, visao_mensal_feature_2019, feature_2019, 2019)
    
visao_mensal_feature_2019.fillna(0, inplace=True)
visao_mensal_feature_2019.columns = ["Mês", "Canceladas", "Abertas", "Iniciadas", "Implantadas", "Finalizadas"]
visao_mensal_feature_2019["Backlog"] = visao_mensal_feature_2019["Abertas"].cumsum() - visao_mensal_feature_2019["Iniciadas"].cumsum()
visao_mensal_feature_2019["Execução"] = visao_mensal_feature_2019["Iniciadas"].cumsum() - visao_mensal_feature_2019["Finalizadas"].cumsum()
visao_mensal_feature_2019["Carteira"] = visao_mensal_feature_2019[["Backlog", "Execução", "Finalizadas"]].sum(axis=1) + visao_mensal_feature_2019["Finalizadas"].cumsum()

kpi_carteira = visao_mensal_feature_2019[["Mês", "Backlog", "Execução", "Finalizadas", "Canceladas"]]
kpi_carteira = kpi_carteira.melt(id_vars="Mês", var_name="Status", value_name="Quantidade")
fig_carteira_feature_2019 = px.bar(kpi_carteira,
       y="Mês",
       x="Quantidade",
       color="Status", 
       text="Quantidade",
       orientation="h",
       color_discrete_map={"Backlog": "rgb(98, 102, 102)", "Execução": "rgb(73, 168, 39)", "Finalizadas": "rgb(52, 110, 235)", "Canceladas":"rgb(194, 48, 61)"},
       title="2020", height=600)
##########################################################################################
#                                       Dash App                                         #
##########################################################################################
import dash
import dash_html_components as html
import dash_core_components as dcc
from dash.dependencies import Input, Output

app = dash.Dash(
    __name__, meta_tags=[{"name": "viewport", "content": "width=device-width"}], 
)

def indicator(color, text, id_value, indicador):
    return html.Div(
        [
            html.P(indicador, id=id_value, className="indicator_value"),
            html.P(text, className="twelve columns indicator_text"),
        ],
        className="five columns indicator pretty_container",
    )

indicadores = html.Div(
                className="row indicators",
                children=[
                    indicator("#00cc96", "Iniciativas", "indicador_carteira", abertas),
                    indicator("#119DFF", "Backlog", "indicador_backlog", backlog),
                    indicator("#EF553B", "Execução", "indicador_exec", execucao),
                    indicator("#00cc96", "Finalizadas", "indicador_finalizadas", finalizadas),
                    indicator("#00cc96", "Canceladas", "indicador_canceladas", canceladas),
                ]
            )

categorias = html.Div(
    className="chart_div pretty_container",
    children=[
        dcc.Graph(
            id="categorias",
            figure=fig_categorias
        )
    ]
)

carteira_mensal = html.Div(
    className="two columns pretty_container",
    children=[
        html.Div(
            children=[
                dcc.Dropdown(options=[
                        {"label": "Iniciativa", "value":"Iniciativa"},
                        {"label": "Feature", "value":"Feature"},
                        ],
                        value="Iniciativa",
                        id="dropdown")
            ],
            style={"width":"15%", "align":"left", "margin":"1%"}
        ),
        html.Div(
            className="chart_div",
            children=[
                dcc.Graph(
                    id="carteira_mensal_2019",
                    figure=fig_carteira_2019
                ),
            ],
            style={"width":"49%", "display": "inline-block", "height":"95%"}
        ),
        html.Div(
            className="chart_div",
            children=[
                dcc.Graph(
                    id="carteira_mensal_2020",
                    figure=fig_carteira
                ),
            ],
            style={"width":"49%", "display": "inline-block", "height":"95%"}
        )
    ]
)

status_projetos = html.Div(
    className="chart_div pretty_container",
    children=[
        dcc.Graph(
            id="status_projetos",
            figure=fig_status_projetos
        )
    ]
)

etapas = html.Div(
    className="chart_div pretty_container",
    children=[
        dcc.Graph(
            id="etapas",
            figure=fig_etapas
        )
    ]
)

app.layout = html.Div(
    children=[
        html.H1("Indicadores"),
        indicadores, 
        html.H1("Categoria"),
        categorias,
        html.H1("Status - Mensal"),
        carteira_mensal,
        html.H1("Status - Projetos"),
        status_projetos,
        html.H1("Etapas - Mensal"),
        etapas
    ], 
    style={ "margin_bottom":"10%", "margin_top":"1%", "margin":"5%"}
)

@app.callback(
    Output(component_id='carteira_mensal_2019', component_property='figure'),
    [Input(component_id='dropdown', component_property='value')]
)
def change_in2feature_2019(input_value):
    if input_value == "Feature":
        return fig_carteira_feature_2019
    else:
        return fig_carteira_2019

@app.callback(
    Output(component_id='carteira_mensal_2020', component_property='figure'),
    [Input(component_id='dropdown', component_property='value')]
)
def change_in2feature_2020(input_value):
    if input_value == "Feature":
        return fig_carteira_feature
    else:
        return fig_carteira

if __name__ == '__main__':
    app.run_server()