import psycopg2, glob, os
import pandas as pd
from sqlalchemy import create_engine
from psycopg2 import connect, extras
from psycopg2.extras import execute_batch
from config import DB_CONFIG

# Database connection parameters
DB_NAME = DB_CONFIG['dbname']
DB_USER = DB_CONFIG['user']
DB_PASSWORD = DB_CONFIG['password']
DB_HOST = DB_CONFIG['host']
DB_PORT = DB_CONFIG['port']


# Função para converter campos de data
def parse_date(x):
    x = x.strip()
    if not x:
        return None
    return pd.to_datetime(x, format='%Y%m%d', errors='coerce')

# Função para converter campos numéricos com decimais implícitos
def parse_numeric(x):
    x = x.strip()
    if not x:
        return None
    return float(x) / 100  # Dividir por 100 para considerar as casas decimais

# Função para converter campos inteiros
def parse_int(x):
    x = x.strip()
    if not x:
        return None
    return int(x)

# Definição das especificações das colunas (posições inicial e final)
colspecs = [
    (0, 2),     # tipo_registro
    (2, 10),    # data_pregao
    (10, 12),   # codigo_bdi
    (12, 24),   # codigo_negociacao
    (24, 27),   # tipo_mercado
    (27, 39),   # nome_resumido_empresa
    (39, 49),   # especificacao_papel
    (49, 52),   # prazo_dias_mercado_termo
    (52, 56),   # moeda_referencia
    (56, 69),   # preco_abertura
    (69, 82),   # preco_maximo
    (82, 95),   # preco_minimo
    (95, 108),  # preco_medio
    (108, 121), # preco_ultimo_negocio
    (121, 134), # melhor_oferta_compra
    (134, 147), # melhor_oferta_venda
    (147, 152), # negocios_efetuados
    (152, 170), # quantidade_total_titulos
    (170, 188), # volume_total_titulos
    (188, 201), # preco_exercicio_opcoes
    (201, 202), # indicador_correcao_preco
    (202, 210), # data_vencimento
    (210, 217), # fator_cotacao
    (217, 230), # preco_exercicio_pontos
    (230, 242), # codigo_isin
    (242, 245)  # numero_distribuicao
]

# Nomes das colunas correspondentes às posições acima
names = [
    "tipo_registro",
    "data_pregao",
    "codigo_bdi",
    "codigo_negociacao",
    "tipo_mercado",
    "nome_resumido_empresa",
    "especificacao_papel",
    "prazo_dias_mercado_termo",
    "moeda_referencia",
    "preco_abertura",
    "preco_maximo",
    "preco_minimo",
    "preco_medio",
    "preco_ultimo_negocio",
    "melhor_oferta_compra",
    "melhor_oferta_venda",
    "negocios_efetuados",
    "quantidade_total_titulos",
    "volume_total_titulos",
    "preco_exercicio_opcoes",
    "indicador_correcao_preco",
    "data_vencimento",
    "fator_cotacao",
    "preco_exercicio_pontos",
    "codigo_isin",
    "numero_distribuicao"
]

# Dicionário de conversores para tipos específicos
converters = {
    'data_pregao': parse_date,
    'data_vencimento': parse_date,
    'prazo_dias_mercado_termo': parse_int,
    'negocios_efetuados': parse_int,
    'quantidade_total_titulos': lambda x: int(x.strip()) if x.strip() else None,
    'indicador_correcao_preco': parse_int,
    'volume_total_titulos': parse_numeric,
    'preco_abertura': parse_numeric,
    'preco_maximo': parse_numeric,
    'preco_minimo': parse_numeric,
    'preco_medio': parse_numeric,
    'preco_ultimo_negocio': parse_numeric,
    'melhor_oferta_compra': parse_numeric,
    'melhor_oferta_venda': parse_numeric,
    'preco_exercicio_opcoes': parse_numeric,
    'preco_exercicio_pontos': parse_numeric
}

# Lista de colunas de texto para limpeza de espaços
string_columns = [
    'tipo_registro',
    'codigo_bdi',
    'codigo_negociacao',
    'tipo_mercado',
    'nome_resumido_empresa',
    'especificacao_papel',
    'moeda_referencia',
    'fator_cotacao',
    'codigo_isin',
    'numero_distribuicao'
]

def process_file(filepath, engine):
    print(f'Processando o arquivo {filepath}...')
    # Ler o arquivo com pandas
    with open(filepath, 'r', encoding='latin1') as file:
        # Contar o número total de linhas do arquivo
        total_lines = sum(1 for line in file)
    
    df = pd.read_fwf(
        filepath,
        colspecs=colspecs,
        names=names,
        converters=converters,
        skiprows=1,       # Pular a primeira linha
        skipfooter=1,     # Pular a última linha
        engine='python',   # Usar o engine python para evitar warnings
        encoding='latin1'
    )
    
    # Limpar espaços em branco nas colunas de texto
    for col in string_columns:
        df[col] = df[col].astype(str).str.strip()
    
    # Inserir os dados no banco de dados
    try:
        df.to_sql('cotacoes_historicas', engine, if_exists='append', index=False)
        print(f'Dados do arquivo {filepath} inseridos com sucesso.')
    except Exception as e:
        print(f'Erro ao inserir dados do arquivo {filepath}: {e}')


def create_database(conn):
    try:
        cur = conn.cursor()       
        # Check if the database exists (optional)
        query = f"SELECT datname FROM pg_database WHERE datname = '{DB_CONFIG['dbname']}'"
        cur.execute(query)
        result = cur.fetchone()
        
        if not result:
            print(f"Database '{DB_CONFIG['dbname']}' does not exist. Creating it...")
            
            # Execute the command to create the new database
            cur.execute(f"CREATE DATABASE {DB_CONFIG['dbname']}")
            print(f"Database '{DB_CONFIG['dbname']}' created successfully.")
        else:
            print(f"Database '{DB_CONFIG['dbname']}' already exists.")
        
        # Close the cursor and connection
        cur.close()
        conn.commit()  # Commit if you executed any DDL commands
        
    except Exception as e:
        print(f"Error creating database: {e}")
        if conn is not None:
            conn.rollback()  # Rollback on error


def check_table_exists(conn):
    try:
        cursor = conn.cursor()
        
        cursor.execute("SELECT pg_tables.tablename FROM pg_catalog.pg_tables WHERE pg_tables.tablename = 'cotacoes_historicas';")
        
        if cursor.fetchone() is not None:
            return True
        else:
            return False
            
    except psycopg2.Error as e:
        print(f"Erro ao consultar o banco de dados: {e}")


def create_table(conn):
    try:
        with open('src/queries/create_table.sql', 'r') as f:
            query = f.read()
            cur  = conn.cursor()
            cur.execute(query)
            conn.commit()
            cur.close()
    except Exception as e:
        print(f"Error creating table: {e}")



# def main():
#     # Connect to PostgreSQL database
#     conn = psycopg2.connect(
#         dbname=DB_NAME,
#         user=DB_USER,
#         password=DB_PASSWORD,
#         host=DB_HOST,
#         port=DB_PORT
#     )
#     try:
#         create_database(conn)
#         if (not check_table_exists(conn)):
#             create_table(conn)
#         # Create cursor with execute_batch support
#         cur = conn.cursor()
        
#         # Define the field format positions from the text layout
#         field_positions = {
#             'tipo_registro': (0, 2),
#             'data_pregao': (3, 14),
#             'codigo_bdi': (15, 17),
#             'codigo_negociacao': (18, 30),
#             'tipo_mercado': (31, 33),
#             'nome_resumido_empresa': (34, 46),
#             'especificacao_papel': (47, 59),
#             'prazo_dias_mercado_termo': (60, 62),
#             'moeda_referencia': (63, 66),
#             'preco_abertura': (67, 78),
#             'preco_maximo': (79, 90),
#             'preco_minimo': (91, 102),
#             'preco_medio': (103, 114),
#             'preco_ultimo_negocio': (115, 126),
#             'melhor_oferta_compra': (127, 138),
#             'melhor_oferta_venda': (139, 150),
#             'negocios_efetuados': (151, 154),
#             'quantidade_total_titulos': (155, 169),
#             'volume_total_titulos': (170, 187),
#             'preco_exercicio_opcoes': (188, 200),
#             'indicador_correcao_preco': (201, 201),
#             'data_vencimento': (202, 213),
#             'fator_cotacao': (214, 225),
#             'preco_exercicio_pontos': (226, 239),
#             'codigo_isin': (240, 252),
#             'numero_distribuicao': (253, 256)
#         }
        
#         # Open and process the text file
#         with open('src/cotacoes/COTAHIST_A2014.TXT', 'r', encoding='latin1') as txtfile:
#             # Read all lines
#             lines = txtfile.readlines()
            
#             # Skip first and last lines
#             for line in lines[1:-1]:
#                 # Extract fields based on their positions
#                 data_dict = {}
#                 for column, (start, end) in field_positions.items():
#                     if start < len(line):
#                         data_dict[column] = line[start:end].strip()
#                     else:
#                         data_dict[column] = None
                
#                 # Convert values to appropriate types
#                 conversion_rules = {
#                     'preco_abertura': float,
#                     'preco_maximo': float,
#                     'preco_minimo': float,
#                     'preco_medio': float,
#                     'preco_ultimo_negocio': float,
#                     'melhor_oferta_compra': float,
#                     'melhor_oferta_venda': float,
#                     'negocios_efetuados': int,
#                     'quantidade_total_titulos': int,
#                     'volume_total_titulos': float,
#                     'preco_exercicio_opcoes': float,
#                     'indicador_correcao_preco': int,
#                     'data_vencimento': str,
#                     'fator_cotacao': str,
#                     'preco_exercicio_pontos': float,
#                     'codigo_isin': str,
#                     'numero_distribuicao': str
#                 }
                
#                 # Convert values based on rules
#                 for key, converter in conversion_rules.items():
#                     if data_dict[key] and data_dict[key].strip():
#                         try:
#                             if isinstance(converter, (int, float)):
#                                 data_dict[key] = converter(data_dict[key].replace(',', '.'))  # Replace comma with dot for decimals
#                             else:
#                                 data_dict[key] = data_dict[key]
#                         except ValueError:
#                             pass  # Leave as string if conversion fails
                
#                 values = list(data_dict.values())
#                 extras.execute_batch(
#                     cur,
#                     "INSERT INTO cotacoes_historicas (%s) VALUES (%s);" % (
#                         ','.join(field_positions.keys()),  # Columns
#                         ','.join(['%s'] * len(values))    # Placeholders
#                     ),
#                     [values]
#                 )
                
#                 # cur.execute_batch(
#                 #     "INSERT INTO cotacoes_historicas (%s) VALUES (%s);",
#                 #     (tuple(field_positions.keys()),),  # Parameters for the columns
#                 #     [tuple(values)]
#                 # )    
#         cur.close()
#         conn.commit()
#         conn.close()
#     except Exception as e:
#         print(f"Error creating table: {e}")
#     finally:
#         if 'conn' in locals():
#             conn.close()

def main():
    try:
        # Configurações do banco de dados
        db_user = 'postgres'
        db_pass = 'postgres'
        db_host = '192.168.0.130'
        db_port = '5432'
        db_name = 'b3'
    
        # Caminho para o diretório contendo os arquivos CSV
        data_dir = 'src/cotacoes/COTAHIST_A2014.TXT'

        # Criar a engine de conexão com o banco de dados
        engine = create_engine(f'postgresql+psycopg2://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}')
        file_list = ['src/cotacoes/COTAHIST_A2016.TXT', 'src/cotacoes/COTAHIST_A2015.TXT', 'src/cotacoes/COTAHIST_A2017.TXT', 'src/cotacoes/COTAHIST_A2018.TXT', 'src/cotacoes/COTAHIST_A2019.TXT', 'src/cotacoes/COTAHIST_A2020.TXT', 'src/cotacoes/COTAHIST_A2021.TXT', 'src/cotacoes/COTAHIST_A2022.TXT', 'src/cotacoes/COTAHIST_A2023.TXT', 'src/cotacoes/COTAHIST_A2024.TXT']
        # Obter a lista de arquivos CSV no diretório
        # file_list = glob.glob("src/cotacoes/COTAHIST_A2014.TXT")
        

        # Processar cada arquivo
        for filepath in file_list:
            process_file(filepath, engine)
    except Exception as e:
        print(f"Error creating table: {e}")


if __name__ == "__main__":
    main()
