import os
from datetime import datetime

import pandas as pd
import yfinance as yf


# ==========================================
# CONFIGURAÇÕES
# ==========================================

# Lista de ativos que serão monitorados
TICKERS = [
    "PETR4.SA",
    "VALE3.SA",
    "ITUB4.SA",
    "BBDC4.SA",
    "BBAS3.SA",
    "WEGE3.SA",
    "ABEV3.SA",
    "MGLU3.SA"
]


# ==========================================
# FUNÇÃO DE EXTRAÇÃO
# ==========================================

def extract_market_data(ticker):
    """
    Extrai dados históricos de um ativo financeiro
    utilizando a biblioteca yfinance.
    """

    try:
        print(f"Coletando dados de {ticker}...")

        # Cria o objeto do ativo
        asset = yf.Ticker(ticker)

        # Busca dados históricos
        data = asset.history(
            period="6mo",
            interval="1d"
        )

        # Verifica se existem dados
        if data.empty:
            print(f"Nenhum dado encontrado para {ticker}")
            return None

        # Transforma o índice de data em coluna
        data = data.reset_index()

        # Adiciona o ticker
        data["ticker"] = ticker

        # Mantém apenas as colunas necessárias
        data = data[
            [
                "Date",
                "ticker",
                "Open",
                "High",
                "Low",
                "Close",
                "Volume"
            ]
        ]

        # Calcula a variação percentual diária
        data["daily_variation_pct"] = (
            data["Close"]
            .pct_change()
            .mul(100)
        )

        return data

    except Exception as error:

        print(
            f"Erro ao coletar dados de {ticker}: {error}"
        )

        return None


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def main():

    print("=" * 50)
    print("INICIANDO COLETA DE DADOS FINANCEIROS")
    print("=" * 50)

    # Lista para armazenar os dados coletados
    all_data = []

    # Percorre todos os ativos
    for ticker in TICKERS:

        data = extract_market_data(ticker)

        # Adiciona apenas dados válidos
        if data is not None:
            all_data.append(data)

    # Verifica se algum dado foi coletado
    if not all_data:

        print("\nNenhum dado foi coletado.")
        return

    # Une os dados de todos os ativos
    final_data = pd.concat(
        all_data,
        ignore_index=True
    )

    # ==========================================
    # DATA DE EXECUÇÃO
    # ==========================================

    execution_date = datetime.now()

    year = execution_date.strftime("%Y")
    month = execution_date.strftime("%m")
    day = execution_date.strftime("%d")

    # ==========================================
    # CAMADA RAW PARTICIONADA
    # ==========================================

    raw_path = (
        f"data/raw/market_data/"
        f"year={year}/"
        f"month={month}/"
        f"day={day}"
    )

    # Cria os diretórios caso não existam
    os.makedirs(
        raw_path,
        exist_ok=True
    )

    # Caminho final do arquivo
    output_path = (
        f"{raw_path}/market_data.csv"
    )

    # Salva os dados no formato CSV
    final_data.to_csv(
        output_path,
        index=False
    )

    # ==========================================
    # RESULTADOS
    # ==========================================

    print("\n" + "=" * 50)
    print("COLETA FINALIZADA COM SUCESSO!")
    print("=" * 50)

    print(f"\nTotal de registros coletados: {len(final_data)}")

    print(
        f"\nArquivo salvo em:\n{output_path}"
    )

    print("\nPrévia dos dados:")

    print(
        final_data.head()
    )


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    main()