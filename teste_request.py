import requests
import json
import pandas as pd
from datetime import datetime
import os
import pathlib as Path

url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=ERJ&apikey=HE6JJP6N87RFIOD9'
r = requests.get(url)
data = r.json()
print(data)


try:
    r = requests.get(url)
    r.raise_for_status()  # Verifica se houve erros na requisição
    data = r.json()

    # --- Parte alterada ---
    # Define o caminho completo para salvar o arquivo
    diretorio_saida = r'C:\Users\Acer\Downloads'
    nome_do_arquivo = 'diario_api.json'
    caminho_completo = os.path.join(diretorio_saida, nome_do_arquivo)
    # --------------------

    # Garante que o diretório de destino exista antes de salvar
    os.makedirs(diretorio_saida, exist_ok=True)

    # Salva o arquivo no caminho especificado
    with open(caminho_completo, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

    print(f"Os dados foram salvos com sucesso em: '{caminho_completo}'")

except requests.exceptions.RequestException as e:
    print(f"Ocorreu um erro ao fazer a requisição: {e}")
except json.JSONDecodeError:
    print("Ocorreu um erro ao decodificar o JSON da resposta.")
    
#########
#ESTRUTURAÇÃO DOS METADADOS
#########


def processar_dados_simples():
    # Caminho direto como string
    caminho_arquivo = r'C:\Users\Acer\Downloads\diario_api.json'  # SUBSTITUA pelo nome real
    
    print(f"📁 Procurando: {caminho_arquivo}")
    
    # Verificar se arquivo existe
    if not os.path.exists(caminho_arquivo):
        print("❌ Arquivo não encontrado!")
        return None
    
    try:
        # Ler arquivo
        with open(caminho_arquivo, 'r', encoding='utf-8') as file:
            dados = json.load(file)
        
        print("✅ Arquivo carregado com sucesso!")
        
        # Converter diretamente para DataFrame
        time_series = dados["Time Series (Daily)"]
        df = pd.DataFrame.from_dict(time_series, orient='index')
        
        # Limpar colunas
        df.columns = [col.split('. ')[1] for col in df.columns]
        
        # Converter tipos
        df = df.astype({
            'open': float, 'high': float, 'low': float, 'close': float, 'volume': int
        })
        
        # Ordenar
        df.index = pd.to_datetime(df.index)
        df = df.sort_index(ascending=False)
        
        # Metadados simples
        metadados = {
            'Símbolo': dados["Meta Data"]["2. Symbol"],
            'Última Atualização': dados["Meta Data"]["3. Last Refreshed"],
            'Período': f"{df.index.min().strftime('%d/%m/%Y')} a {df.index.max().strftime('%d/%m/%Y')}",
            'Total de Dias': len(df)
        }
        
        return {'metadados': metadados, 'dados': df}
        
    except Exception as e:
        print(f"❌ Erro: {e}")
        return None

# Usar versão simples
resultado = processar_dados_simples()

if resultado:
    print("\n📊 METADADOS:")
    for chave, valor in resultado['metadados'].items():
        print(f"   {chave}: {valor}")
    
    print(f"\n📈 DADOS (primeiras 5 linhas de {len(resultado['dados'])}):")
    print(resultado['dados'].head())
    
    # Salvar CSV
    caminho_saida = r'C:\Users\Acer\Downloads\dados_organizados.csv'
    resultado['dados'].to_csv(caminho_saida)
    print(f"\n💾 Arquivo salvo em: {caminho_saida}")