CREATE TABLE cotacoes_historicas (
    id INT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    tipo_registro VARCHAR(255) NOT NULL,
    data_pregao DATE NOT NULL,
    codigo_bdi VARCHAR(2) NOT NULL,
    codigo_negociacao VARCHAR(12) NOT NULL,
    tipo_mercado VARCHAR(3),
    nome_resumido_empresa VARCHAR(12),
    especificacao_papel VARCHAR(10),
    prazo_dias_mercado_termo INT,
    moeda_referencia VARCHAR(4),
    preco_abertura DECIMAL(11,99) NULL,
    preco_maximo DECIMAL(11,99) NULL,
    preco_minimo DECIMAL(11,99) NULL,
    preco_medio DECIMAL(11,99) NULL,
    preco_ultimo_negocio DECIMAL(11,99) NULL,
    melhor_oferta_compra DECIMAL(11,99) NULL,
    melhor_oferta_venda DECIMAL(11,99) NULL,
    negocios_efetuados INT,
    quantidade_total_titulos BIGINT,
    volume_total_titulos DECIMAL(16,2),
    preco_exercicio_opcoes DECIMAL(11,99) NULL,
    indicador_correcao_preco INT,
    data_vencimento DATE,
    fator_cotacao VARCHAR(7),
    preco_exercicio_pontos DECIMAL(7,6),
    codigo_isin VARCHAR(12),
    numero_distribuicao VARCHAR(3)
);

ALTER TABLE cotacoes_historicas
ADD CONSTRAINT pk_cotacoes_historicas UNIQUE (
    tipo_registro,
    data_pregao,
    codigo_bdi,
    codigo_negociacao,
    nome_resumido_empresa
);