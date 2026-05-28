"""
Script para baixar dados de Acidentes com Animais Peçonhentos (ANIM)
do SINAN via PySUS, desde 2007, e salvar em um único arquivo .parquet.

Mantém todas as variáveis originais.
"""

import pandas as pd
from pysus import sinan
import time
import sys

# Anos desde 2007 até 2024 (último ano com dados consolidados disponíveis)
ANOS = list(range(2007, 2025))

OUTPUT_FILE = "/home/gabrielgraciano/analises_vigitrop/sinan_animais_peconhentos_2007_2024.parquet"


def main():
    frames = []

    for ano in ANOS:
        print(f"\n{'='*60}")
        print(f"Baixando dados do ano {ano}...")
        print(f"{'='*60}")
        t0 = time.time()

        try:
            df = sinan(disease="ANIM", year=ano)
            n_rows = len(df)
            n_cols = len(df.columns)
            elapsed = time.time() - t0
            print(f"  -> {n_rows:,} registros, {n_cols} variáveis ({elapsed:.1f}s)")
            frames.append(df)
        except Exception as e:
            print(f"  -> ERRO ao baixar {ano}: {e}", file=sys.stderr)
            # Tenta novamente após uma pausa
            print(f"  -> Tentando novamente em 10s...")
            time.sleep(10)
            try:
                df = sinan(disease="ANIM", year=ano)
                n_rows = len(df)
                n_cols = len(df.columns)
                elapsed = time.time() - t0
                print(f"  -> (retry) {n_rows:,} registros, {n_cols} variáveis ({elapsed:.1f}s)")
                frames.append(df)
            except Exception as e2:
                print(f"  -> ERRO definitivo para {ano}: {e2}", file=sys.stderr)

    if not frames:
        print("\nNenhum dado foi baixado. Verifique a conexão.", file=sys.stderr)
        sys.exit(1)

    print(f"\n{'='*60}")
    print("Concatenando todos os DataFrames...")
    df_final = pd.concat(frames, ignore_index=True)

    print(f"Total: {len(df_final):,} registros, {len(df_final.columns)} variáveis")
    print(f"Colunas: {list(df_final.columns)}")
    print(f"\nAnos presentes nos dados:")
    # Tenta mostrar distribuição por ano de notificação
    for col in ["NU_ANO", "DT_NOTIFIC", "ANO_NASC"]:
        if col in df_final.columns:
            print(f"  (baseado em '{col}')")
            break

    print(f"\nSalvando em: {OUTPUT_FILE}")
    df_final.to_parquet(OUTPUT_FILE, index=False, engine="pyarrow")

    # Verificação
    df_check = pd.read_parquet(OUTPUT_FILE)
    print(f"Verificação: {len(df_check):,} registros lidos do parquet")
    print(f"\nInfo do DataFrame:")
    print(df_final.dtypes)
    print(f"\n{'='*60}")
    print("CONCLUÍDO COM SUCESSO!")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
