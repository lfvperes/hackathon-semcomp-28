import requests
import json
import pandas as pd
from datetime import datetime
import os
import pathlib as Path
import re
from collections import Counter

url = 'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=ERJ&apikey=HE6JJP6N87RFIOD9'
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
    nome_do_arquivo = 'news_sentiments.json'
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

import json
import pandas as pd
import os
from datetime import datetime
import re
from collections import Counter

def processar_news_sentiments(arquivo_json):
    """
    Processa arquivo JSON de News & Sentiments
    Args:
        arquivo_json: caminho do arquivo ou nome se estiver na mesma pasta
    """
    
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as file:
            dados = json.load(file)
        
        print("✅ Arquivo de News carregado com sucesso!")
        
        # ESTRUTURA PRINCIPAL
        estrutura_organizada = {
            'metadados_gerais': {},
            'feed_noticias': [],
            'analise_sentimentos': {},
            'estatisticas_detalhadas': {},
            'tickers_analisados': {}
        }
        
        # METADADOS GERAIS
        estrutura_organizada['metadados_gerais'] = {
            'total_noticias': int(dados.get('items', 0)),
            'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'definicao_sentimento': dados.get('sentiment_score_definition', ''),
            'definicao_relevancia': dados.get('relevance_score_definition', ''),
            'periodo_cobertura': extrair_periodo_noticias(dados.get('feed', []))
        }
        
        # PROCESSAR CADA NOTÍCIA
        noticias_processadas = []
        todos_tickers = []
        
        for noticia in dados.get('feed', []):
            noticia_processada = {
                'titulo': noticia.get('title', ''),
                'resumo': noticia.get('summary', ''),
                'fonte_publicacao': noticia.get('source', ''),
                'dominio_fonte': noticia.get('source_domain', ''),
                'data_publicacao': formatar_data(noticia.get('time_published', '')),
                'url_noticia': noticia.get('url', ''),
                'autores': ', '.join(noticia.get('authors', [])),
                'imagem_capa': noticia.get('banner_image', ''),
                'categoria': noticia.get('category_within_source', ''),
                'score_sentimento': noticia.get('overall_sentiment_score', 0),
                'label_sentimento': noticia.get('overall_sentiment_label', 'Neutral'),
                'topicos': processar_topics(noticia.get('topics', [])),
                'sentimento_tickers': processar_ticker_sentiment(noticia.get('ticker_sentiment', []))
            }
            
            noticias_processadas.append(noticia_processada)
            
            # Coletar todos os tickers para análise agregada
            for ticker in noticia.get('ticker_sentiment', []):
                todos_tickers.append({
                    'ticker': ticker.get('ticker'),
                    'score_relevancia': float(ticker.get('relevance_score', 0)),
                    'score_sentimento': float(ticker.get('ticker_sentiment_score', 0)),
                    'label_sentimento': ticker.get('ticker_sentiment_label', 'Neutral'),
                    'titulo_noticia': noticia.get('title', ''),
                    'data_publicacao': formatar_data(noticia.get('time_published', ''))
                })
        
        estrutura_organizada['feed_noticias'] = noticias_processadas
        
        # ANÁLISE DE SENTIMENTOS
        if noticias_processadas:
            df_noticias = pd.DataFrame(noticias_processadas)
            df_tickers = pd.DataFrame(todos_tickers)
            
            # CORREÇÃO: Usar .get() para evitar KeyError
            estrutura_organizada['analise_sentimentos'] = {
                'total_noticias_processadas': len(noticias_processadas),
                'distribuicao_sentimentos': df_noticias['label_sentimento'].value_counts().to_dict(),
                'score_sentimento_medio': round(df_noticias['score_sentimento'].mean(), 4) if 'score_sentimento' in df_noticias.columns else 0,
                'quantidade_fontes': df_noticias['fonte_publicacao'].nunique() if 'fonte_publicacao' in df_noticias.columns else 0,
                'topicos_principais': obter_topics_mais_comuns(noticias_processadas)
            }
            
            # ESTATÍSTICAS DETALHADAS
            estrutura_organizada['estatisticas_detalhadas'] = {
                'publicacoes_por_fonte': df_noticias['fonte_publicacao'].value_counts().to_dict() if 'fonte_publicacao' in df_noticias.columns else {},
                'publicacoes_por_data': df_noticias['data_publicacao'].value_counts().to_dict() if 'data_publicacao' in df_noticias.columns else {},
                'evolucao_sentimento_diaria': calcular_evolucao_sentimento(df_noticias)
            }
            
            # ANÁLISE POR TICKER
            if not df_tickers.empty:
                # Calcular estatísticas por ticker
                stats_tickers = df_tickers.groupby('ticker').agg({
                    'score_sentimento': ['mean', 'count'],
                    'score_relevancia': 'mean'
                }).round(4)
                
                # Converter para dicionário de forma limpa
                sentiment_por_ticker = {}
                for ticker in stats_tickers.index:
                    sentiment_por_ticker[ticker] = {
                        'sentimento_medio': stats_tickers.loc[ticker, ('score_sentimento', 'mean')],
                        'total_mencoes': stats_tickers.loc[ticker, ('score_sentimento', 'count')],
                        'relevancia_media': stats_tickers.loc[ticker, ('score_relevancia', 'mean')]
                    }
                
                estrutura_organizada['tickers_analisados'] = {
                    'total_tickers_unicos': df_tickers['ticker'].nunique(),
                    'analise_sentimento_tickers': sentiment_por_ticker,
                    'tickers_mais_citados': df_tickers['ticker'].value_counts().head(10).to_dict()
                }
        
        return estrutura_organizada
        
    except Exception as e:
        print(f"❌ Erro ao processar news: {e}")
        import traceback
        traceback.print_exc()
        return None

# FUNÇÕES AUXILIARES
def formatar_data(data_string):
    """Converter data do formato 20251018T170133 para 2025-10-18 17:01:33"""
    if not data_string:
        return ''
    try:
        match = re.match(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})', data_string)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)} {match.group(4)}:{match.group(5)}:{match.group(6)}"
        return data_string
    except:
        return data_string

def processar_topics(topics):
    """Processar lista de tópicos"""
    return [f"{topic.get('topic', '')} (relevância: {topic.get('relevance_score', '0')})" 
            for topic in topics]

def processar_ticker_sentiment(ticker_sentiment):
    """Processar sentimentos por ticker"""
    return [f"{ticker.get('ticker', '')}: {ticker.get('ticker_sentiment_label', 'Neutral')} " +
            f"(score: {ticker.get('ticker_sentiment_score', '0')}, " +
            f"relevância: {ticker.get('relevance_score', '0')})" 
            for ticker in ticker_sentiment]

def extrair_periodo_noticias(feed):
    """Extrair período de cobertura das notícias"""
    if not feed:
        return "N/A"
    
    datas = [formatar_data(noticia.get('time_published', '')) for noticia in feed]
    datas_validas = [d for d in datas if d]
    
    if datas_validas:
        return f"{min(datas_validas)} a {max(datas_validas)}"
    return "N/A"

def obter_topics_mais_comuns(noticias):
    """Encontrar tópicos mais frequentes"""
    all_topics = []
    for noticia in noticias:
        for topic in noticia.get('topicos', []):
            if isinstance(topic, str):
                # Extrair apenas o nome do tópico (remover relevância)
                topic_name = topic.split(' (relevância:')[0].strip()
                all_topics.append(topic_name)
    
    return dict(Counter(all_topics).most_common(10))

def calcular_evolucao_sentimento(df_noticias):
    """Calcular evolução do sentimento por dia"""
    try:
        if 'data_publicacao' not in df_noticias.columns or 'score_sentimento' not in df_noticias.columns:
            return {}
            
        df_noticias['data'] = pd.to_datetime(df_noticias['data_publicacao']).dt.date
        evolucao = df_noticias.groupby('data').agg({
            'score_sentimento': 'mean',
            'titulo': 'count'
        }).round(4)
        
        # CORREÇÃO: Converter datas para string
        evolucao_dict = {}
        for data, row in evolucao.iterrows():
            data_str = data.strftime('%Y-%m-%d')  # Converter para string
            evolucao_dict[data_str] = {
                'sentimento_medio': float(row['score_sentimento']),
                'total_noticias': int(row['titulo'])
            }
        
        return evolucao_dict
        
    except:
        return {}

# FUNÇÃO PARA EXPORTAR RESULTADOS - CORRIGIDA (SEM EXCEL)
def exportar_resultados(dados_estruturados, prefixo="news_sentiments"):
    """Exporta os dados estruturados em JSON e CSV apenas"""
    
    if not dados_estruturados:
        print("❌ Nenhum dado para exportar!")
        return
    
    try:
        # 1. Exportar JSON completo - CORREÇÃO: adicionar default=str
        with open(f"{prefixo}_estruturado.json", 'w', encoding='utf-8') as f:
            json.dump(dados_estruturados, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 JSON salvo: {prefixo}_estruturado.json")
        
        # 2. Exportar notícias em CSV
        if dados_estruturados['feed_noticias']:
            df_noticias = pd.DataFrame(dados_estruturados['feed_noticias'])
            df_noticias.to_csv(f"{prefixo}_noticias.csv", index=False, encoding='utf-8')
            print(f"💾 CSV salvo: {prefixo}_noticias.csv")
            
        # 3. Exportar análise de tickers em CSV separado
        if dados_estruturados.get('tickers_analisados'):
            tickers_data = []
            for ticker, info in dados_estruturados['tickers_analisados']['analise_sentimento_tickers'].items():
                tickers_data.append({
                    'ticker': ticker,
                    'sentimento_medio': info['sentimento_medio'],
                    'total_mencoes': info['total_mencoes'],
                    'relevancia_media': info['relevancia_media']
                })
            
            df_tickers = pd.DataFrame(tickers_data)
            df_tickers.to_csv(f"{prefixo}_tickers_analise.csv", index=False, encoding='utf-8')
            print(f"💾 CSV de tickers salvo: {prefixo}_tickers_analise.csv")
        
        print("✅ Exportação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")

# EXECUÇÃO PRINCIPAL COM VERIFICAÇÕES
if __name__ == "__main__":
    # SUBSTITUA pelo caminho real do seu arquivo
    caminho_arquivo = r"C:\Users\Acer\Downloads\news_sentiments.json"
    
    print("🚀 INICIANDO PROCESSAMENTO DE NEWS & SENTIMENTS")
    print("=" * 60)
    
    # Verificar se arquivo existe
    if not os.path.exists(caminho_arquivo):
        print(f"❌ Arquivo não encontrado: {caminho_arquivo}")
        print("📁 Arquivos na pasta Downloads:")
        downloads_path = r"C:\Users\Acer\Downloads"
        for arquivo in os.listdir(downloads_path):
            if arquivo.endswith('.json'):
                print(f"   📄 {arquivo}")
    else:
        dados_news = processar_news_sentiments(caminho_arquivo)
        
        if dados_news:
            print("\n✅ DADOS ORGANIZADOS COM SUCESSO!")
            
            # CORREÇÃO: Usar .get() para evitar KeyError ao exibir
            metadados = dados_news['metadados_gerais']
            analise = dados_news['analise_sentimentos']
            
            print(f"📊 Total de notícias: {metadados.get('total_noticias', 0)}")
            print(f"📈 Sentimento médio: {analise.get('score_sentimento_medio', 'N/A')}")
            print(f"🎯 Fontes únicas: {analise.get('quantidade_fontes', 0)}")
            
            # Verificar distribuição de sentimentos
            distribuicao = analise.get('distribuicao_sentimentos', {})
            if distribuicao:
                print(f"📋 Distribuição de sentimentos:")
                for sentimento, quantidade in distribuicao.items():
                    print(f"   {sentimento}: {quantidade}")
            
            # Verificar tickers
            if dados_news.get('tickers_analisados'):
                tickers_info = dados_news['tickers_analisados']
                print(f"💹 Tickers analisados: {tickers_info.get('total_tickers_unicos', 0)}")
                
                tickers_mais_citados = tickers_info.get('tickers_mais_citados', {})
                if tickers_mais_citados:
                    print(f"🏆 Tickers mais citados:")
                    for ticker, count in list(tickers_mais_citados.items())[:5]:
                         print(f"   {ticker}: {count} menções")
            
            # Exportar resultados
            exportar_resultados(dados_news)
            
            print("\n🎉 PROCESSAMENTO CONCLUÍDO!")
        else:
            print("❌ Falha no processamento dos dados!")