import streamlit as st
import pandas as pd
import json
import plotly.express as px
import geopandas as gpd
import numpy as np

# Configuração inicial da página
st.set_page_config(page_title="Dashboard de Acidentes", layout="wide")
st.title("Acidentes com Animais Peçonhentos")

# --- 1. CARREGAMENTO DOS DADOS ---
@st.cache_data
def carregar_dados():
    df = pd.read_parquet('dados_traduzidos.parquet')
    
    # Extrai o Ano da coluna de Data e converte para tipo numérico
    df['Ano'] = df['Data'].dt.year.astype('Int64')
    
    return df

@st.cache_data
def carregar_geojson():
    # 1. Carrega o GeoJSON original
    gdf = gpd.read_file("brasil_municipios.json")
    
    # 2. Simplifica a geometria (solução definitiva para a memória)
    gdf['geometry'] = gdf.geometry.simplify(tolerance=0.005)
    
    # 3. Retorna o JSON limpo
    return json.loads(gdf.to_json())

df = carregar_dados()
geojson_brasil = carregar_geojson()

# --- 2. BARRA LATERAL: FILTROS ---
st.sidebar.header("Filtros Analíticos")

def extrair_opcoes(serie):
    valores = serie.dropna().unique().tolist()
    try:
        valores = sorted(valores)
    except TypeError:
        pass
    return ['Todas'] + valores

uf_selecionada = st.sidebar.selectbox("UF", extrair_opcoes(df['UF']))
ano_selecionado = st.sidebar.selectbox("Ano", extrair_opcoes(df['Ano']))
sexo_selecionado = st.sidebar.selectbox("Sexo", extrair_opcoes(df['Sexo']))
raca_selecionada = st.sidebar.selectbox("Raça", extrair_opcoes(df['Raça']))
acidente_selecionado = st.sidebar.selectbox("Tipo de Acidente", extrair_opcoes(df['Tipo de Acidente']))
doenca_selecionada = st.sidebar.selectbox("Doença relac. Trabalho", extrair_opcoes(df['Doença relac. Trabalho']))

# --- 3. MOTOR DE FILTRAGEM ---
df_filtrado = df.copy()

if uf_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['UF'] == uf_selecionada]

if ano_selecionado != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Ano'] == ano_selecionado]

if sexo_selecionado != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Sexo'] == sexo_selecionado]

if raca_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Raça'] == raca_selecionada]

if acidente_selecionado != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Tipo de Acidente'] == acidente_selecionado]

if doenca_selecionada != 'Todas':
    df_filtrado = df_filtrado[df_filtrado['Doença relac. Trabalho'] == doenca_selecionada]

# --- 4. RENDERIZAÇÃO DAS ABAS ---
aba_analises, aba_mapa = st.tabs(["Análises Gerais", "Mapa Interativo"])

# --- ABA 1: ANÁLISES GERAIS ---
with aba_analises:
    if not df_filtrado.empty:
        
        # 1. Gráfico de Série Histórica (Semanal)
        st.subheader("Série Histórica de Casos (Semanal)")
        
        df_serie = df_filtrado.dropna(subset=['Data'])
        if not df_serie.empty:
            serie_semanal = (
                df_serie.resample('W-MON', on='Data')
                .size()
                .reset_index(name='Casos')
            )
            
            st.line_chart(
                data=serie_semanal,
                x='Data',
                y='Casos',
                use_container_width=True
            )
        else:
            st.info("Não há registros com datas válidas para plotar a série histórica após os filtros.")
        
        st.markdown("---")
        
        col1, col2 = st.columns(2)
        
        with col1:
            # 2. Gráfico de Distribuição por Animal (%)
            st.subheader("Distribuição por Tipo de Animal (%)")
            
            dist_animal = (
                df_filtrado['Tipo de Acidente']
                .value_counts(normalize=True) * 100
            ).reset_index()
            
            dist_animal.columns = ['Tipo de Acidente', 'Porcentagem (%)']
            dist_animal = dist_animal[dist_animal['Porcentagem (%)'] > 0]
            dist_animal = dist_animal.sort_values(by='Porcentagem (%)', ascending=False)
            
            st.bar_chart(
                data=dist_animal,
                x='Tipo de Acidente',
                y='Porcentagem (%)',
                use_container_width=True
            )

        with col2:
            # 3. Ranking Top 20 Municípios
            st.subheader("Top 20 Municípios por Volume")
            
            agrupamento = (
                df_filtrado.groupby('Município', observed=False)
                .size()
                .reset_index(name='Casos')
            )
            
            top_20_municipios = (
                agrupamento[agrupamento['Casos'] > 0]
                .sort_values(by='Casos', ascending=False)
                .head(20)
            )

            if top_20_municipios.empty:
                st.warning("Nenhum município registrou casos com essa combinação de filtros.")
            else:
                st.dataframe(
                    top_20_municipios.style.format({'Casos': '{:,}'}),
                    use_container_width=True,
                    hide_index=True
                )
    else:
        st.warning("O banco de dados filtrado está vazio. Ajuste os filtros.")

# --- ABA 2: MAPA DE CALOR ---
# --- CONTEÚDO DA ABA MAPA ---
# --- CONTEÚDO DA ABA MAPA ---
with aba_mapa:
    if uf_selecionada == 'Todas':
        st.info("🗺️ Selecione um Estado (UF) específico no filtro lateral para gerar o mapa. A renderização simultânea de todo o território nacional excede o limite de memória.")
    elif not df_filtrado.empty:
        st.subheader(f"Mapa de Calor de Acidentes - {uf_selecionada} (Escala Logarítmica)")
        
        # 1. Agrega os dados em nível municipal
        df_mapa = (
            df_filtrado.groupby('cod_municipio', observed=False)
            .size()
            .reset_index(name='Casos')
        )
        
        # Garante que a chave é string limpa
        df_mapa['cod_municipio'] = df_mapa['cod_municipio'].astype(str).str.replace(r'\.0$', '', regex=True).str.strip()
        
        # Cria a escala logarítmica (base 10) para definir as cores
        df_mapa['Log_Casos'] = np.log10(df_mapa['Casos'])
        
        # 2. Criação do mapa
        fig_mapa = px.choropleth(
            df_mapa,
            geojson=geojson_brasil, 
            locations='cod_municipio',
            featureidkey='properties.id',
            color='Log_Casos', # Utiliza a coluna logarítmica para a cor
            color_continuous_scale="Reds",
            hover_name='cod_municipio',
            # Oculta o valor do Log na caixa de texto e exibe apenas os Casos Reais
            hover_data={'Log_Casos': False, 'Casos': True}
        )
        
        # 3. Ajustes visuais
        fig_mapa.update_geos(
            fitbounds="locations", 
            visible=False,         
            bgcolor='rgba(0,0,0,0)'
        )
        
        fig_mapa.update_layout(
            margin={"r":0,"t":0,"l":0,"b":0},
            paper_bgcolor='rgba(0,0,0,0)', 
            plot_bgcolor='rgba(0,0,0,0)',
            # Renomeia a legenda para o usuário entender a transformação
            coloraxis_colorbar=dict(title="Log10(Casos)")
        )
        
        st.plotly_chart(fig_mapa, use_container_width=True)
    else:
        st.warning("O banco de dados filtrado está vazio. Ajuste os filtros para visualizar o mapa.")