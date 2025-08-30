
import os
from sqlalchemy import create_engine, text
from src.database.config import get_database_config

def migrate_service_order_files():
    """
    Migração para adicionar colunas de arquivos na tabela service_order
    """
    config = get_database_config()
    engine = create_engine(config['SQLALCHEMY_DATABASE_URI'])
    
    try:
        with engine.connect() as conn:
            # Para PostgreSQL, verificamos se as colunas existem de forma diferente
            result = conn.execute(text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'service_order' 
                AND column_name IN ('file1_filename', 'file2_filename', 'file3_filename')
            """))
            
            existing_columns = [row[0] for row in result.fetchall()]
            
            # Adicionar colunas que não existem
            columns_to_add = [
                ('file1_filename', 'VARCHAR(200)'),
                ('file2_filename', 'VARCHAR(200)'),
                ('file3_filename', 'VARCHAR(200)')
            ]
            
            for column_name, column_type in columns_to_add:
                if column_name not in existing_columns:
                    try:
                        conn.execute(text(f"ALTER TABLE service_order ADD COLUMN {column_name} {column_type}"))
                        conn.commit()
                        print(f"Coluna {column_name} adicionada com sucesso!")
                    except Exception as e:
                        print(f"Erro ao adicionar coluna {column_name}: {e}")
                        conn.rollback()
                else:
                    print(f"Coluna {column_name} já existe.")
                    
        print("Migração de arquivos do service_order concluída!")
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")

if __name__ == "__main__":
    migrate_service_order_files()
