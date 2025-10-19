import requests
import json
import pandas as pd
from datetime import datetime
import os
import re
from collections import Counter

class AlphaVantageProcessor:
    """
    Classe unificada para processar dados de News & Sentiments e dados de ações da Alpha Vantage API
    """
    
    def __init__(self, api_key="HE6JJP6N87RFIOD9"):
        self.api_key = api_key
        self.dados_brutos_news = None
        self.dados_brutos_stock = None
        self.dados_estruturados_news = None
        self.dados_estruturados_stock = None
        self.base_path = r'C:\Users\Acer\Downloads'
    
    # ============ MÉTODOS PARA DADOS DE AÇÃO ============
    
    def buscar_dados_acao(self, simbolo="ERJ"):
        """
        Busca dados de série temporal diária para uma ação
        """
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={simbolo}&apikey={self.api_key}'
        
        try:
            print(f"🌐 Buscando dados da ação {simbolo}...")
            r = requests.get(url)
            r.raise_for_status()
            self.dados_brutos_stock = r.json()
            
            # Verificar erros da API
            if 'Information' in self.dados_brutos_stock:
                print(f"❌ ERRO DA API: {self.dados_brutos_stock['Information']}")
                return False
            
            if 'Time Series (Daily)' not in self.dados_brutos_stock:
                print("❌ Nenhum dado de série temporal encontrado")
                return False
            
            print(f"✅ Dados da ação {simbolo} carregados com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
    
    def salvar_dados_acao(self, nome_arquivo='dados_acao.json'):
        """
        Salva os dados brutos da ação em arquivo JSON
        """
        if self.dados_brutos_stock is None:
            print("❌ Nenhum dado de ação para salvar")
            return None
        
        try:
            caminho_completo = os.path.join(self.base_path, nome_arquivo)
            os.makedirs(self.base_path, exist_ok=True)
            
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                json.dump(self.dados_brutos_stock, f, ensure_ascii=False, indent=4)
            
            print(f"💾 Dados da ação salvos em: '{caminho_completo}'")
            return caminho_completo
            
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return None
    
    def processar_dados_acao(self):
        """
        Processa os dados brutos da ação e estrutura em formato organizado
        """
        if self.dados_brutos_stock is None:
            print("❌ Nenhum dado de ação para processar")
            return False
        
        try:
            time_series = self.dados_brutos_stock.get("Time Series (Daily)", {})
            if not time_series:
                print("⚠️ Nenhum dado de série temporal encontrado")
                return False
            
            print(f"📊 Processando {len(time_series)} dias de dados da ação...")
            
            # Converter para DataFrame
            df = pd.DataFrame.from_dict(time_series, orient='index')
            
            # Limpar e renomear colunas
            df.columns = [col.split('. ')[1] for col in df.columns]
            
            # Converter tipos de dados
            df = df.astype({
                'open': float, 'high': float, 'low': float, 'close': float, 'volume': int
            })
            
            # Ordenar por data (mais recente primeiro)
            df.index = pd.to_datetime(df.index)
            df = df.sort_index(ascending=False)
            
            # Estruturar dados
            self.dados_estruturados_stock = {
                'metadados': {
                    'simbolo': self.dados_brutos_stock["Meta Data"]["2. Symbol"],
                    'ultima_atualizacao': self.dados_brutos_stock["Meta Data"]["3. Last Refreshed"],
                    'timezone': self.dados_brutos_stock["Meta Data"]["5. Time Zone"],
                    'periodo': f"{df.index.min().strftime('%d/%m/%Y')} a {df.index.max().strftime('%d/%m/%Y')}",
                    'total_dias': len(df),
                    'data_processamento': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                },
                'dados_diarios': df,
                'analise_tecnica': self._calcular_analise_tecnica(df)
            }
            
            print("✅ Dados da ação processados com sucesso!")
            return True
            
        except Exception as e:
            print(f"❌ Erro ao processar dados da ação: {e}")
            return False
    
    def _calcular_analise_tecnica(self, df):
        """
        Calcula análise técnica básica dos dados da ação
        """
        try:
            if df.empty:
                return {}
            
            # Estatísticas básicas
            analise = {
                'preco_atual': df.iloc[0]['close'],
                'variacao_dia_anterior': round(((df.iloc[0]['close'] - df.iloc[1]['close']) / df.iloc[1]['close']) * 100, 2),
                'media_7_dias': round(df['close'].head(7).mean(), 2),
                'media_30_dias': round(df['close'].head(30).mean(), 2),
                'maximo_30_dias': round(df['high'].head(30).max(), 2),
                'minimo_30_dias': round(df['low'].head(30).min(), 2),
                'volume_medio_30_dias': int(df['volume'].head(30).mean())
            }
            
            # Tendência
            preco_atual = df.iloc[0]['close']
            media_7 = analise['media_7_dias']
            media_30 = analise['media_30_dias']
            
            if preco_atual > media_7 and preco_atual > media_30:
                analise['tendencia'] = 'Alta'
            elif preco_atual < media_7 and preco_atual < media_30:
                analise['tendencia'] = 'Baixa'
            else:
                analise['tendencia'] = 'Lateral'
            
            return analise
            
        except Exception as e:
            print(f"⚠️ Erro na análise técnica: {e}")
            return {}
    
    def exportar_dados_acao(self, prefixo="dados_acao"):
        """
        Exporta os dados estruturados da ação
        """
        if self.dados_estruturados_stock is None:
            print("❌ Nenhum dado de ação para exportar!")
            return False
        
        try:
            # 1. Exportar JSON completo
            caminho_json = os.path.join(self.base_path, f"{prefixo}_estruturado.json")
            with open(caminho_json, 'w', encoding='utf-8') as f:
                json.dump(self.dados_estruturados_stock, f, indent=2, ensure_ascii=False, default=str)
            print(f"💾 JSON da ação salvo: {caminho_json}")
            
            # 2. Exportar dados diários em CSV
            if not self.dados_estruturados_stock['dados_diarios'].empty:
                df = self.dados_estruturados_stock['dados_diarios']
                caminho_csv = os.path.join(self.base_path, f"{prefixo}_diarios.csv")
                df.to_csv(caminho_csv, encoding='utf-8')
                print(f"💾 CSV da ação salvo: {caminho_csv}")
            
            print("✅ Exportação dos dados da ação concluída!")
            return True
            
        except Exception as e:
            print(f"❌ Erro na exportação da ação: {e}")
            return False
    
    def mostrar_resumo_acao(self):
        """
        Exibe um resumo dos dados da ação processados
        """
        if self.dados_estruturados_stock is None:
            print("❌ Nenhum dado de ação processado para mostrar")
            return
        
        metadados = self.dados_estruturados_stock['metadados']
        analise = self.dados_estruturados_stock['analise_tecnica']
        
        print("\n" + "=" * 50)
        print("📈 RESUMO DOS DADOS DA AÇÃO")
        print("=" * 50)
        print(f"🏷️  Símbolo: {metadados.get('simbolo', 'N/A')}")
        print(f"📅 Período: {metadados.get('periodo', 'N/A')}")
        print(f"📊 Total de dias: {metadados.get('total_dias', 0)}")
        
        if analise:
            print(f"\n💹 ANÁLISE TÉCNICA:")
            print(f"   Preço atual: ${analise.get('preco_atual', 'N/A')}")
            print(f"   Variação vs dia anterior: {analise.get('variacao_dia_anterior', 'N/A')}%")
            print(f"   Média 7 dias: ${analise.get('media_7_dias', 'N/A')}")
            print(f"   Tendência: {analise.get('tendencia', 'N/A')}")
            print(f"   Volume médio (30 dias): {analise.get('volume_medio_30_dias', 0):,}")
    
    # ============ MÉTODOS PARA NEWS (mantidos da versão anterior) ============
    
    def fazer_requisicao_news(self, tickers="AAPL"):
        """Faz requisição para a API de News"""
        url = f'https://www.alphavantage.co/query?function=NEWS_SENTIMENT&tickers={tickers}&apikey={self.api_key}'
        
        try:
            print("🌐 Fazendo requisição para a API de News...")
            r = requests.get(url)
            r.raise_for_status()
            self.dados_brutos_news = r.json()
            
            if 'Information' in self.dados_brutos_news:
                print(f"❌ ERRO DA API: {self.dados_brutos_news['Information']}")
                return False
            
            if 'feed' not in self.dados_brutos_news:
                print("❌ Nenhum dado de 'feed' encontrado")
                return False
            
            print(f"✅ API retornou {len(self.dados_brutos_news.get('feed', []))} notícias")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
    
    def salvar_dados_news(self, nome_arquivo='news_sentiments.json'):
        """Salva os dados brutos das news"""
        if self.dados_brutos_news is None:
            print("❌ Nenhum dado de news para salvar")
            return None
        
        try:
            caminho_completo = os.path.join(self.base_path, nome_arquivo)
            with open(caminho_completo, 'w', encoding='utf-8') as f:
                json.dump(self.dados_brutos_news, f, ensure_ascii=False, indent=4)
            print(f"💾 Dados de news salvos em: '{caminho_completo}'")
            return caminho_completo
        except Exception as e:
            print(f"❌ Erro ao salvar arquivo: {e}")
            return None
    
    def processar_dados_news(self):
        """Processa os dados de news (mantido da versão anterior)"""
        # ... (manter todos os métodos de news da versão anterior)
        # Para economizar espaço, mantive apenas a assinatura
        pass
    
    def exportar_dados_news(self, prefixo="news_sentiments"):
        """Exporta os dados de news (mantido da versão anterior)"""
        # ... (manter todos os métodos de news da versão anterior)
        pass
    
    def mostrar_resumo_news(self):
        """Exibe resumo das news (mantido da versão anterior)"""
        # ... (manter todos os métodos de news da versão anterior)
        pass


# ============ EXECUÇÃO PRINCIPAL UNIFICADA ============

if __name__ == "__main__":
    # Criar instância do processador
    processor = AlphaVantageProcessor()
    
    print("🚀 INICIANDO PROCESSAMENTO UNIFICADO ALPHA VANTAGE")
    print("=" * 60)
    
    # OPÇÃO 1: Processar dados de ação
    print("\n1. 📈 PROCESSANDO DADOS DE AÇÃO")
    print("-" * 30)
    
    simbolo_acao = "ERJ"  # Pode alterar para qualquer símbolo
    if processor.buscar_dados_acao(simbolo_acao):
        processor.salvar_dados_acao()
        if processor.processar_dados_acao():
            processor.mostrar_resumo_acao()
            processor.exportar_dados_acao()
        else:
            print("❌ Falha no processamento dos dados da ação!")
    else:
        print(f"❌ Falha na obtenção dos dados da ação {simbolo_acao}")
    
    # OPÇÃO 2: Processar dados de news
    print("\n2. 📰 PROCESSANDO DADOS DE NEWS")
    print("-" * 30)
    
    if processor.fazer_requisicao_news("AAPL"):
        processor.salvar_dados_news()
        if processor.processar_dados_news():
            processor.mostrar_resumo_news()
            processor.exportar_dados_news()
        else:
            print("❌ Falha no processamento dos dados de news!")
    else:
        print("❌ Falha na obtenção dos dados de news")
    
    print("\n🎉 PROCESSAMENTO UNIFICADO CONCLUÍDO!")