from src.ast_nodes import (
    Atribuicao, Binario, Bloco, Booleano, For, If, Inteiro, Print, Unario, Variavel, While,
)
from src.parser import analisar, analisar_expressao


def B(op, e, d):
    return Binario(op, e, d)


def test_precedencia_multiplicacao_sobre_soma():
    assert analisar_expressao("1 + 2 * 3") == B("+", Inteiro(1), B("*", Inteiro(2), Inteiro(3)))


def test_parenteses_alteram_precedencia():
    assert analisar_expressao("(1 + 2) * 3") == B("*", B("+", Inteiro(1), Inteiro(2)), Inteiro(3))


def test_associatividade_esquerda_subtracao():
    assert analisar_expressao("10 - 3 - 2") == B("-", B("-", Inteiro(10), Inteiro(3)), Inteiro(2))


def test_associatividade_esquerda_divisao():
    assert analisar_expressao("8 / 4 / 2") == B("/", B("/", Inteiro(8), Inteiro(4)), Inteiro(2))


def test_menos_unario_associa_a_direita():
    assert analisar_expressao("- - 4") == Unario("-", Unario("-", Inteiro(4)))


def test_menos_unario_mais_forte_que_multiplicacao():
    assert analisar_expressao("-2 * 3") == B("*", Unario("-", Inteiro(2)), Inteiro(3))


def test_comparacao_abaixo_da_aritmetica():
    assert analisar_expressao("x + 1 < y * 2") == B(
        "<", B("+", Variavel("x"), Inteiro(1)), B("*", Variavel("y"), Inteiro(2))
    )


def test_igualdade_abaixo_da_relacional():
    assert analisar_expressao("a < b == true") == B("==", B("<", Variavel("a"), Variavel("b")), Booleano(True))


def test_atribuicao_e_print():
    prog = analisar("x = 10; print(x + 1);")
    assert prog.comandos == [
        Atribuicao("x", Inteiro(10)),
        Print(B("+", Variavel("x"), Inteiro(1))),
    ]


def test_if_else():
    prog = analisar("if (x > 0) { print(1); } else { print(0); }")
    assert prog.comandos[0] == If(
        B(">", Variavel("x"), Inteiro(0)),
        Bloco([Print(Inteiro(1))]),
        Bloco([Print(Inteiro(0))]),
    )


def test_if_sem_else():
    assert analisar("if (true) { }").comandos[0] == If(Booleano(True), Bloco([]), None)


def test_while():
    prog = analisar("while (x < 10) { x = x + 1; }")
    assert prog.comandos[0] == While(
        B("<", Variavel("x"), Inteiro(10)),
        Bloco([Atribuicao("x", B("+", Variavel("x"), Inteiro(1)))]),
    )


def test_for_com_tres_clausulas():
    no = analisar("for (i = 0; i < 10; i = i + 1) { print(i); }").comandos[0]
    assert isinstance(no, For)
    assert no.init == Atribuicao("i", Inteiro(0))
    assert no.cond == B("<", Variavel("i"), Inteiro(10))
    assert no.atualizacao == Atribuicao("i", B("+", Variavel("i"), Inteiro(1)))
    assert no.corpo == Bloco([Print(Variavel("i"))])


def test_lacos_aninhados_e_bloco_solto():
    prog = analisar("{ for (i = 0; i < 2; i = i + 1) { while (false) { } } }")
    bloco = prog.comandos[0]
    assert isinstance(bloco, Bloco)
    assert isinstance(bloco.comandos[0], For)
    assert isinstance(bloco.comandos[0].corpo.comandos[0], While)


def test_programa_vazio():
    assert analisar("// só comentário\n").comandos == []


def test_programa_valido_de_exemplo():
    with open("exemplos/programa_valido.ml", encoding="utf-8") as f:
        prog = analisar(f.read())
    tipos = {type(c) for c in prog.comandos}
    assert While in tipos and For in tipos and If in tipos
