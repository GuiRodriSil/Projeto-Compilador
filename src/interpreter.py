import sys

from src import ast_nodes as ast
from src.lexer import LexerError
from src.parser import ParserError, analisar


class SemanticError(Exception):
    def __init__(self, mensagem, linha):
        super().__init__(f"Erro semântico (linha {linha}): {mensagem}")
        self.mensagem = mensagem
        self.linha = linha


def tipo_de(valor):
    return "bool" if isinstance(valor, bool) else "int"


def formatar_valor(valor):
    if isinstance(valor, bool):
        return "true" if valor else "false"
    return str(valor)


class TabelaSimbolos:
    """Escopo único: nome -> (tipo, valor)."""

    def __init__(self):
        self.simbolos = {}

    def inserir(self, nome, valor, linha):
        tipo = tipo_de(valor)
        if nome in self.simbolos and self.simbolos[nome][0] != tipo:
            raise SemanticError(
                f"tipo incompatível: '{nome}' é {self.simbolos[nome][0]} e recebeu {tipo}", linha
            )
        self.simbolos[nome] = (tipo, valor)

    def buscar(self, nome, linha):
        if nome not in self.simbolos:
            raise SemanticError(f"variável '{nome}' não definida", linha)
        return self.simbolos[nome][1]

    def __contains__(self, nome):
        return nome in self.simbolos


class Interpretador:
    def __init__(self, max_iteracoes=100_000, saida=None):
        self.tabela = TabelaSimbolos()
        self.max_iteracoes = max_iteracoes
        self.saida = [] if saida is None else saida

    # ---------- comandos ----------
    def executar(self, no):
        metodo = getattr(self, f"_exec_{type(no).__name__}")
        metodo(no)

    def _exec_Programa(self, no):
        for cmd in no.comandos:
            self.executar(cmd)

    def _exec_Bloco(self, no):
        for cmd in no.comandos:
            self.executar(cmd)

    def _exec_Atribuicao(self, no):
        self.tabela.inserir(no.nome, self.avaliar(no.valor), no.linha)

    def _exec_Print(self, no):
        self.saida.append(formatar_valor(self.avaliar(no.expr)))

    def _exec_If(self, no):
        if self._condicao(no.cond, "if", no.linha):
            self.executar(no.entao)
        elif no.senao is not None:
            self.executar(no.senao)

    def _exec_While(self, no):
        iteracoes = 0
        while self._condicao(no.cond, "while", no.linha):
            iteracoes = self._contar(iteracoes, "while", no.linha)
            self.executar(no.corpo)

    def _exec_For(self, no):
        self.executar(no.init)
        iteracoes = 0
        while self._condicao(no.cond, "for", no.linha):
            iteracoes = self._contar(iteracoes, "for", no.linha)
            self.executar(no.corpo)
            self.executar(no.atualizacao)

    def _condicao(self, expr, comando, linha):
        valor = self.avaliar(expr)
        if not isinstance(valor, bool):
            raise SemanticError(
                f"condição do {comando} deve ser booleana, obtido {tipo_de(valor)}", linha
            )
        return valor

    def _contar(self, iteracoes, comando, linha):
        iteracoes += 1
        if iteracoes > self.max_iteracoes:
            raise SemanticError(
                f"limite de {self.max_iteracoes} iterações excedido no {comando} (possível laço infinito)",
                linha,
            )
        return iteracoes

    # ---------- expressões ----------
    def avaliar(self, no):
        if isinstance(no, (ast.Inteiro, ast.Booleano)):
            return no.valor
        if isinstance(no, ast.Variavel):
            return self.tabela.buscar(no.nome, no.linha)
        if isinstance(no, ast.Unario):
            v = self.avaliar(no.operando)
            self._exigir_int(v, "-", no.linha)
            return -v
        if isinstance(no, ast.Binario):
            return self._binario(no)
        raise TypeError(f"nó desconhecido: {type(no).__name__}")

    def _exigir_int(self, valor, op, linha):
        if tipo_de(valor) != "int":
            raise SemanticError(f"tipo incompatível: operador '{op}' exige int, obtido bool", linha)

    def _binario(self, no):
        a = self.avaliar(no.esq)
        b = self.avaliar(no.dir)
        op = no.op

        if op in ("==", "!="):
            if tipo_de(a) != tipo_de(b):
                raise SemanticError(
                    f"tipo incompatível: '{op}' entre {tipo_de(a)} e {tipo_de(b)}", no.linha
                )
            return (a == b) if op == "==" else (a != b)

        self._exigir_int(a, op, no.linha)
        self._exigir_int(b, op, no.linha)

        if op == "+":
            return a + b
        if op == "-":
            return a - b
        if op == "*":
            return a * b
        if op == "/":
            if b == 0:
                raise SemanticError("divisão por zero", no.linha)
            q = abs(a) // abs(b)
            return q if (a >= 0) == (b > 0) else -q
        if op == "<":
            return a < b
        if op == ">":
            return a > b
        if op == "<=":
            return a <= b
        if op == ">=":
            return a >= b
        raise TypeError(f"operador desconhecido: {op}")


def executar(codigo, max_iteracoes=100_000):
    """Lexer + parser + interpretador. Devolve a lista de linhas impressas."""
    interp = Interpretador(max_iteracoes)
    interp.executar(analisar(codigo))
    return interp.saida


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if len(argv) != 1:
        print("uso: python -m src.interpreter <arquivo.ml>", file=sys.stderr)
        return 2
    with open(argv[0], encoding="utf-8") as f:
        codigo = f.read()
    saida = []
    interp = Interpretador(saida=saida)
    try:
        programa = analisar(codigo)
        interp.executar(programa)
    except (LexerError, ParserError, SemanticError) as e:
        for linha in saida:
            print(linha)
        print(e, file=sys.stderr)
        return 1
    for linha in saida:
        print(linha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
