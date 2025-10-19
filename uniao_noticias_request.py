import requests
import json
import pandas as pd
from datetime import datetime
import os
import re
from collections import Counter

class AlphaVantageNewsProcessor:
    """
    Classe para processar dados de News & Sentiments da Alpha Vantage API
    """
    
    def __init__(self, api_key="HE6JJP6N87RFIOD9"):
        self.api_key = api_key
        self.dados_brutos = None
        self.dados_estruturados = None
        self.base_path = r'C:\Users\Acer\Downloads'
    
    def fazer_requisicao_api(self, tickers="ERJ"):
        """
        Faz requisição para a API Alpha Vantage
        """
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={tickers}&apikey={self.api_key}'
        
        try:
            print("🌐 Fazendo requisição para a API...")
            r = requests.get(url)
            r.raise_for_status()
            self.dados_brutos = r.json()
            
            # Verificar erros da API
            if 'Information' in self.dados_brutos:
                print(f"❌ ERRO DA API: {self.dados_brutos['Information']}")
                return False
            
            if 'feed' not in self.dados_brutos:
                print("❌ Nenhum dado de 'feed' encontrado")
                return False
            
            print(f"✅ API retornou {len(self.dados_brutos.get('feed', []))} notícias")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
    
    def salvar_dados_brutos(self, nome_arquivo='news_sentiments.json'):
        """
        Salva os dados brutos da API em arquivo JSON
        """
        if self.dados_brutos is None:
            print("❌ Nenhum dado para salvar")
            return None
        
        try:
            caminho_completo = os.path.join(self.base_path, nome_arquivo)
            os.makedirs(self.base_path, exist_ok=True)
            
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                json.dump(self.dados_brutos, f, ensure_ascii=False, indent=4)
            
            print(f"💾 Dados brutos salvos em: '{caminho_completo}'")
            return caminho_completo
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return None
    
    def carregar_dados_arquivo(self, arquivo_json):
        """
        Carrega dados de um arquivo JSON
        """
        try:
            with open(arquivo_json, 'r', encoding='utf-8') as file:
                self.dados_brutos = json.load(file)
            print("✅ Arquivo carregado com sucesso!")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar arquivo: {e}")
            return False
    
    def processar_dados(self):
        """
        Processa os dados brutos e estrutura em formato organizado
        """
        if self.dados_brutos is None:
            print("❌ Nenhum dado para processar")
            return False
        
        try:
            feed_noticias = self.dados_brutos.get('feed', [])
            if not feed_noticias:
                print("⚠️ Nenhuma notícia encontrada para processar")
                return False
            
            print(f"📊 Processando {len(feed_noticias)} notícias...")
            
            # Estrutura principal
            self.dados_estruturados = {
                'metadados_gerais': self._extrair_metadados(feed_noticias),
                'feed_noticias': self._processar_noticias(feed_noticias),
                'analise_sentimentos': {},
                'estatisticas_detalhadas': {},
                'tickers_analisados': {}
            }
            
            # Análises e estatísticas
            if self.dados_estruturados['feed_noticias']:
                self._calcular_analises()
            
            print("✅ Dados processados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao processar dados: {e}")
            return False
    
    def _extrair_metadados(self, feed_noticias):
        """Extrai metadados gerais"""
        return {
            'total_noticias': len(feed_noticias),
            'items_retornados': int(self.dados_brutos.get('items', len(feed_noticias))),
            'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            'definicao_sentimento': self.dados_brutos.get('sentiment_score_definition', ''),
            'definicao_relevancia': self.dados_brutos.get('relevance_score_definition', ''),
            'periodo_cobertura': self._extrair_periodo_noticias(feed_noticias)
        }
    
    def _processar_noticias(self, feed_noticias):
        """Processa cada notícia individualmente"""
        noticias_processadas = []
        
        for noticia in feed_noticias:
            noticia_processada = {
                'titulo': noticia.get('title', ''),
                'resumo': noticia.get('summary', ''),
                'fonte_publicacao': noticia.get('source', ''),
                'dominio_fonte': noticia.get('source_domain', ''),
                'data_publicacao': self._formatar_data(noticia.get('time_published', '')),
                'url_noticia': noticia.get('url', ''),
                'autores': ', '.join(noticia.get('authors', [])),
                'imagem_capa': noticia.get('banner_image', ''),
                'categoria': noticia.get('category_within_source', ''),
                'score_sentimento': noticia.get('overall_sentiment_score', 0),
                'label_sentimento': noticia.get('overall_sentiment_label', 'Neutral'),
                'topicos': self._processar_topics(noticia.get('topics', [])),
                'sentimento_tickers': self._processar_ticker_sentiment(noticia.get('ticker_sentiment', []))
            }
            noticias_processadas.append(noticia_processada)
        
        return noticias_processadas
    
    def _calcular_analises(self):
        """Calcula análises e estatísticas dos dados processados"""
        df_noticias = pd.DataFrame(self.dados_estruturados['feed_noticias'])
        
        # Coletar todos os tickers
        todos_tickers = []
        for noticia in self.dados_estruturados['feed_noticias']:
            for ticker_str in noticia['sentimento_tickers']:
                # Extrair dados do ticker da string formatada
                parts = ticker_str.split(': ')
                if len(parts) >= 2:
                    ticker = parts[0]
                    # Extrair scores usando regex
                    score_match = re.search(r'score: ([-\d.]+)', ticker_str)
                    relevancia_match = re.search(r'relevância: ([-\d.]+)', ticker_str)
                    
                    if score_match and relevancia_match:
                        todos_tickers.append({
                            'ticker': ticker,
                            'score_relevancia': float(relevancia_match.group(1)),
                            'score_sentimento': float(score_match.group(1)),
                            'titulo_noticia': noticia['titulo'],
                            'data_publicacao': noticia['data_publicacao']
                        })
        
        df_tickers = pd.DataFrame(todos_tickers)
        
        # Análise de sentimentos
        self.dados_estruturados['analise_sentimentos'] = {
            'total_noticias_processadas': len(self.dados_estruturados['feed_noticias']),
            'distribuicao_sentimentos': df_noticias['label_sentimento'].value_counts().to_dict(),
            'score_sentimento_medio': round(df_noticias['score_sentimento'].mean(), 4),
            'quantidade_fontes': df_noticias['fonte_publicacao'].nunique(),
            'topicos_principais': self._obter_topics_mais_comuns()
        }
        
        # Estatísticas detalhadas
        self.dados_estruturados['estatisticas_detalhadas'] = {
            'publicacoes_por_fonte': df_noticias['fonte_publicacao'].value_counts().to_dict(),
            'publicacoes_por_data': df_noticias['data_publicacao'].value_counts().to_dict(),
            'evolucao_sentimento_diaria': self._calcular_evolucao_sentimento(df_noticias)
        }
        
        # Análise por ticker
        if not df_tickers.empty:
            stats_tickers = df_tickers.groupby('ticker').agg({
                'score_sentimento': ['mean', 'count'],
                'score_relevancia': 'mean'
            }).round(4)
            
            sentiment_por_ticker = {}
            for ticker in stats_tickers.index:
                sentiment_por_ticker[ticker] = {
                    'sentimento_medio': stats_tickers.loc[ticker, ('score_sentimento', 'mean')],
                    'total_mencoes': stats_tickers.loc[ticker, ('score_sentimento', 'count')],
                    'relevancia_media': stats_tickers.loc[ticker, ('score_relevancia', 'mean')]
                }
            
            self.dados_estruturados['tickers_analisados'] = {
                'total_tickers_unicos': df_tickers['ticker'].nunique(),
                'analise_sentimento_tickers': sentiment_por_ticker,
                'tickers_mais_citados': df_tickers['ticker'].value_counts().head(10).to_dict()
            }
    
    # ============ MÉTODOS AUXILIARES ============
    
    def _formatar_data(self, data_string):
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
    
    def _processar_topics(self, topics):
        """Processar lista de tópicos"""
        return [f"{topic.get('topic', '')} (relevância: {topic.get('relevance_score', '0')})" 
                for topic in topics]
    
    def _processar_ticker_sentiment(self, ticker_sentiment):
        """Processar sentimentos por ticker"""
        return [f"{ticker.get('ticker', '')}: {ticker.get('ticker_sentiment_label', 'Neutral')} " +
                f"(score: {ticker.get('ticker_sentiment_score', '0')}, " +
                f"relevância: {ticker.get('relevance_score', '0')})" 
                for ticker in ticker_sentiment]
    
    def _extrair_periodo_noticias(self, feed):
        """Extrair período de cobertura das notícias"""
        if not feed:
            return "N/A"
        
        datas = [self._formatar_data(noticia.get('time_published', '')) for noticia in feed]
        datas_validas = [d for d in datas if d]
        
        if datas_validas:
            return f"{min(datas_validas)} a {max(datas_validas)}"
        return "N/A"
    
    def _obter_topics_mais_comuns(self):
        """Encontrar tópicos mais frequentes"""
        all_topics = []
        for noticia in self.dados_estruturados['feed_noticias']:
            for topic in noticia.get('topicos', []):
                if isinstance(topic, str):
                    topic_name = topic.split(' (relevância:')[0].strip()
                    all_topics.append(topic_name)
        
        return dict(Counter(all_topics).most_common(10))
    
    def _calcular_evolucao_sentimento(self, df_noticias):
        """Calcular evolução do sentimento por dia"""
        try:
            if 'data_publicacao' not in df_noticias.columns or 'score_sentimento' not in df_noticias.columns:
                return {}
                
            df_noticias['data'] = pd.to_datetime(df_noticias['data_publicacao']).dt.date
            evolucao = df_noticias.groupby('data').agg({
                'score_sentimento': 'mean',
                'titulo': 'count'
            }).round(4)
            
            # Converter datas para string
            evolucao_dict = {}
            for data, row in evolucao.iterrows():
                data_str = data.strftime('%Y-%m-%d')
                evolucao_dict[data_str] = {
                    'sentimento_medio': float(row['score_sentimento']),
                    'total_noticias': int(row['titulo'])
                }
            
            return evolucao_dict
            
        except:
            return {}
    
    # ============ MÉTODOS DE EXPORTAÇÃO ============
    
    def exportar_resultados(self, prefixo="news_sentiments"):
        """Exporta os dados estruturados em JSON e CSV"""
        
        if self.dados_estruturados is None:
            print("❌ Nenhum dado estruturado para exportar!")
            return False
        
        try:
            # 1. Exportar JSON completo
            caminho_json = os.path.join(self.base_path, f"{prefixo}_estruturado.json")
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(self.dados_estruturados, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 JSON salvo: {caminho_json}")
            
            # 2. Exportar notícias em CSV
            if self.dados_estruturados['feed_noticias']:
                df_noticias = pd.DataFrame(self.dados_estruturados['feed_noticias'])
                caminho_csv = os.path.join(self.base_path, f"{prefixo}_noticias.csv")
                df_noticias.to_csv(caminho_csv, index=False, encoding='utf-8')
                print(f"💾 CSV salvo: {caminho_csv}")
                
            # 3. Exportar análise de tickers
            if self.dados_estruturados.get('tickers_analisados'):
                tickers_data = []
                for ticker, info in self.dados_estruturados['tickers_analisados']['analise_sentimento_tickers'].items():
                    tickers_data.append({
                        'ticker': ticker,
                        'sentimento_medio': info['sentimento_medio'],
                        'total_mencoes': info['total_mencoes'],
                        'relevancia_media': info['relevancia_media']
                    })
                
                df_tickers = pd.DataFrame(tickers_data)
                caminho_tickers = os.path.join(self.base_path, f"{prefixo}_tickers_analise.csv")
                df_tickers.to_csv(caminho_tickers, index=False, encoding='utf-8')
                print(f"💾 CSV de tickers salvo: {caminho_tickers}")
            
            print("✅ Exportação concluída com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na exportação: {e}")
            return False
    
    def mostrar_resumo(self):
        """Exibe um resumo dos dados processados"""
        if self.dados_estruturados is None:
            print("❌ Nenhum dado processado para mostrar")
            return
        
        metadados = self.dados_estruturados['metadados_gerais']
        analise = self.dados_estruturados['analise_sentimentos']
        
        print("\n" + "=" * 50)
        print("📊 RESUMO DOS DADOS PROCESSADOS")
        print("=" * 50)
        print(f"📰 Total de notícias: {metadados.get('total_noticias', 0)}")
        print(f"📈 Sentimento médio: {analise.get('score_sentimento_medio', 'N/A')}")
        print(f"🎯 Fontes únicas: {analise.get('quantidade_fontes', 0)}")
        
        # Distribuição de sentimentos
        distribuicao = analise.get('distribuicao_sentimentos', {})
        if distribuicao:
            print(f"\n📋 DISTRIBUIÇÃO DE SENTIMENTOS:")
            for sentimento, quantidade in distribuicao.items():
                print(f"   {sentimento}: {quantidade}")
        
        # Tickers analisados
        if self.dados_estruturados.get('tickers_analisados'):
            tickers_info = self.dados_estruturados['tickers_analisados']
            print(f"\n💹 TICKERS ANALISADOS:")
            print(f"   Total de tickers únicos: {tickers_info.get('total_tickers_unicos', 0)}")
            
            tickers_mais_citados = tickers_info.get('tickers_mais_citados', {})
            if tickers_mais_citados:
                print(f"\n🏆 TOP 5 TICKERS MAIS CITADOS:")
                print(len(list(tickers_mais_citados)))
                for ticker, count in list(tickers_mais_citados.items())[:5]:
                    print(f"   {ticker}: {count} menções")


# ============ EXECUÇÃO PRINCIPAL ============

if __name__ == "__main__":
    # Criar instância do processador
    processor = AlphaVantageNewsProcessor()
    
    print("🚀 INICIANDO PROCESSAMENTO DE NEWS & SENTIMENTS")
    print("=" * 60)
    
    # 1. Fazer requisição para a API
    if processor.fazer_requisicao_api():
        # 2. Salvar dados brutos
        processor.salvar_dados_brutos()
        
        # 3. Processar dados
        if processor.processar_dados():
            # 4. Mostrar resumo
            processor.mostrar_resumo()
            
            # 5. Exportar resultados
            print(f"\n📤 EXPORTANDO RESULTADOS...")
            processor.exportar_resultados()
            
            print("\n🎉 PROCESSAMENTO CONCLUÍDO!")
        else:
            print("❌ Falha no processamento dos dados!")
    else:
        print("❌ Falha na obtenção dos dados da API")