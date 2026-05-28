import json

notebook_path = 'dados_picada.ipynb'
with open(notebook_path, 'r', encoding='utf-8') as f:
    nb = json.load(f)

code = """import pandas as pd

# 1. Carregar os dados de 2007 a 2026
df_all = pd.read_parquet('dados_2007_2026.parquet')

# 2. Remover todas as observações em que o ano é 2024 (usando a coluna NU_ANO)
df_all_filtered = df_all[df_all['NU_ANO'].astype(str) != '2024']

# 3. Carregar os dados corretos de 2024
df_2024 = pd.read_parquet('sinan_animais_peconhentos_2024.parquet')

# 4. Juntar os dois dataframes
dados_corrigidos = pd.concat([df_all_filtered, df_2024], ignore_index=True)

# 5. Salvar o novo dataframe corrigido
dados_corrigidos.to_parquet('dados_corrigidos.parquet')

# Exibir informações do novo dataframe
print(f"Tamanho do dataframe original filtrado: {len(df_all_filtered)}")
print(f"Tamanho do dataframe de 2024 inserido: {len(df_2024)}")
print(f"Tamanho final de dados_corrigidos: {len(dados_corrigidos)}")
dados_corrigidos.head()"""

new_cell = {
    "cell_type": "code",
    "execution_count": None,
    "metadata": {},
    "outputs": [],
    "source": [line + "\n" if i < len(code.split('\n')) - 1 else line for i, line in enumerate(code.split('\n'))]
}

nb['cells'].append(new_cell)

with open(notebook_path, 'w', encoding='utf-8') as f:
    json.dump(nb, f, indent=1)
