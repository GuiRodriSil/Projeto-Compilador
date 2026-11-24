from src.interpreter import Interpretador, TabelaSimbolos, executar
from src.parser import analisar


def test_atribuicao_e_print():
    assert executar("x = 10; print(x + 1);") == ["11"]


def test_precedencia_na_execucao():
    assert executar("print(1 + 2 * 3); print((1 + 2) * 3);") == ["7", "9"]


def test_associatividade_na_execucao():
    assert executar("print(10 - 3 - 2); print(16 / 4 / 2);") == ["5", "2"]


def test_divisao_inteira_trunca_para_zero():
    assert executar("print(7 / 2); print(-7 / 2); print(7 / -2);") == ["3", "-3", "-3"]


def test_menos_unario():
    assert executar("x = 4; print(-x); print(- - x);") == ["-4", "4"]


def test_booleanos_e_comparacoes():
    assert executar(
        "print(true); print(1 < 2); print(2 <= 1); print(3 >= 3); print(1 > 2);"
        "print(1 == 1); print(1 != 1); print(true == false);"
    ) == ["true", "true", "false", "true", "false", "true", "false", "false"]


def test_variavel_booleana():
    assert executar("ok = 3 > 2; if (ok) { print(1); }") == ["1"]


def test_if_else():
    assert executar("x = 5; if (x > 0) { print(1); } else { print(0); }") == ["1"]
    assert executar("x = -5; if (x > 0) { print(1); } else { print(0); }") == ["0"]


def test_if_sem_else_falso():
    assert executar("if (false) { print(1); }") == []


def test_while():
    assert executar("x = 3; while (x > 0) { print(x); x = x - 1; }") == ["3", "2", "1"]


def test_for():
    assert executar("for (i = 0; i < 3; i = i + 1) { print(i); }") == ["0", "1", "2"]


def test_for_variavel_de_controle_persiste():
    assert executar("for (i = 0; i < 3; i = i + 1) { } print(i);") == ["3"]


def test_bloco_solto_mesmo_escopo():
    assert executar("{ x = 1; } print(x);") == ["1"]


def test_lacos_aninhados():
    codigo = """
    total = 0;
    for (i = 0; i < 3; i = i + 1) {
        j = 0;
        while (j < 2) { total = total + 1; j = j + 1; }
    }
    print(total);
    """
    assert executar(codigo) == ["6"]


def test_tabela_de_simbolos_insercao_e_busca():
    t = TabelaSimbolos()
    t.inserir("x", 10, 1)
    assert t.buscar("x", 1) == 10
    t.inserir("x", 20, 2)
    assert t.buscar("x", 2) == 20
    assert t.simbolos["x"] == ("int", 20)
    assert "y" not in t


def test_estado_final_da_tabela():
    interp = Interpretador()
    interp.executar(analisar("soma = 0; for (i = 1; i <= 4; i = i + 1) { soma = soma + i; }"))
    assert interp.tabela.simbolos == {"soma": ("int", 10), "i": ("int", 5)}


def test_programa_valido_de_exemplo():
    with open("exemplos/programa_valido.ml", encoding="utf-8") as f:
        saida = executar(f.read())
    assert saida[0] == "30"
    assert saida[1:11] == [str(n) for n in range(10, 0, -1)]
