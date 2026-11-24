from src import ast_nodes as ast
from src.lexer import tokenizar


class ParserError(Exception):
    def __init__(self, mensagem, linha, coluna):
        super().__init__(f"Erro sintático (linha {linha}, coluna {coluna}): {mensagem}")
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna


OPS_IGUALDADE = {"EQ", "NE"}
OPS_RELACIONAIS = {"LT", "GT", "LE", "GE"}
OPS_ADITIVOS = {"PLUS", "MINUS"}
OPS_MULTIPLICATIVOS = {"STAR", "SLASH"}

INICIO_COMANDO = {"IDENT", "PRINT", "IF", "WHILE", "FOR", "LBRACE"}


def _descrever(tok):
    return "fim do arquivo" if tok.tipo == "EOF" else f"'{tok.lexema}'"


class Parser:
    """Parser descendente recursivo: um método para cada não-terminal da EBNF."""

    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0

    # ---------- utilitários ----------
    @property
    def atual(self):
        return self.tokens[self.pos]

    def _avancar(self):
        tok = self.atual
        if tok.tipo != "EOF":
            self.pos += 1
        return tok

    def _erro(self, mensagem):
        raise ParserError(mensagem, self.atual.linha, self.atual.coluna)

    def _esperar(self, tipo, simbolo, contexto):
        if self.atual.tipo != tipo:
            self._erro(f"esperado '{simbolo}' {contexto}, encontrado {_descrever(self.atual)}")
        return self._avancar()

    # ---------- programa e comandos ----------
    def programa(self):
        comandos = []
        while self.atual.tipo != "EOF":
            comandos.append(self.comando())
        return ast.Programa(comandos)

    def comando(self):
        tipo = self.atual.tipo
        if tipo == "IDENT":
            atr = self.atribuicao()
            self._esperar("SEMI", ";", "após a atribuição")
            return atr
        if tipo == "PRINT":
            return self.impressao()
        if tipo == "IF":
            return self.condicional()
        if tipo == "WHILE":
            return self.laco_while()
        if tipo == "FOR":
            return self.laco_for()
        if tipo == "LBRACE":
            return self.bloco()
        self._erro(f"comando inválido iniciado por {_descrever(self.atual)}")

    def bloco(self):
        abre = self._esperar("LBRACE", "{", "para abrir o bloco")
        comandos = []
        while self.atual.tipo in INICIO_COMANDO:
            comandos.append(self.comando())
        self._esperar("RBRACE", "}", "para fechar o bloco")
        return ast.Bloco(comandos, abre.linha)

    def atribuicao(self):
        nome = self._esperar("IDENT", "identificador", "no início da atribuição")
        self._esperar("ASSIGN", "=", f"após '{nome.lexema}'")
        return ast.Atribuicao(nome.lexema, self.expressao(), nome.linha)

    def impressao(self):
        tok = self._avancar()
        self._esperar("LPAREN", "(", "após 'print'")
        expr = self.expressao()
        self._esperar("RPAREN", ")", "para fechar o print")
        self._esperar("SEMI", ";", "após o print")
        return ast.Print(expr, tok.linha)

    def condicional(self):
        tok = self._avancar()
        self._esperar("LPAREN", "(", "após 'if'")
        cond = self.expressao()
        self._esperar("RPAREN", ")", "após a condição do if")
        entao = self.bloco()
        senao = None
        if self.atual.tipo == "ELSE":
            self._avancar()
            senao = self.bloco()
        return ast.If(cond, entao, senao, tok.linha)

    def laco_while(self):
        tok = self._avancar()
        self._esperar("LPAREN", "(", "após 'while'")
        cond = self.expressao()
        self._esperar("RPAREN", ")", "após a condição do while")
        return ast.While(cond, self.bloco(), tok.linha)

    def laco_for(self):
        tok = self._avancar()
        self._esperar("LPAREN", "(", "após 'for'")
        if self.atual.tipo != "IDENT":
            self._erro(f"esperada atribuição na inicialização do for, encontrado {_descrever(self.atual)}")
        init = self.atribuicao()
        self._esperar("SEMI", ";", "após a inicialização do for")
        cond = self.expressao()
        self._esperar("SEMI", ";", "após a condição do for")
        if self.atual.tipo != "IDENT":
            self._erro(f"esperada atribuição na atualização do for, encontrado {_descrever(self.atual)}")
        atualizacao = self.atribuicao()
        self._esperar("RPAREN", ")", "após a atualização do for")
        return ast.For(init, cond, atualizacao, self.bloco(), tok.linha)

    # ---------- expressões (da menor para a maior precedência) ----------
    def expressao(self):
        return self.igualdade()

    def igualdade(self):
        esq = self.relacional()
        if self.atual.tipo in OPS_IGUALDADE:
            op = self._avancar()
            esq = ast.Binario(op.lexema, esq, self.relacional(), op.linha)
            if self.atual.tipo in OPS_IGUALDADE:
                self._erro("operadores de igualdade não podem ser encadeados")
        return esq

    def relacional(self):
        esq = self.aditiva()
        if self.atual.tipo in OPS_RELACIONAIS:
            op = self._avancar()
            esq = ast.Binario(op.lexema, esq, self.aditiva(), op.linha)
            if self.atual.tipo in OPS_RELACIONAIS:
                self._erro("operadores relacionais não podem ser encadeados")
        return esq

    def aditiva(self):
        esq = self.multiplicativa()
        while self.atual.tipo in OPS_ADITIVOS:
            op = self._avancar()
            esq = ast.Binario(op.lexema, esq, self.multiplicativa(), op.linha)
        return esq

    def multiplicativa(self):
        esq = self.unaria()
        while self.atual.tipo in OPS_MULTIPLICATIVOS:
            op = self._avancar()
            esq = ast.Binario(op.lexema, esq, self.unaria(), op.linha)
        return esq

    def unaria(self):
        if self.atual.tipo == "MINUS":
            op = self._avancar()
            return ast.Unario("-", self.unaria(), op.linha)
        return self.primaria()

    def primaria(self):
        tok = self.atual
        if tok.tipo == "INT":
            self._avancar()
            return ast.Inteiro(int(tok.lexema), tok.linha)
        if tok.tipo in ("TRUE", "FALSE"):
            self._avancar()
            return ast.Booleano(tok.tipo == "TRUE", tok.linha)
        if tok.tipo == "IDENT":
            self._avancar()
            return ast.Variavel(tok.lexema, tok.linha)
        if tok.tipo == "LPAREN":
            self._avancar()
            expr = self.expressao()
            self._esperar("RPAREN", ")", "para fechar a expressão")
            return expr
        self._erro(f"expressão esperada, encontrado {_descrever(tok)}")


def analisar(codigo):
    """Lexer + parser: devolve a AST (ast.Programa) ou lança LexerError/ParserError."""
    return Parser(tokenizar(codigo)).programa()


def analisar_expressao(codigo):
    p = Parser(tokenizar(codigo))
    expr = p.expressao()
    if p.atual.tipo != "EOF":
        p._erro(f"símbolo inesperado {_descrever(p.atual)} após a expressão")
    return expr
