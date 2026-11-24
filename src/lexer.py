from dataclasses import dataclass


class LexerError(Exception):
    """Erro léxico com posição (linha e coluna começam em 1)."""

    def __init__(self, mensagem, linha, coluna):
        super().__init__(f"Erro léxico (linha {linha}, coluna {coluna}): {mensagem}")
        self.mensagem = mensagem
        self.linha = linha
        self.coluna = coluna


@dataclass(frozen=True)
class Token:
    tipo: str      # ex.: "INT", "IDENT", "WHILE", "PLUS", "EOF"
    lexema: str    # texto original ("" para EOF)
    linha: int
    coluna: int


PALAVRAS_RESERVADAS = {
    "if": "IF",
    "else": "ELSE",
    "while": "WHILE",
    "for": "FOR",
    "print": "PRINT",
    "true": "TRUE",
    "false": "FALSE",
}

# Símbolos de um único caractere que não são prefixo de nenhum outro token.
SIMBOLOS_SIMPLES = {
    "+": "PLUS",
    "-": "MINUS",
    "*": "STAR",
    "(": "LPAREN",
    ")": "RPAREN",
    "{": "LBRACE",
    "}": "RBRACE",
    ";": "SEMI",
}

# Símbolos que podem ser seguidos de '=' formando outro token: (sozinho, com '=').
SIMBOLOS_COM_IGUAL = {
    "<": ("LT", "LE"),
    ">": ("GT", "GE"),
    "=": ("ASSIGN", "EQ"),
}

ESPACOS = " \t\r\n"


def _eh_letra(c):
    return c.isascii() and (c.isalpha() or c == "_")


def _eh_digito(c):
    return c.isascii() and c.isdigit()


class Lexer:
    def __init__(self, codigo):
        self.codigo = codigo
        self.pos = 0
        self.linha = 1
        self.coluna = 1

    # ---------- utilitários de leitura ----------
    def _atual(self):
        return self.codigo[self.pos] if self.pos < len(self.codigo) else ""

    def _seguinte(self):
        p = self.pos + 1
        return self.codigo[p] if p < len(self.codigo) else ""

    def _avancar(self):
        c = self.codigo[self.pos]
        self.pos += 1
        if c == "\n":
            self.linha += 1
            self.coluna = 1
        else:
            self.coluna += 1
        return c

    # ---------- estados que descartam entrada ----------
    def _pular_ignorados(self):
        """Estados q0 (espaços), q_com_linha e q_com_bloco/q_com_bloco_estrela."""
        while True:
            c = self._atual()
            if c and c in ESPACOS:
                self._avancar()
            elif c == "/" and self._seguinte() == "/":
                while self._atual() and self._atual() != "\n":
                    self._avancar()
            elif c == "/" and self._seguinte() == "*":
                linha, coluna = self.linha, self.coluna
                self._avancar()
                self._avancar()
                while True:
                    if not self._atual():
                        raise LexerError("comentário de bloco não fechado", linha, coluna)
                    if self._atual() == "*" and self._seguinte() == "/":
                        self._avancar()
                        self._avancar()
                        break
                    self._avancar()
            else:
                return

    # ---------- reconhecimento de um token ----------
    def _proximo_token(self):
        self._pular_ignorados()
        linha, coluna = self.linha, self.coluna
        c = self._atual()

        if not c:
            return Token("EOF", "", linha, coluna)

        # q_id: letra/_ seguido de (letra|dígito|_)*
        if _eh_letra(c):
            inicio = self.pos
            while _eh_letra(self._atual()) or _eh_digito(self._atual()):
                self._avancar()
            lexema = self.codigo[inicio:self.pos]
            return Token(PALAVRAS_RESERVADAS.get(lexema, "IDENT"), lexema, linha, coluna)

        # q_int: dígito+ (letra/_ logo depois leva ao estado de erro)
        if _eh_digito(c):
            inicio = self.pos
            while _eh_digito(self._atual()):
                self._avancar()
            if _eh_letra(self._atual()):
                while _eh_letra(self._atual()) or _eh_digito(self._atual()):
                    self._avancar()
                lexema = self.codigo[inicio:self.pos]
                raise LexerError(f"número mal formado '{lexema}'", linha, coluna)
            return Token("INT", self.codigo[inicio:self.pos], linha, coluna)

        if c in SIMBOLOS_SIMPLES:
            self._avancar()
            return Token(SIMBOLOS_SIMPLES[c], c, linha, coluna)

        # '/' só chega aqui se não iniciar comentário
        if c == "/":
            self._avancar()
            return Token("SLASH", c, linha, coluna)

        # q_lt, q_gt, q_assign: aceitam sozinhos ou com '=' (maior casamento)
        if c in SIMBOLOS_COM_IGUAL:
            sozinho, com_igual = SIMBOLOS_COM_IGUAL[c]
            self._avancar()
            if self._atual() == "=":
                self._avancar()
                return Token(com_igual, c + "=", linha, coluna)
            return Token(sozinho, c, linha, coluna)

        # q_bang: estado não final, exige '='
        if c == "!":
            self._avancar()
            if self._atual() == "=":
                self._avancar()
                return Token("NE", "!=", linha, coluna)
            raise LexerError("'!' deve ser seguido de '=' (operador '!=')", linha, coluna)

        raise LexerError(f"caractere inválido '{c}'", linha, coluna)

    def tokenizar(self):
        tokens = []
        while True:
            tok = self._proximo_token()
            tokens.append(tok)
            if tok.tipo == "EOF":
                return tokens


def tokenizar(codigo):
    """Atalho: devolve a lista de tokens (terminada em EOF) ou lança LexerError."""
    return Lexer(codigo).tokenizar()
