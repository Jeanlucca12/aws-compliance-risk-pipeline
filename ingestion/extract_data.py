import os
from datetime import datetime

import boto3
import pandas as pd
import yfinance as yf


# ==========================================
# CONFIGURAÇÕES
# ==========================================

BUCKET_NAME = "aws-compliance-risk-pipeline"

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
# EXTRAÇÃO DE DADOS
# ==========================================

def extract_market_data(ticker):
    """
    Extrai dados históricos de um ativo financeiro
    utilizando a biblioteca yfinance.
    """

    try:
        print(f"Coletando dados de {ticker}...")

        asset = yf.Ticker(ticker)

        data = asset.history(
            period="6mo",
            interval="1d"
        )

        if data.empty:
            print(f"Nenhum dado encontrado para {ticker}")
            return None

        # Transforma a data do índice em coluna
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
# UPLOAD PARA AMAZON S3
# ==========================================

def upload_to_s3(local_file_path, s3_key):
    """
    Faz upload de um arquivo local para o Amazon S3.
    """

    try:

        print("\nIniciando upload para o Amazon S3...")

        # Cria o cliente S3
        s3_client = boto3.client("s3")

        # Faz upload do arquivo
        s3_client.upload_file(
            local_file_path,
            BUCKET_NAME,
            s3_key
        )

        print("Upload realizado com sucesso!")

        print(
            f"s3://{BUCKET_NAME}/{s3_key}"
        )

    except Exception as error:

        print(
            f"Erro ao fazer upload para o S3: {error}"
        )


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def main():

    print("=" * 50)
    print("INICIANDO PIPELINE DE INGESTÃO")
    print("=" * 50)

    # Lista para armazenar os dados
    all_data = []

    # Percorre todos os ativos
    for ticker in TICKERS:

        data = extract_market_data(ticker)

        if data is not None:
            all_data.append(data)

    # Verifica se dados foram coletados
    if not all_data:

        print("\nNenhum dado foi coletado.")
        return

    # Une todos os dados
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
    # CAMINHO LOCAL - RAW
    # ==========================================

    raw_path = (
        f"data/raw/market_data/"
        f"year={year}/"
        f"month={month}/"
        f"day={day}"
    )

    # Cria os diretórios locais
    os.makedirs(
        raw_path,
        exist_ok=True
    )

    # Arquivo local
    output_path = (
        f"{raw_path}/market_data.csv"
    )

    # Salva os dados
    final_data.to_csv(
        output_path,
        index=False
    )

    # ==========================================
    # CAMINHO NO S3
    # ==========================================

    s3_key = (
        f"raw/market_data/"
        f"year={year}/"
        f"month={month}/"
        f"day={day}/"
        f"market_data.csv"
    )

    # ==========================================
    # UPLOAD PARA S3
    # ==========================================

    upload_to_s3(
        output_path,
        s3_key
    )

    # ==========================================
    # RESULTADOS
    # ==========================================

    print("\n" + "=" * 50)
    print("PIPELINE FINALIZADO")
    print("=" * 50)

    print(
        f"\nTotal de registros coletados: {len(final_data)}"
    )

    print(
        f"\nArquivo local:\n{output_path}"
    )

    print(
        f"\nArquivo no S3:\n"
        f"s3://{BUCKET_NAME}/{s3_key}"
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