"""Erros SINTÁTICOS. Resultado esperado: ParserError com a mensagem indicada.
  - "for (i = 0; i < 10) { }"       -> esperado ';' após a condição do for, encontrado ')'
  - "for (i = 0; i < 10;) { }"      -> esperada atribuição na atualização do for, encontrado ')'
  - "for (; i < 10; i = i + 1) { }" -> esperada atribuição na inicialização do for, encontrado ';'
  - "x = (1 + ;"                    -> expressão esperada, encontrado ';'
  - "x = 10"                        -> esperado ';' após a atribuição, encontrado fim do arquivo
  - "a < b < c"                     -> operadores relacionais não podem ser encadeados
"""

import pytest

from src.parser import ParserError, analisar


def erro(codigo):
    with pytest.raises(ParserError) as e:
        analisar(codigo)
    return e.value


def test_for_sem_atualizacao():
    e = erro("for (i = 0; i < 10) { print(i); }")
    assert "esperado ';' após a condição do for, encontrado ')'" in str(e)


def test_for_com_atualizacao_vazia():
    assert "atualização do for" in str(erro("for (i = 0; i < 10;) { }"))


def test_for_com_inicializacao_vazia():
    assert "inicialização do for" in str(erro("for (; i < 10; i = i + 1) { }"))


def test_for_sem_chaves():
    assert "esperado '{'" in str(erro("for (i = 0; i < 3; i = i + 1) print(i);"))


def test_for_com_expressao_na_atualizacao():
    assert "esperado '=' após 'i'" in str(erro("for (i = 0; i < 3; i + 1) { }"))


def test_while_sem_parenteses():
    assert "esperado '('" in str(erro("while x < 10 { }"))


def test_while_sem_condicao():
    assert "expressão esperada" in str(erro("while () { }"))


def test_while_sem_fechar_bloco():
    assert "esperado '}'" in str(erro("while (true) { x = 1;"))


def test_expressao_incompleta():
    assert "expressão esperada, encontrado ';'" in str(erro("x = (1 + ;"))


def test_parentese_nao_fechado():
    assert "esperado ')'" in str(erro("x = (1 + 2;"))


def test_falta_ponto_e_virgula():
    assert "fim do arquivo" in str(erro("x = 10"))


def test_relacionais_encadeados():
    assert "não podem ser encadeados" in str(erro("x = a < b < c;"))


def test_igualdades_encadeadas():
    assert "não podem ser encadeados" in str(erro("x = a == b == c;"))


def test_else_sem_if():
    assert "comando inválido" in str(erro("else { }"))


def test_if_sem_chaves():
    assert "esperado '{'" in str(erro("if (x > 0) print(x);"))


def test_atribuicao_sem_valor():
    assert "expressão esperada" in str(erro("x = ;"))


def test_linha_do_erro():
    assert erro("x = 1;\ny = 2;\nfor (i = 0; i < 10) { }").linha == 3


def test_programa_invalido_de_exemplo():
    with open("exemplos/programa_invalido.ml", encoding="utf-8") as f:
        e = erro(f.read())
    assert "após a condição do for" in str(e)
