import os
from datetime import datetime

import pandas as pd


# ==========================================
# CONFIGURAÇÕES
# ==========================================

RAW_BASE_PATH = "data/raw/market_data"
PROCESSED_BASE_PATH = "data/processed/market_data"


# ==========================================
# LOCALIZAR ARQUIVO RAW MAIS RECENTE
# ==========================================

def get_latest_raw_file():
    """
    Localiza o arquivo CSV mais recente
    dentro da camada RAW.
    """

    csv_files = []

    for root, _, files in os.walk(RAW_BASE_PATH):

        for file in files:

            if file.endswith(".csv"):

                file_path = os.path.join(
                    root,
                    file
                )

                csv_files.append(file_path)

    if not csv_files:

        raise FileNotFoundError(
            "Nenhum arquivo CSV encontrado "
            "na camada RAW."
        )

    # Retorna o arquivo mais recentemente modificado
    latest_file = max(
        csv_files,
        key=os.path.getmtime
    )

    return latest_file


# ==========================================
# TRANSFORMAÇÃO DOS DADOS
# ==========================================

def transform_data(data):
    """
    Realiza a limpeza e transformação
    dos dados financeiros.
    """

    print("\nIniciando transformação dos dados...")

    # Cria uma cópia para evitar alterações
    # no DataFrame original
    df = data.copy()

    print(
        f"Registros antes da transformação: {len(df)}"
    )

    # ==========================================
    # REMOVER DUPLICADOS
    # ==========================================

    df = df.drop_duplicates()

    print(
        f"Registros após remover duplicados: {len(df)}"
    )

    # ==========================================
    # TRATAR VALORES NULOS
    # ==========================================

    # Converte a coluna de variação para número
    df["daily_variation_pct"] = pd.to_numeric(
        df["daily_variation_pct"],
        errors="coerce"
    )

    # A primeira variação de cada ativo pode ser nula,
    # pois não existe um dia anterior para comparação.
    df["daily_variation_pct"] = (
        df.groupby("ticker")[
            "daily_variation_pct"
        ].fillna(0)
    )

    # Remove registros que possuam valores
    # nulos nas colunas essenciais
    essential_columns = [
        "Date",
        "ticker",
        "Open",
        "High",
        "Low",
        "Close",
        "Volume"
    ]

    df = df.dropna(
        subset=essential_columns
    )

    # ==========================================
    # PADRONIZAÇÃO DE DADOS
    # ==========================================

    # Converte a coluna Date para datetime
    df["Date"] = pd.to_datetime(
        df["Date"]
    )

    # Ordena os dados
    df = df.sort_values(
        by=[
            "ticker",
            "Date"
        ]
    )

    # ==========================================
    # REGRA DE COMPLIANCE
    # ==========================================

    df["status_alerta"] = (
        df["daily_variation_pct"]
        .abs()
        .apply(
            lambda value:
            "Alerta de Risco"
            if value > 5
            else "Normal"
        )
    )

    # ==========================================
    # COLUNAS DE PARTIÇÃO
    # ==========================================

    df["year"] = (
        df["Date"]
        .dt.year
    )

    df["month"] = (
        df["Date"]
        .dt.month
    )

    df["day"] = (
        df["Date"]
        .dt.day
    )

    print(
        f"Registros após transformação: {len(df)}"
    )

    return df


# ==========================================
# SALVAR CAMADA PROCESSED
# ==========================================

def save_processed_data(data):
    """
    Salva os dados transformados
    na camada PROCESSED em Parquet.
    """

    print(
        "\nSalvando dados na camada PROCESSED..."
    )

    # Data da execução
    execution_date = datetime.now()

    year = execution_date.strftime("%Y")
    month = execution_date.strftime("%m")
    day = execution_date.strftime("%d")

    # Caminho particionado
    processed_path = (
        f"{PROCESSED_BASE_PATH}/"
        f"year={year}/"
        f"month={month}/"
        f"day={day}"
    )

    # Cria o diretório
    os.makedirs(
        processed_path,
        exist_ok=True
    )

    # Caminho do arquivo Parquet
    output_path = (
        f"{processed_path}/"
        f"market_data_processed.parquet"
    )

    # Salva no formato Parquet
    data.to_parquet(
        output_path,
        index=False
    )

    print(
        "Dados processados salvos com sucesso!"
    )

    print(
        f"\nArquivo:\n{output_path}"
    )

    return output_path


# ==========================================
# FUNÇÃO PRINCIPAL
# ==========================================

def main():

    print("=" * 50)
    print("INICIANDO PIPELINE DE TRANSFORMAÇÃO")
    print("=" * 50)

    # ==========================================
    # LOCALIZA O ARQUIVO RAW
    # ==========================================

    raw_file = get_latest_raw_file()

    print(
        f"\nArquivo RAW encontrado:\n{raw_file}"
    )

    # ==========================================
    # LEITURA DOS DADOS
    # ==========================================

    print(
        "\nLendo dados da camada RAW..."
    )

    raw_data = pd.read_csv(
        raw_file
    )

    print(
        f"Total de registros lidos: {len(raw_data)}"
    )

    # ==========================================
    # TRANSFORMAÇÃO
    # ==========================================

    processed_data = transform_data(
        raw_data
    )

    # ==========================================
    # SALVAR DADOS
    # ==========================================

    output_path = save_processed_data(
        processed_data
    )

    # ==========================================
    # RESULTADO
    # ==========================================

    total_alerts = len(
        processed_data[
            processed_data[
                "status_alerta"
            ] == "Alerta de Risco"
        ]
    )

    print("\n" + "=" * 50)
    print("TRANSFORMAÇÃO FINALIZADA")
    print("=" * 50)

    print(
        f"\nTotal de registros: "
        f"{len(processed_data)}"
    )

    print(
        f"Total de alertas de risco: "
        f"{total_alerts}"
    )

    print(
        f"\nArquivo processado salvo em:\n"
        f"{output_path}"
    )

    print("\nPrévia dos dados:")

    print(
        processed_data.head()
    )


# ==========================================
# EXECUÇÃO
# ==========================================

if __name__ == "__main__":
    main()