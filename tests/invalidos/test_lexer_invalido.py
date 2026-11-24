"""Testes do lexer com entradas inválidas (categoria: erros LÉXICOS).

Resultado esperado: cada entrada lança LexerError com a mensagem e a posição indicadas.
  - "x = @;"          -> Erro léxico (linha 1, coluna 5): caractere inválido '@'
  - "y = 1x;"         -> Erro léxico (linha 1, coluna 5): número mal formado '1x'
  - "x = 1; /* aberto" -> Erro léxico (linha 1, coluna 8): comentário de bloco não fechado
  - "a ! b"           -> Erro léxico (linha 1, coluna 3): '!' deve ser seguido de '='
"""

import pytest

from src.lexer import LexerError, tokenizar


def test_caractere_invalido_arroba():
    with pytest.raises(LexerError) as e:
        tokenizar("x = @;")
    assert "caractere inválido '@'" in str(e.value)
    assert (e.value.linha, e.value.coluna) == (1, 5)


def test_numero_seguido_de_letra():
    with pytest.raises(LexerError) as e:
        tokenizar("y = 1x;")
    assert "número mal formado '1x'" in str(e.value)


def test_comentario_de_bloco_nao_fechado():
    with pytest.raises(LexerError) as e:
        tokenizar("x = 1; /* aberto")
    assert "comentário de bloco não fechado" in str(e.value)
    assert (e.value.linha, e.value.coluna) == (1, 8)


def test_exclamacao_sozinha():
    with pytest.raises(LexerError) as e:
        tokenizar("a ! b")
    assert "'!'" in str(e.value)


@pytest.mark.parametrize("c", ["#", "$", "&", "|", '"', "ç", "%"])
def test_outros_caracteres_fora_do_alfabeto(c):
    with pytest.raises(LexerError):
        tokenizar(f"x = 1 {c} 2;")


def test_erro_informa_linha_correta():
    with pytest.raises(LexerError) as e:
        tokenizar("x = 1;\ny = 2;\nz = @;")
    assert e.value.linha == 3
