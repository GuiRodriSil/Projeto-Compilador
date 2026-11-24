"""Erros SEMÂNTICOS. Resultado esperado: SemanticError com a mensagem indicada. 
  - "while (x) { ... }" com x int       -> condição do while deve ser booleana, obtido int
  - "for (i = 0; i + 1; i = i + 1) { }" -> condição do for deve ser booleana, obtido int
  - "while (contador < 5) { ... }"      -> variável 'contador' não definida
  - "y = true + 1;"                     -> tipo incompatível: operador '+' exige int, obtido bool
  - "b = 10 / a;" com a = 0             -> divisão por zero
"""

import pytest

from src.interpreter import SemanticError, executar


def erro(codigo):
    with pytest.raises(SemanticError) as e:
        executar(codigo)
    return e.value


def test_while_condicao_nao_booleana():
    e = erro("x = 5; while (x) { x = x - 1; }")
    assert "condição do while deve ser booleana, obtido int" in str(e)


def test_for_condicao_nao_booleana():
    assert "condição do for deve ser booleana" in str(erro("for (i = 0; i + 1; i = i + 1) { }"))


def test_if_condicao_nao_booleana():
    assert "condição do if deve ser booleana" in str(erro("if (1) { }"))


def test_while_variavel_de_controle_nao_definida():
    e = erro("while (contador < 5) { contador = contador + 1; }")
    assert "variável 'contador' não definida" in str(e)
    assert e.linha == 1


def test_for_condicao_usa_variavel_nao_definida():
    assert "variável 'n' não definida" in str(erro("for (i = 0; i < n; i = i + 1) { }"))


def test_for_atualizacao_usa_variavel_nao_definida():
    assert "variável 'k' não definida" in str(erro("for (i = 0; i < 3; i = k + 1) { }"))


def test_variavel_nao_definida_em_print():
    assert "variável 'y' não definida" in str(erro("print(y);"))


def test_soma_bool_com_int():
    assert "operador '+' exige int" in str(erro("y = true + 1;"))


def test_comparacao_bool_com_int():
    assert "tipo incompatível" in str(erro("print(true < 1);"))


def test_igualdade_entre_tipos_diferentes():
    assert "'==' entre int e bool" in str(erro("print(1 == true);"))


def test_menos_unario_em_bool():
    assert "operador '-' exige int" in str(erro("print(-true);"))


def test_reatribuicao_com_tipo_diferente():
    assert "'x' é int e recebeu bool" in str(erro("x = 1; x = true;"))


def test_divisao_por_zero():
    assert "divisão por zero" in str(erro("a = 0; b = 10 / a;"))


def test_linha_do_erro():
    assert erro("x = 1;\ny = 2;\nz = x / 0;").linha == 3
