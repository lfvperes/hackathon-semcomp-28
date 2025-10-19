import requests
import json
import pandas as pd
from datetime import datetime
import os
import re
from collections import Counter

# ============ PARTE 1: REQUISIÇÃO DA API ============

def fazer_requisicao_news():
    """Faz a requisição para a API de News da Alpha Vantage"""
    
    api_key = "HE6JJP6N87RFIOD9"
    url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers=AAPL&apikey={api_key}'
    
    try:
        print("🌐 Fazendo requisição para a API...")
        r = requests.get(url)
        r.raise_for_status()
        data = r.json()
        
        # VERIFICAR SE A API RETORNOU ERRO
        if 'Information' in data:
            print(f"❌ ERRO DA API: {data['Information']}")
            return None
        
        if 'Error Message' in data:
            print(f"❌ ERRO DA API: {data['Error Message']}")
            return None
        
        if 'feed' not in data:
            print("❌ Nenhum dado de 'feed' encontrado na resposta da API")
            return None
        
        if not data.get('feed'):
            print("⚠️ O 'feed' de notícias está vazio na resposta da API")
            return None
        
        print(f"✅ API retornou {len(data.get('feed', []))} notícias")
        return data
        
    except requests.exceptions.RequestException as e:
        print(f"❌ Erro na requisição: {e}")
        return None

def salvar_dados_api(data, nome_arquivo='news_sentiments.json'):
    """Salva os dados da API em arquivo JSON"""
    if data is None:
        print("❌ Nenhum dado para salvar")
        return None
    
    try:
        diretorio_saida = r'C:\Users\Acer\Downloads'
        caminho_completo = os.path.join(diretorio_saida, nome_arquivo)
        
        os.makedirs(diretorio_saida, exist_ok=True)
        
        with open(caminho_completo, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        
        print(f"💾 Dados salvos com sucesso em: '{caminho_completo}'")
        return caminho_completo
        
    except Exception as e:
        print(f"❌ Erro ao salvar arquivo: {e}")
        return None

# ============ PARTE 2: PROCESSAMENTO DOS DADOS ============

def processar_news_sentiments(arquivo_json):
    """
    Processa arquivo JSON de News & Sentiments
    """
    
    try:
        with open(arquivo_json, 'r', encoding='utf-8') as file:
            dados = json.load(file)
        
        print("✅ Arquivo de News carregado com sucesso!")
        
        if 'feed' not in dados:
            print("❌ Nenhum dado de 'feed' encontrado no arquivo")
            return None
        
        feed_noticias = dados.get('feed', [])
        if not feed_noticias:
            print("⚠️ O 'feed' de notícias está vazio")
            return None
        
        print(f"📊 Processando {len(feed_noticias)} notícias...")
        
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
            'total_noticias': len(feed_noticias),
            'items_retornados': int(dados.get('items', len(feed_noticias))),
            'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'definicao_sentimento': dados.get('sentiment_score_definition', ''),
            'definicao_relevancia': dados.get('relevance_score_definition', ''),
            'periodo_cobertura': extrair_periodo_noticias(feed_noticias)
        }
        
        # PROCESSAR CADA NOTÍCIA
        noticias_processadas = []
        todos_tickers = []
        
        for noticia in feed_noticias:
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
            
            estrutura_organizada['analise_sentimentos'] = {
                'total_noticias_processadas': len(noticias_processadas),
                'distribuicao_sentimentos': df_noticias['label_sentimento'].value_counts().to_dict(),
                'score_sentimento_medio': round(df_noticias['score_sentimento'].mean(), 4) if 'score_sentimento' in df_noticias.columns else 0,
                'quantidade_fontes': df_noticias['fonte_publicacao'].nunique() if 'fonte_publicacao' in df_noticias.columns else 0,
                'topicos_principais': obter_topics_mais_comuns(noticias_processadas)
            }
            
            # ESTATÍSTICAS DETALHADAS - CORRIGIDO
            estrutura_organizada['estatisticas_detalhadas'] = {
                'publicacoes_por_fonte': df_noticias['fonte_publicacao'].value_counts().to_dict() if 'fonte_publicacao' in df_noticias.columns else {},
                'publicacoes_por_data': df_noticias['data_publicacao'].value_counts().to_dict() if 'data_publicacao' in df_noticias.columns else {},
                'evolucao_sentimento_diaria': calcular_evolucao_sentimento(df_noticias)  # Esta função foi corrigida
            }
            
            # ANÁLISE POR TICKER
            if not df_tickers.empty:
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
                topic_name = topic.split(' (relevância:')[0].strip()
                all_topics.append(topic_name)
    return dict(Counter(all_topics).most_common(10))

def calcular_evolucao_sentimento(df_noticias):
    """Calcular evolução do sentimento por dia - CORRIGIDA"""
    try:
        if 'data_publicacao' not in df_noticias.columns or 'score_sentimento' not in df_noticias.columns:
            return {}
            
        df_noticias['data'] = pd.to_datetime(df_noticias['data_publicacao']).dt.date
        
        # CORREÇÃO: Converter datas para string antes de criar o dicionário
        evolucao = df_noticias.groupby('data').agg({
            'score_sentimento': 'mean',
            'titulo': 'count'
        }).round(4)
        
        # Converter o índice de data para string
        evolucao_dict = {}
        for data, row in evolucao.iterrows():
            data_str = data.strftime('%Y-%m-%d')  # Converter date para string
            evolucao_dict[data_str] = {
                'sentimento_medio': float(row['score_sentimento']),
                'total_noticias': int(row['titulo'])
            }
        
        return evolucao_dict
        
    except Exception as e:
        print(f"⚠️ Aviso na evolução de sentimento: {e}")
        return {}

# ============ PARTE 3: EXPORTAÇÃO ============

def exportar_resultados(dados_estruturados, prefixo="news_sentiments"):
    """Exporta os dados estruturados em JSON e CSV"""
    
    if not dados_estruturados:
        print("❌ Nenhum dado para exportar!")
        return
    
    try:
        diretorio_saida = r'C:\Users\Acer\Downloads'
        
        # 1. Exportar JSON completo
        caminho_json = os.path.join(diretorio_saida, f"{prefixo}_estruturado.json")
        with open(caminho_json, 'w', encoding='utf-8') as f:
            json.dump(dados_estruturados, f, indent=2, ensure_ascii=False, default=str)
        print(f"💾 JSON salvo: {caminho_json}")
        
        # 2. Exportar notícias em CSV
        if dados_estruturados['feed_noticias']:
            df_noticias = pd.DataFrame(dados_estruturados['feed_noticias'])
            caminho_csv = os.path.join(diretorio_saida, f"{prefixo}_noticias.csv")
            df_noticias.to_csv(caminho_csv, index=False, encoding='utf-8')
            print(f"💾 CSV salvo: {caminho_csv}")
            
            # 3. Exportar análise de tickers em CSV
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
                caminho_tickers = os.path.join(diretorio_saida, f"{prefixo}_tickers.csv")
                df_tickers.to_csv(caminho_tickers, index=False, encoding='utf-8')
                print(f"💾 CSV de tickers salvo: {caminho_tickers}")
        
        print("✅ Exportação concluída com sucesso!")
        
    except Exception as e:
        print(f"❌ Erro na exportação: {e}")
        import traceback
        traceback.print_exc()

# ============ EXECUÇÃO PRINCIPAL ============

if __name__ == "__main__":
    print("🚀 INICIANDO PROCESSAMENTO DE NEWS & SENTIMENTS")
    print("=" * 60)
    
    # 1. Fazer requisição para a API
    dados_api = fazer_requisicao_news()
    
    if dados_api is None:
        print("❌ Falha na obtenção dos dados da API")
        exit()
    
    # 2. Salvar dados da API
    caminho_arquivo = salvar_dados_api(dados_api)
    
    if caminho_arquivo is None:
        print("❌ Falha ao salvar dados da API")
        exit()
    
    # 3. Processar dados
    dados_news = processar_news_sentiments(caminho_arquivo)
    
    if dados_news:
        print("\n" + "=" * 50)
        print("✅ DADOS ORGANIZADOS COM SUCESSO!")
        print("=" * 50)
        
        metadados = dados_news['metadados_gerais']
        analise = dados_news['analise_sentimentos']
        
        print(f"📊 Total de notícias processadas: {metadados.get('total_noticias', 0)}")
        print(f"📈 Sentimento médio: {analise.get('score_sentimento_medio', 'N/A')}")
        print(f"🎯 Fontes únicas: {analise.get('quantidade_fontes', 0)}")
        
        # Verificar distribuição de sentimentos
        distribuicao = analise.get('distribuicao_sentimentos', {})
        if distribuicao:
            print(f"\n📋 DISTRIBUIÇÃO DE SENTIMENTOS:")
            for sentimento, quantidade in distribuicao.items():
                print(f"   {sentimento}: {quantidade} notícias")
        
        # Verificar tickers
        if dados_news.get('tickers_analisados'):
            tickers_info = dados_news['tickers_analisados']
            print(f"\n💹 TICKERS ANALISADOS:")
            print(f"   Total de tickers únicos: {tickers_info.get('total_tickers_unicos', 0)}")
            
            tickers_mais_citados = tickers_info.get('tickers_mais_citados', {})
            if tickers_mais_citados:
                print(f"\n🏆 TOP 5 TICKERS MAIS CITADOS:")
                for i, (ticker, count) in enumerate(list(tickers_mais_citados.items())[:5], 1):
                    print(f"   {i}. {ticker}: {count} menções")
        
        # Verificar evolução do sentimento
        evolucao = dados_news['estatisticas_detalhadas'].get('evolucao_sentimento_diaria', {})
        if evolucao:
            print(f"\n📅 EVOLUÇÃO DO SENTIMENTO POR DIA:")
            for data, info in list(evolucao.items())[:3]:  # Mostrar apenas 3 primeiros dias
                print(f"   {data}: Sentimento {info['sentimento_medio']} ({info['total_noticias']} notícias)")
        
        # 4. Exportar resultados
        print(f"\n📤 EXPORTANDO RESULTADOS...")
        exportar_resultados(dados_news)
        
        print("\n" + "=" * 50)
        print("🎉 PROCESSAMENTO CONCLUÍDO!")
        print("=" * 50)
        
    else:
        print("❌ Falha no processamento dos dados!")