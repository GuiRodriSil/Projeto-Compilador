from src.ast_nodes import (
    Atribuicao, Binario, Bloco, Booleano, For, If, Inteiro, Print, Programa,
    Unario, Variavel, While, formatar,
)
from src.parser import analisar, analisar_expressao


def test_construcao_manual_de_1_mais_2_vezes_3():
    no = Binario("+", Inteiro(1), Binario("*", Inteiro(2), Inteiro(3)))
    assert no.op == "+"
    assert no.esq == Inteiro(1)
    assert no.dir.op == "*"
    assert (no.dir.esq.valor, no.dir.dir.valor) == (2, 3)


def test_parser_gera_ast_de_1_mais_2_vezes_3():
    assert analisar_expressao("1 + 2 * 3") == Binario(
        "+", Inteiro(1), Binario("*", Inteiro(2), Inteiro(3))
    )


def test_parenteses_nao_viram_no():
    assert analisar_expressao("((7))") == Inteiro(7)
    assert analisar_expressao("(1 + 2) * 3") == Binario(
        "*", Binario("+", Inteiro(1), Inteiro(2)), Inteiro(3)
    )


def test_for_com_as_tres_clausulas():
    no = analisar("for (i = 0; i < 10; i = i + 1) { print(i); }").comandos[0]
    assert no == For(
        init=Atribuicao("i", Inteiro(0)),
        cond=Binario("<", Variavel("i"), Inteiro(10)),
        atualizacao=Atribuicao("i", Binario("+", Variavel("i"), Inteiro(1))),
        corpo=Bloco([Print(Variavel("i"))]),
    )
    assert isinstance(no.init, Atribuicao)
    assert isinstance(no.atualizacao, Atribuicao)


def test_while_campos_condicao_e_corpo():
    no = analisar("while (x > 0) { x = x - 1; }").comandos[0]
    assert isinstance(no, While)
    assert no.cond == Binario(">", Variavel("x"), Inteiro(0))
    assert no.corpo.comandos == [Atribuicao("x", Binario("-", Variavel("x"), Inteiro(1)))]


def test_if_guarda_os_dois_ramos():
    no = analisar("if (true) { print(1); } else { print(2); }").comandos[0]
    assert no == If(Booleano(True), Bloco([Print(Inteiro(1))]), Bloco([Print(Inteiro(2))]))


def test_menos_unario():
    assert analisar_expressao("-x") == Unario("-", Variavel("x"))


def test_linha_registrada_nos_nos():
    prog = analisar("x = 1;\n\nwhile (x > 0) {\n  x = x - 1;\n}")
    laco = prog.comandos[1]
    assert laco.linha == 3
    assert laco.corpo.comandos[0].linha == 4


def test_linha_nao_afeta_igualdade():
    assert Inteiro(5, linha=1) == Inteiro(5, linha=99)


def test_programa_completo_com_laco():
    prog = analisar(
        "soma = 0;\n"
        "for (i = 1; i <= 3; i = i + 1) { soma = soma + i; }\n"
        "print(soma);"
    )
    assert isinstance(prog, Programa)
    assert [type(c) for c in prog.comandos] == [Atribuicao, For, Print]


def test_formatar():
    texto = formatar(analisar_expressao("1 + 2 * 3"))
    assert texto.splitlines()[0] == "Binario(op='+')"
    assert "Binario(op='*')" in texto
