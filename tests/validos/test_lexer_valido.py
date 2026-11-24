from src.lexer import tokenizar


def tipos(codigo):
    return [t.tipo for t in tokenizar(codigo)]


def test_entrada_vazia():
    assert tipos("") == ["EOF"]


def test_atribuicao():
    assert tipos("x = 10;") == ["IDENT", "ASSIGN", "INT", "SEMI", "EOF"]


def test_palavras_reservadas():
    assert tipos("if else while for print true false") == [
        "IF", "ELSE", "WHILE", "FOR", "PRINT", "TRUE", "FALSE", "EOF",
    ]


def test_prefixo_de_reservada_e_identificador():
    toks = tokenizar("whilex for_1 iff")
    assert [t.tipo for t in toks[:-1]] == ["IDENT", "IDENT", "IDENT"]


def test_operadores_aritmeticos_e_parenteses():
    assert tipos("(1 + 2) * 3 - 4 / 5") == [
        "LPAREN", "INT", "PLUS", "INT", "RPAREN", "STAR", "INT",
        "MINUS", "INT", "SLASH", "INT", "EOF",
    ]


def test_relacionais_maior_casamento():
    assert tipos("< > <= >= == != =") == [
        "LT", "GT", "LE", "GE", "EQ", "NE", "ASSIGN", "EOF",
    ]


def test_relacionais_sem_espaco():
    assert tipos("a<=b") == ["IDENT", "LE", "IDENT", "EOF"]


def test_comentario_de_linha_ignorado():
    assert tipos("x = 1; // comentário @ qualquer\ny = 2;") == [
        "IDENT", "ASSIGN", "INT", "SEMI", "IDENT", "ASSIGN", "INT", "SEMI", "EOF",
    ]


def test_comentario_de_bloco_ignorado():
    assert tipos("x /* um\n comentário ** */ = 1;") == [
        "IDENT", "ASSIGN", "INT", "SEMI", "EOF",
    ]


def test_for_completo():
    assert tipos("for (i = 0; i < 10; i = i + 1) { print(i); }") == [
        "FOR", "LPAREN", "IDENT", "ASSIGN", "INT", "SEMI",
        "IDENT", "LT", "INT", "SEMI",
        "IDENT", "ASSIGN", "IDENT", "PLUS", "INT", "RPAREN",
        "LBRACE", "PRINT", "LPAREN", "IDENT", "RPAREN", "SEMI", "RBRACE", "EOF",
    ]


def test_lexemas_e_posicoes():
    toks = tokenizar("x = 42;\n  while")
    assert toks[2].lexema == "42"
    assert (toks[4].tipo, toks[4].linha, toks[4].coluna) == ("WHILE", 2, 3)


def test_programa_valido_de_exemplo():
    with open("exemplos/programa_valido.ml", encoding="utf-8") as f:
        toks = tokenizar(f.read())
    assert toks[-1].tipo == "EOF"
    assert "WHILE" in [t.tipo for t in toks] and "FOR" in [t.tipo for t in toks]
