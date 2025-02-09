import psycopg2
from psycopg2 import connect, extras
from psycopg2.extras import execute_batch
from config import DB_CONFIG

# Database connection parameters
DB_NAME = DB_CONFIG['dbname']
DB_USER = DB_CONFIG['user']
DB_PASSWORD = DB_CONFIG['password']
DB_HOST = DB_CONFIG['host']
DB_PORT = DB_CONFIG['port']


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



def main():
    # Connect to PostgreSQL database
    conn = psycopg2.connect(
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT
    )
    try:
        create_database(conn)
        if (not check_table_exists(conn)):
            create_table(conn)
        # Create cursor with execute_batch support
        cur = conn.cursor()
        
        # Define the field format positions from the text layout
        field_positions = {
            'tipo_registro': (0, 2),
            'data_pregao': (3, 14),
            'codigo_bdi': (15, 17),
            'codigo_negociacao': (18, 30),
            'tipo_mercado': (31, 33),
            'nome_resumido_empresa': (34, 46),
            'especificacao_papel': (47, 59),
            'prazo_dias_mercado_termo': (60, 62),
            'moeda_referencia': (63, 66),
            'preco_abertura': (67, 78),
            'preco_maximo': (79, 90),
            'preco_minimo': (91, 102),
            'preco_medio': (103, 114),
            'preco_ultimo_negocio': (115, 126),
            'melhor_oferta_compra': (127, 138),
            'melhor_oferta_venda': (139, 150),
            'negocios_efetuados': (151, 154),
            'quantidade_total_titulos': (155, 169),
            'volume_total_titulos': (170, 187),
            'preco_exercicio_opcoes': (188, 200),
            'indicador_correcao_preco': (201, 201),
            'data_vencimento': (202, 213),
            'fator_cotacao': (214, 225),
            'preco_exercicio_pontos': (226, 239),
            'codigo_isin': (240, 252),
            'numero_distribuicao': (253, 256)
        }
        
        # Open and process the text file
        with open('src/cotacoes/COTAHIST_A2014.TXT', 'r', encoding='latin1') as txtfile:
            # Read all lines
            lines = txtfile.readlines()
            
            # Skip first and last lines
            for line in lines[1:-1]:
                # Extract fields based on their positions
                data_dict = {}
                for column, (start, end) in field_positions.items():
                    if start < len(line):
                        data_dict[column] = line[start:end].strip()
                    else:
                        data_dict[column] = None
                
                # Convert values to appropriate types
                conversion_rules = {
                    'preco_abertura': float,
                    'preco_maximo': float,
                    'preco_minimo': float,
                    'preco_medio': float,
                    'preco_ultimo_negocio': float,
                    'melhor_oferta_compra': float,
                    'melhor_oferta_venda': float,
                    'negocios_efetuados': int,
                    'quantidade_total_titulos': int,
                    'volume_total_titulos': float,
                    'preco_exercicio_opcoes': float,
                    'indicador_correcao_preco': int,
                    'data_vencimento': str,
                    'fator_cotacao': str,
                    'preco_exercicio_pontos': float,
                    'codigo_isin': str,
                    'numero_distribuicao': str
                }
                
                # Convert values based on rules
                for key, converter in conversion_rules.items():
                    if data_dict[key] and data_dict[key].strip():
                        try:
                            if isinstance(converter, (int, float)):
                                data_dict[key] = converter(data_dict[key].replace(',', '.'))  # Replace comma with dot for decimals
                            else:
                                data_dict[key] = data_dict[key]
                        except ValueError:
                            pass  # Leave as string if conversion fails
                
                values = list(data_dict.values())
                extras.execute_batch(
                    cur,
                    "INSERT INTO cotacoes_historicas (%s) VALUES (%s);" % (
                        ','.join(field_positions.keys()),  # Columns
                        ','.join(['%s'] * len(values))    # Placeholders
                    ),
                    [values]
                )
                
                # cur.execute_batch(
                #     "INSERT INTO cotacoes_historicas (%s) VALUES (%s);",
                #     (tuple(field_positions.keys()),),  # Parameters for the columns
                #     [tuple(values)]
                # )    
        cur.close()
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Error creating table: {e}")
    finally:
        if 'conn' in locals():
            conn.close()


if __name__ == "__main__":
    main()
