import sqlite3

# Criando a conexão com o banco de dados (se não existir, será criado)
conn = sqlite3.connect('veiculos.db')

# Criando um cursor para executar comandos SQL
cursor = conn.cursor()

# Comando SQL para criar uma tabela chamada 'veiculos'
create_table_query = """
CREATE TABLE IF NOT EXISTS veiculos (
    renavam TEXT,
    placa TEXT,
    marca TEXT,
    modelo TEXT
);
"""

# Executando o comando para criar a tabela
cursor.execute(create_table_query)

# Confirmando a criação da tabela
conn.commit()

# Fechando a conexão com o banco de dados
conn.close()
