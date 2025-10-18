import requests
import json
import pandas as pd
from datetime import datetime
import os
import pathlib as Path

url = 'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=600104.SHH&outputsize=full&apikey=HE6JJP6N87RFIOD9'
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

# #########
# #Noticias
# #########
# url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=HE6JJP6N87RFIOD9'
# r = requests.get(url)
# data = r.json()
# print(data)


# try:
#     r = requests.get(url)
#     r.raise_for_status()  # Verifica se houve erros na requisição
#     data = r.json()

#     # --- Parte alterada ---
#     # Define o caminho completo para salvar o arquivo
#     diretorio_saida = r'C:\Users\Acer\Downloads'
#     nome_do_arquivo = 'noticias.json'
#     caminho_completo = os.path.join(diretorio_saida, nome_do_arquivo)
#     # --------------------

#     # Garante que o diretório de destino exista antes de salvar
#     os.makedirs(diretorio_saida, exist_ok=True)

#     # Salva o arquivo no caminho especificado
#     with open(caminho_completo, 'w', encoding='utf-8') as f:
#         json.dump(data, f, ensure_ascii=False, indent=4)

#     print(f"Os dados foram salvos com sucesso em: '{caminho_completo}'")

# except requests.exceptions.RequestException as e:
#     print(f"Ocorreu um erro ao fazer a requisição: {e}")
# except json.JSONDecodeError:
#     print("Ocorreu um erro ao decodificar o JSON da resposta.")
    
    
#########
#ESTRUTURAÇÃO DOS METADADOS
#########

def processar_dados_alphavantage():
    # Encontrar pasta Downloads
    downloads_path = Path.home() / "Downloads"
    arquivo_json = downloads_path / "diario_api.json"  # SUBSTITUA pelo nome do seu arquivo
    
    # Verificar se arquivo existe
    if not arquivo_json.exists():
        print("❌ Arquivo não encontrado na pasta Downloads!")
        print("📁 Arquivos JSON disponíveis:")
        for arquivo in downloads_path.glob("*.json"):
            print(f"   📄 {arquivo.name}")
        return None
    
    try:
        # Ler arquivo
        with open(arquivo_json, 'r', encoding='utf-8') as file:
            dados = json.load(file)
        
        print("✅ Arquivo carregado com sucesso!")
        
        # Estruturar metadados
        metadados_organizados = {
            'informacoes_acao': {
                'symbol': dados["Meta Data"]["2. Symbol"],
                'information': dados["Meta Data"]["1. Information"],
                'last_refreshed': dados["Meta Data"]["3. Last Refreshed"],
                'time_zone': dados["Meta Data"]["5. Time Zone"]
            },
            'dados_tecnicos': {
                'output_size': dados["Meta Data"]["4. Output Size"],
                'total_dias': len(dados["Time Series (Daily)"]),
                'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
        }
        
        # Estruturar série temporal
        time_series = dados["Time Series (Daily)"]
        dados_diarios = []
        
        for data, valores in time_series.items():
            dados_diarios.append({
                'date': data,
                'open': float(valores['1. open']),
                'high': float(valores['2. high']),
                'low': float(valores['3. low']),
                'close': float(valores['4. close']),
                'volume': int(valores['5. volume'])
            })
        
        # Criar DataFrame
        df = pd.DataFrame(dados_diarios)
        df['date'] = pd.to_datetime(df['date'])
        df = df.sort_values('date', ascending=False)
        
        resultado = {
            'metadados': metadados_organizados,
            'dados_diarios': df,
            'resumo_estatistico': {
                'preco_medio_close': round(df['close'].mean(), 4),
                'volume_medio': int(df['volume'].mean()),
                'max_high': round(df['high'].max(), 4),
                'min_low': round(df['low'].min(), 4),
                'periodo_inicio': df['date'].min().strftime('%Y-%m-%d'),
                'periodo_fim': df['date'].max().strftime('%Y-%m-%d')
            }
        }
        
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao processar arquivo: {e}")
        return None

# Executar a função
dados_estruturados = processar_dados_alphavantage()

if dados_estruturados:
    print("\n" + "="*50)
    print("METADADOS DA AÇÃO")
    print("="*50)
    for categoria, info in dados_estruturados['metadados'].items():
        print(f"\n{categoria.upper()}:")
        for chave, valor in info.items():
            print(f"  {chave}: {valor}")
    
    print("\n" + "="*50)
    print("PRIMEIRAS 5 LINHAS DOS DADOS")
    print("="*50)
    print(dados_estruturados['dados_diarios'].head())
    
    print("\n" + "="*50)
    print("RESUMO ESTATÍSTICO")
    print("="*50)
    for chave, valor in dados_estruturados['resumo_estatistico'].items():
        print(f"  {chave}: {valor}")