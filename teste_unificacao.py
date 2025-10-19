# -*- coding: utf-8 -*-
"""Sistema Unificado de Recomendação e Análise de Investimentos"""

import requests
import json
import pandas as pd
import numpy as np
from datetime import datetime
import os
import re
from collections import Counter

# ============ FUNÇÕES DE PROCESSAMENTO MANUAIS ============

def one_hot_encoding(df, columns):
    """Implementação manual de One-Hot Encoding"""
    result_df = df.copy()
    
    for col in columns:
        # Verificar se a coluna existe no DataFrame
        if col not in df.columns:
            continue
            
        # Obter valores únicos da coluna
        unique_values = df[col].unique()
        
        # Criar colunas para cada valor único
        for value in unique_values:
            new_col_name = f"{col}_{value}"
            result_df[new_col_name] = (df[col] == value).astype(int)
    
    # Remover colunas originais
    result_df = result_df.drop(columns=[col for col in columns if col in result_df.columns])
    return result_df

def min_max_scaler(data):
    """Implementação manual do MinMaxScaler"""
    data = np.array(data).reshape(-1, 1)
    min_val = np.min(data)
    max_val = np.max(data)
    
    if max_val == min_val:  # Evitar divisão por zero
        return np.zeros_like(data)
    
    scaled = (data - min_val) / (max_val - min_val)
    return scaled.flatten()

def cosine_similarity_manual(vec1, vec2):
    """Implementação manual da similaridade do cosseno"""
    vec1 = np.array(vec1)
    vec2 = np.array(vec2)
    
    dot_product = np.dot(vec1, vec2)
    norm_vec1 = np.linalg.norm(vec1)
    norm_vec2 = np.linalg.norm(vec2)
    
    if norm_vec1 == 0 or norm_vec2 == 0:
        return 0
    
    return dot_product / (norm_vec1 * norm_vec2)

# ============ CLASSES DO SISTEMA ============

class Carteira:
    """Classe para a carteira de investimentos do cliente"""
    def __init__(self, tickers, quantidades):
        self.tickers = tickers            # Ações da carteira
        self.quantidades = quantidades    # Quantidade de ações na carteira
    
    def __str__(self):
        return f"Carteira com {len(self.tickers)} ativos"
    
    def mostrar_carteira(self):
        """Exibe os ativos da carteira"""
        print("Ação - Quantidade:")
        for i in range(len(self.tickers)):
            print(f"  {self.tickers[i]} - {self.quantidades[i]}")

class Cliente:
    """Classe dos dados do cliente, incluindo a carteira de investimentos"""
    def __init__(self, id, nome, perfil, carteira):
        self.id = id                      # Identificação do cliente
        self.nome = nome                  # Nome do cliente
        self.perfil = perfil              # Perfil de investimento do cliente
        self.carteira = carteira          # Carteira de investimento do cliente
    
    def __str__(self):
        return f"Cliente {self.id}: {self.nome} ({self.perfil})"
    
    def mostrar_perfil(self):
        """Exibe o perfil completo do cliente"""
        print(f"\n{self.id}: {self.nome}")
        print(f"Perfil: {self.perfil}")
        self.carteira.mostrar_carteira()

class SistemaRecomendacao:
    """Sistema de recomendação baseado em similaridade"""
    
    def __init__(self, dados_nasdaq):
        self.dados_nasdaq = dados_nasdaq
        self._preprocessar_dados()
    
    def _preprocessar_dados(self):
        """Pré-processa os dados da NASDAQ de forma flexível"""
        print("📊 Pré-processando dados da NASDAQ...")
        
        # Criar uma cópia para não modificar o original
        self.dados_processados = self.dados_nasdaq.copy()
        
        # Mapeamento flexível de colunas
        mapeamento_colunas = {
            'Last Sale': 'LS', 
            'Net Change': 'NC', 
            '% Change': 'PC', 
            'Market Cap': 'MC', 
            'IPO Year': 'IPOY'
        }
        
        # Renomear apenas as colunas que existem
        colunas_para_renomear = {}
        for old_name, new_name in mapeamento_colunas.items():
            if old_name in self.dados_processados.columns:
                colunas_para_renomear[old_name] = new_name
        
        if colunas_para_renomear:
            self.dados_processados.rename(columns=colunas_para_renomear, inplace=True)
        
        # Colunas para preencher valores nulos
        colunas_para_preencher = ['Industry', 'Sector', 'Country', 'PC', 'MC']
        for col in colunas_para_preencher:
            if col in self.dados_processados.columns:
                if col in ['Industry', 'Sector', 'Country']:
                    self.dados_processados[col] = self.dados_processados[col].fillna('-')
                else:
                    self.dados_processados[col] = self.dados_processados[col].fillna(0)
        
        # Preencher IPOY se existir
        if 'IPOY' in self.dados_processados.columns:
            self.dados_processados['IPOY'] = self.dados_processados['IPOY'].fillna(0)
        
        # Converter formatos de forma segura
        if 'LS' in self.dados_processados.columns:
            self.dados_processados['LS'] = self.dados_processados['LS'].astype(str).str.replace('$', '', regex=False)
            self.dados_processados['LS'] = pd.to_numeric(self.dados_processados['LS'], errors='coerce').fillna(0)
        
        if 'PC' in self.dados_processados.columns:
            self.dados_processados['PC'] = self.dados_processados['PC'].astype(str).str.replace('%', '', regex=False)
            self.dados_processados['PC'] = pd.to_numeric(self.dados_processados['PC'], errors='coerce').fillna(0)
        
        print(f"✅ Dados pré-processados: {len(self.dados_processados)} ativos")
        print(f"📋 Colunas disponíveis: {list(self.dados_processados.columns)}")
    
    def _criar_features(self, df):
        """Cria features para o algoritmo de recomendação de forma flexível"""
        # Colunas categóricas possíveis
        possiveis_cat_cols = ['Country', 'Sector', 'Industry']
        cat_cols = [col for col in possiveis_cat_cols if col in df.columns]
        
        # Colunas numéricas possíveis
        possiveis_num_cols = ['PC', 'LS', 'MC']
        num_cols = [col for col in possiveis_num_cols if col in df.columns]
        
        if not cat_cols and not num_cols:
            print("⚠️ Nenhuma coluna disponível para criar features")
            return pd.DataFrame()
        
        # Garantir que temos a coluna Symbol
        if 'Symbol' not in df.columns:
            print("❌ Coluna 'Symbol' não encontrada")
            return pd.DataFrame()
        
        # One-Hot Encoding manual para categóricas
        if cat_cols:
            df_encoded = one_hot_encoding(df[['Symbol'] + cat_cols + num_cols], cat_cols)
        else:
            df_encoded = df[['Symbol'] + num_cols].copy()
        
        # Normalizar colunas numéricas
        for num_col in num_cols:
            if num_col in df_encoded.columns:
                new_col_name = f"{num_col}_normalized"
                df_encoded[new_col_name] = min_max_scaler(df_encoded[num_col].values)
                df_encoded = df_encoded.drop(num_col, axis=1)
        
        return df_encoded
    
    def recomendar_acoes(self, cliente, top_n=5):
        """
        Recomenda ações similares baseado na carteira do cliente
        """
        print(f"\n🎯 Gerando recomendações para {cliente.nome}...")
        
        symbols_entrada = cliente.carteira.tickers
        pesos = cliente.carteira.quantidades
        
        # Verificar se temos a coluna PC para filtrar performance positiva
        if 'PC' in self.dados_processados.columns:
            df_filtered = self.dados_processados[self.dados_processados['PC'] > 0].copy()
        else:
            # Se não temos PC, usar todos os dados
            df_filtered = self.dados_processados.copy()
            print("⚠️ Usando todos os dados (coluna PC não disponível)")
        
        if df_filtered.empty:
            print("⚠️ Nenhuma ação disponível para recomendação")
            return []
        
        # Criar features para todos os dados
        df_features = self._criar_features(df_filtered)
        
        if df_features.empty:
            print("❌ Não foi possível criar features para recomendação")
            return []
        
        # Filtrar ações da carteira do cliente
        df_input = df_features[df_features['Symbol'].isin(symbols_entrada)].copy()
        
        if df_input.empty:
            print("⚠️ Nenhum símbolo da carteira encontrado nos dados")
            # Mostrar símbolos disponíveis para debug
            simbolos_disponiveis = df_features['Symbol'].head(10).tolist()
            print(f"📋 Primeiros símbolos disponíveis: {simbolos_disponiveis}")
            return []
        
        # Remover coluna Symbol para cálculo de similaridade
        symbols_all = df_features['Symbol'].values
        features_all = df_features.drop('Symbol', axis=1).values
        
        symbols_input = df_input['Symbol'].values
        features_input = df_input.drop('Symbol', axis=1).values
        
        # Calcular vetor médio ponderado da carteira
        vetor_entrada = np.zeros(features_input.shape[1])
        total_peso = 0
        
        for i, symbol in enumerate(symbols_input):
            if symbol in symbols_entrada:
                peso_idx = symbols_entrada.index(symbol)
                peso = pesos[peso_idx]
                vetor_entrada += features_input[i] * peso
                total_peso += peso
        
        if total_peso > 0:
            vetor_entrada /= total_peso
        
        # Calcular similaridade com todas as ações
        similaridades = []
        for i in range(len(features_all)):
            sim = cosine_similarity_manual(vetor_entrada, features_all[i])
            similaridades.append(sim)
        
        # Criar DataFrame de resultados
        df_resultado = pd.DataFrame({
            'Symbol': symbols_all,
            'score': similaridades
        })
        
        # Excluir ações que já estão na carteira
        df_resultado = df_resultado[~df_resultado['Symbol'].isin(symbols_entrada)]
        
        if df_resultado.empty:
            print("⚠️ Nenhuma recomendação disponível após filtrar carteira atual")
            return []
        
        # Selecionar top_n símbolos
        top_symbols = df_resultado.nlargest(top_n, 'score')['Symbol'].tolist()
        
        print(f"✅ {len(top_symbols)} recomendações geradas: {top_symbols}")
        return top_symbols

class AlphaVantageProcessor:
    """
    Classe para processar dados de ações da Alpha Vantage API
    """
    
    def __init__(self, api_key="HE6JJP6N87RFIOD9"):
        self.api_key = api_key
        self.dados_brutos_stock = None
        self.dados_estruturados_stock = None
        self.base_path = "./dados_investimentos"
        
        # Criar diretório se não existir
        os.makedirs(self.base_path, exist_ok=True)
    
    def buscar_dados_acao(self, simbolo="AAPL"):
        """Busca dados de série temporal diária para uma ação"""
        url = f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol={simbolo}&apikey={self.api_key}'
        
        try:
            print(f"🌐 Buscando dados da ação {simbolo}...")
            r = requests.get(url)
            r.raise_for_status()
            self.dados_brutos_stock = r.json()
            
            # Verificar erros da API
            if 'Information' in self.dados_brutos_stock:
                print(f"⚠️ Limite da API: {self.dados_brutos_stock['Information']}")
                return False
            
            if 'Time Series (Daily)' not in self.dados_brutos_stock:
                print("❌ Nenhum dado de série temporal encontrado")
                return False
            
            print(f"✅ Dados da ação {simbolo} carregados com sucesso!")
            return True
            
        except requests.exceptions.RequestException as e:
            print(f"❌ Erro na requisição: {e}")
            return False
    
    def processar_dados_acao(self):
        """Processa os dados brutos da ação e estrutura em formato organizado"""
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
            for col in ['open', 'high', 'low', 'close']:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            df['volume'] = pd.to_numeric(df['volume'], errors='coerce').fillna(0).astype(int)
            
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
        """Calcula análise técnica básica dos dados da ação"""
        try:
            if df.empty or len(df) < 2:
                return {}
            
            # Estatísticas básicas
            analise = {
                'preco_atual': df.iloc[0]['close'],
                'variacao_dia_anterior': round(((df.iloc[0]['close'] - df.iloc[1]['close']) / df.iloc[1]['close']) * 100, 2),
            }
            
            # Calcular médias se tiver dados suficientes
            if len(df) >= 7:
                analise['media_7_dias'] = round(df['close'].head(7).mean(), 2)
            if len(df) >= 30:
                analise['media_30_dias'] = round(df['close'].head(30).mean(), 2)
                analise['maximo_30_dias'] = round(df['high'].head(30).max(), 2)
                analise['minimo_30_dias'] = round(df['low'].head(30).min(), 2)
                analise['volume_medio_30_dias'] = int(df['volume'].head(30).mean())
            
            # Determinar tendência
            if 'media_7_dias' in analise and 'media_30_dias' in analise:
                preco_atual = df.iloc[0]['close']
                media_7 = analise['media_7_dias']
                media_30 = analise['media_30_dias']
                
                if preco_atual > media_7 and preco_atual > media_30:
                    analise['tendencia'] = 'Alta'
                elif preco_atual < media_7 and preco_atual < media_30:
                    analise['tendencia'] = 'Baixa'
                else:
                    analise['tendencia'] = 'Lateral'
            else:
                analise['tendencia'] = 'Indeterminada'
            
            return analise
            
        except Exception as e:
            print(f"⚠️ Erro na análise técnica: {e}")
            return {}
    
    def mostrar_resumo_acao(self, simbolo):
        """Exibe um resumo dos dados da ação processados"""
        if self.dados_estruturados_stock is None:
            print("❌ Nenhum dado de ação processado para mostrar")
            return
        
        metadados = self.dados_estruturados_stock['metadados']
        analise = self.dados_estruturados_stock['analise_tecnica']
        
        print(f"\n📈 RESUMO DA AÇÃO {simbolo}")
        print("=" * 50)
        print(f"🏷️  Símbolo: {metadados.get('simbolo', 'N/A')}")
        print(f"📅 Período: {metadados.get('periodo', 'N/A')}")
        print(f"📊 Total de dias: {metadados.get('total_dias', 0)}")
        
        if analise:
            print(f"\n💹 ANÁLISE TÉCNICA:")
            print(f"   Preço atual: ${analise.get('preco_atual', 'N/A'):.2f}")
            print(f"   Variação vs dia anterior: {analise.get('variacao_dia_anterior', 'N/A')}%")
            
            if 'media_7_dias' in analise:
                print(f"   Média 7 dias: ${analise.get('media_7_dias', 'N/A'):.2f}")
            if 'media_30_dias' in analise:
                print(f"   Média 30 dias: ${analise.get('media_30_dias', 'N/A'):.2f}")
            
            print(f"   Tendência: {analise.get('tendencia', 'N/A')}")
            
            if 'volume_medio_30_dias' in analise:
                print(f"   Volume médio (30 dias): {analise.get('volume_medio_30_dias', 0):,}")
    
    def analisar_recomendacoes(self, recomendacoes):
        """Analisa cada ação recomendada"""
        print(f"\n🔍 ANALISANDO {len(recomendacoes)} AÇÕES RECOMENDADAS...")
        
        analises = {}
        for simbolo in recomendacoes:
            print(f"\n📊 Analisando {simbolo}...")
            if self.buscar_dados_acao(simbolo):
                if self.processar_dados_acao():
                    analises[simbolo] = self.dados_estruturados_stock['analise_tecnica']
                    self.mostrar_resumo_acao(simbolo)
                else:
                    print(f"❌ Falha no processamento de {simbolo}")
                    analises[simbolo] = {'erro': 'Falha no processamento'}
            else:
                print(f"⚠️ Não foi possível buscar dados para {simbolo}")
                analises[simbolo] = {'erro': 'Dados não disponíveis'}
        
        return analises

# ============ SISTEMA PRINCIPAL ============

class SistemaInvestimentos:
    """Sistema principal unificado de recomendações e análise"""
    
    def __init__(self, caminho_dados_nasdaq=None):
        self.clientes = []
        self.sistema_recomendacao = None
        self.processor = AlphaVantageProcessor()
        
        # Carregar dados da NASDAQ ou usar exemplo
        if caminho_dados_nasdaq and os.path.exists(caminho_dados_nasdaq):
            print(f"📂 Carregando dados da NASDAQ de {caminho_dados_nasdaq}...")
            try:
                self.dados_nasdaq = pd.read_csv(caminho_dados_nasdaq)
                self.sistema_recomendacao = SistemaRecomendacao(self.dados_nasdaq)
                print("✅ Dados da NASDAQ carregados com sucesso!")
            except Exception as e:
                print(f"❌ Erro ao carregar dados da NASDAQ: {e}")
                self._criar_dados_exemplo()
        else:
            print("📋 Usando dados de exemplo para demonstração...")
            self._criar_dados_exemplo()
    
    def _criar_dados_exemplo(self):
        """Cria dados de exemplo para demonstração"""
        dados_exemplo = {
            'Symbol': ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'TSLA', 'JNJ', 'JPM', 'V', 'PG'],
            'Name': ['Apple Inc', 'Microsoft Corp', 'Alphabet Inc', 'Amazon.com Inc', 
                    'NVIDIA Corp', 'Tesla Inc', 'Johnson & Johnson', 'JPMorgan Chase & Co',
                    'Visa Inc', 'Procter & Gamble Co'],
            'Country': ['USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA', 'USA'],
            'Sector': ['Technology', 'Technology', 'Technology', 'Consumer Cyclical',
                      'Technology', 'Consumer Cyclical', 'Healthcare', 'Financial Services',
                      'Financial Services', 'Consumer Defensive'],
            'Industry': ['Consumer Electronics', 'Software—Infrastructure', 'Internet Content & Information',
                        'Internet Retail', 'Semiconductors', 'Auto Manufacturers', 'Drug Manufacturers—General',
                        'Banks—Diversified', 'Credit Services', 'Household & Personal Products'],
            'PC': [2.5, 1.8, 3.2, 1.2, 5.7, 3.1, 0.8, 1.2, 2.1, 0.5],  # Todos positivos para demo
            'LS': [150.0, 330.0, 2800.0, 3400.0, 850.0, 200.0, 160.0, 170.0, 230.0, 150.0]
        }
        self.dados_nasdaq = pd.DataFrame(dados_exemplo)
        self.sistema_recomendacao = SistemaRecomendacao(self.dados_nasdaq)
        print("✅ Dados de exemplo criados com sucesso!")
    
    def cadastrar_cliente(self, id, nome, perfil, tickers, quantidades):
        """Cadastra um novo cliente no sistema"""
        carteira = Carteira(tickers, quantidades)
        cliente = Cliente(id, nome, perfil, carteira)
        self.clientes.append(cliente)
        print(f"✅ Cliente {nome} cadastrado com sucesso!")
        return cliente
    
    def mostrar_clientes(self):
        """Exibe todos os clientes cadastrados"""
        print(f"\n👥 CLIENTES CADASTRADOS ({len(self.clientes)})")
        print("=" * 50)
        for cliente in self.clientes:
            cliente.mostrar_perfil()
    
    def gerar_recomendacoes(self, cliente_id, top_n=5):
        """Gera recomendações para um cliente específico"""
        cliente = next((c for c in self.clientes if c.id == cliente_id), None)
        if not cliente:
            print(f"❌ Cliente {cliente_id} não encontrado")
            return None
        
        if not self.sistema_recomendacao:
            print("❌ Sistema de recomendação não disponível")
            return None
        
        # Gerar recomendações
        recomendacoes = self.sistema_recomendacao.recomendar_acoes(cliente, top_n)
        
        return {
            'cliente': cliente,
            'recomendacoes': recomendacoes
        }
    
    def executar_demo(self):
        """Executa uma demonstração do sistema"""
        print("🚀 INICIANDO DEMONSTRAÇÃO DO SISTEMA")
        print("=" * 60)
        
        # Criar clientes de teste
        print("\n1. 👥 CRIANDO CLIENTES DE TESTE")
        print("-" * 30)
        
        self.cadastrar_cliente(
            '0001', 'Luis Felipe Vamo', 'moderado',
            ['AAPL', 'MSFT', 'JNJ'], [50, 30, 15]
        )
        
        self.cadastrar_cliente(
            '0002', 'Gustavo Cuca', 'arrojado', 
            ['NVDA', 'GOOGL', 'TSLA'], [15, 35, 20]
        )
        
        self.mostrar_clientes()
        
        # Gerar recomendações
        if self.sistema_recomendacao:
            print("\n2. 🎯 GERANDO RECOMENDAÇÕES")
            print("-" * 30)
            
            for cliente in self.clientes:
                print(f"\n💼 Gerando recomendações para {cliente.nome}...")
                resultado = self.gerar_recomendacoes(cliente.id, top_n=3)
                
                if resultado and resultado['recomendacoes']:
                    print(f"\n✅ RECOMENDAÇÕES PARA {cliente.nome}:")
                    for i, simbolo in enumerate(resultado['recomendacoes'], 1):
                        print(f"   {i}. {simbolo}")
                    
                    # Tentar analisar recomendações com API
                    print(f"\n🔍 Tentando obter análise detalhada das recomendações...")
                    self.processor.analisar_recomendacoes(resultado['recomendacoes'])
                else:
                    print(f"❌ Não foi possível gerar recomendações para {cliente.nome}")
        
        print("\n🎉 DEMONSTRAÇÃO CONCLUÍDA!")

# ============ EXECUÇÃO PRINCIPAL ============

if __name__ == "__main__":
    # Criar sistema - funciona mesmo sem arquivo da NASDAQ
    sistema = SistemaInvestimentos()  # Sem caminho específico - usa dados de exemplo
    
    # Executar demonstração
    sistema.executar_demo()