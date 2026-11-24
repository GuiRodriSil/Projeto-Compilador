from dataclasses import dataclass, field, fields
from typing import List, Optional


@dataclass
class No:
    pass


# ---------- Expressões ----------
@dataclass
class Inteiro(No):
    valor: int
    linha: int = field(default=0, compare=False)


@dataclass
class Booleano(No):
    valor: bool
    linha: int = field(default=0, compare=False)


@dataclass
class Variavel(No):
    nome: str
    linha: int = field(default=0, compare=False)


@dataclass
class Unario(No):
    op: str
    operando: No
    linha: int = field(default=0, compare=False)


@dataclass
class Binario(No):
    op: str
    esq: No
    dir: No
    linha: int = field(default=0, compare=False)


# ---------- Comandos ----------
@dataclass
class Atribuicao(No):
    nome: str
    valor: No
    linha: int = field(default=0, compare=False)


@dataclass
class Print(No):
    expr: No
    linha: int = field(default=0, compare=False)


@dataclass
class Bloco(No):
    comandos: List[No]
    linha: int = field(default=0, compare=False)


@dataclass
class If(No):
    cond: No
    entao: Bloco
    senao: Optional[Bloco] = None
    linha: int = field(default=0, compare=False)


@dataclass
class While(No):
    cond: No
    corpo: Bloco
    linha: int = field(default=0, compare=False)


@dataclass
class For(No):
    init: Atribuicao
    cond: No
    atualizacao: Atribuicao
    corpo: Bloco
    linha: int = field(default=0, compare=False)


@dataclass
class Programa(No):
    comandos: List[No]


def formatar(no, nivel=0):
    pad = "  " * nivel
    if isinstance(no, list):
        return "\n".join(formatar(n, nivel) for n in no)
    if not isinstance(no, No):
        return f"{pad}{no!r}"
    campos = [f for f in fields(no) if f.name != "linha"]
    simples = [f"{f.name}={getattr(no, f.name)!r}" for f in campos
               if not isinstance(getattr(no, f.name), (No, list))]
    linhas = [f"{pad}{type(no).__name__}" + (f"({', '.join(simples)})" if simples else "")]
    for f in campos:
        v = getattr(no, f.name)
        if isinstance(v, (No, list)):
            linhas.append(f"{pad}  .{f.name}:")
            if v != []:
                linhas.append(formatar(v, nivel + 2))
    return "\n".join(linhas)
