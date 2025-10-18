import requests
import json
import pandas as pd
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

#########
#Noticias
#########
url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey=HE6JJP6N87RFIOD9'
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
    nome_do_arquivo = 'noticias.json'
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

# Ler o arquivo JSON local
with open('saida_api.json', 'r', encoding='utf-8') as file:
    dados_json = json.load(file)

# Converter para DataFrame
df = pd.json_normalize(response_json)

# Organizar colunas
df = df.reindex(sorted(df.columns), axis=1)
print(df.head())