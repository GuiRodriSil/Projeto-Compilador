# Rascunho do relatório (fonte para docs/relatorio.pdf)

## Análise léxica: justificativa formal

**1. Linguagem dos tokens.** Cada tipo de token *t* tem uma expressão regular *rₜ* (tabela da seção 5.1 de `gramatica.md`). Os lexemas válidos da MiniLang formam a linguagem regular

R = r_IF | r_ELSE | … | r_IDENT | r_INT | … | r_SEMI | r_espaço | r_comentário_linha | r_comentário_bloco.

R é regular porque as linguagens regulares são fechadas sob união, concatenação e fecho de Kleene. Os programas lexicamente válidos formam a linguagem R*, também regular.

**2. Das expressões regulares ao AFD.** Pelo Teorema de Kleene, toda expressão regular tem um autômato finito equivalente. O caminho clássico é:
1. Thompson: cada *rₜ* vira um AFN-ε;
2. um novo estado inicial liga, por ε, todos esses AFN-ε;
3. construção de subconjuntos: o AFN resultante vira um AFD;
4. minimização: estados equivalentes são fundidos.

A tabela de transições da seção 5.2 é o resultado desse processo. Para deixá-la mais compacta, os caracteres foram agrupados nas classes L (letras), D (dígitos) e E (espaços). Por exemplo:
- os AFN de `<` e `<=` têm o mesmo prefixo, por isso viram um único estado `q_rel`, que é final, com uma transição em `=` para `q_rel2`;
- as palavras reservadas não têm estados próprios: elas são reconhecidas pelo caminho de `IDENT` (`q_id`) e separadas depois por consulta a uma tabela. Isso gera a mesma linguagem e um AFD muito menor.

**3. Correspondência AFD ↔ código.** Em `src/lexer.py`, cada ramo de `_proximo_token` e de `_pular_ignorados` implementa um estado da tabela:
- os laços `while` implementam as auto-transições: `q_id` em L∪D, `q_int` em D e `q_cb` nos demais caracteres;
- cada teste de `self._atual() == "="` implementa a transição para `q_rel2`, `q_eq` ou `q_ne`;
- os `raise LexerError` implementam os estados de erro.

Como o código não aceita nenhum caractere fora dessas transições, o conjunto de cadeias aceitas pelo código é exatamente L(AFD) = R*.

**4. Tokenização única.** R* sozinha pode ser ambígua. Por exemplo, `<=` poderia ser lido como `<` seguido de `=`, e `while` poderia ser lido como `IDENT`. Duas regras garantem que cada entrada tenha uma única divisão em tokens:
- **maior casamento:** o autômato só emite um token quando não há mais transição;
- **prioridade das palavras reservadas sobre IDENT.**

Assim, a função *entrada → sequência de tokens* fica bem definida.

**5. Rejeição.** Uma entrada é rejeitada exatamente quando o AFD chega a um estado de erro:
- um caractere fora de Σ_tokens, como `@` (`ERR_char`);
- um `INT` seguido de letra, como `1x` (`ERR_num`): a regra foi definida para não dividir esse lexema em `INT IDENT`;
- `eof` dentro de um comentário de bloco (`ERR_com`);
- `!` não seguido de `=` (`ERR_excl`).

Esses casos são cobertos por `tests/invalidos/test_lexer_invalido.py`. Os casos aceitos são cobertos por `tests/validos/test_lexer_valido.py`.

**Conclusão:** o lexer aceita uma cadeia se e somente se ela pertence a R*, e produz sempre a mesma sequência de tokens para ela. Ou seja, o lexer reconhece exatamente os tokens da linguagem.

## Árvore sintática abstrata (AST)

### Definição formal dos nós

Os nós estão em [src/ast_nodes.py](../src/ast_nodes.py). Todos são `@dataclass` derivadas de `No`, e todos têm o campo `linha`, usado só nas mensagens de erro e ignorado na comparação `==`. Usamos dois tipos abstratos: **Expr**, para expressões, e **Cmd**, para comandos.

| Nó | Tipo | Campos | Produção da EBNF |
|---|---|---|---|
| `Programa` | — | `comandos: list[Cmd]` | `programa` |
| `Bloco` | Cmd | `comandos: list[Cmd]` | `bloco` |
| `Atribuicao` | Cmd | `nome: str`, `valor: Expr` | `atribuicao` |
| `Print` | Cmd | `expr: Expr` | `impressao` |
| `If` | Cmd | `cond: Expr`, `entao: Bloco`, `senao: Bloco \| None` | `condicional` |
| `While` | Cmd | `cond: Expr`, `corpo: Bloco` | `laco_while` |
| `For` | Cmd | `init: Atribuicao`, `cond: Expr`, `atualizacao: Atribuicao`, `corpo: Bloco` | `laco_for` |
| `Binario` | Expr | `op: str`, `esq: Expr`, `dir: Expr` | `igualdade`, `relacional`, `aditiva`, `multiplicativa` |
| `Unario` | Expr | `op: str`, `operando: Expr` | `unaria` |
| `Inteiro` | Expr | `valor: int` | `primaria → INT` |
| `Booleano` | Expr | `valor: bool` | `primaria → true \| false` |
| `Variavel` | Expr | `nome: str` | `primaria → IDENT` |

Em notação de tipos algébricos:
```
Expr ::= Inteiro(int) | Booleano(bool) | Variavel(str)
       | Unario(op, Expr) | Binario(op, Expr, Expr)
Cmd  ::= Atribuicao(str, Expr) | Print(Expr) | Bloco([Cmd])
       | If(Expr, Bloco, Bloco?) | While(Expr, Bloco)
       | For(Atribuicao, Expr, Atribuicao, Bloco)
Programa ::= [Cmd]
```

Os campos de `For` usam o tipo `Atribuicao`, e não um `Cmd` qualquer. Assim, a estrutura de dados repete a restrição da gramática: a inicialização e a atualização do `for` precisam ser atribuições.

### Diagrama da AST de um programa completo com laço

Programa:
```c
soma = 0;
for (i = 1; i <= 3; i = i + 1) { soma = soma + i; }
while (soma > 5) { soma = soma - 2; }
if (soma == 4) { print(soma); } else { print(0); }
```

AST:
```
Programa
├── Atribuicao soma
│   └── Inteiro 0
├── For
│   ├── init:        Atribuicao i
│   │                └── Inteiro 1
│   ├── cond:        Binario <=
│   │                ├── Variavel i
│   │                └── Inteiro 3
│   ├── atualizacao: Atribuicao i
│   │                └── Binario +
│   │                    ├── Variavel i
│   │                    └── Inteiro 1
│   └── corpo:       Bloco
│                    └── Atribuicao soma
│                        └── Binario +
│                            ├── Variavel soma
│                            └── Variavel i
├── While
│   ├── cond:  Binario >
│   │          ├── Variavel soma
│   │          └── Inteiro 5
│   └── corpo: Bloco
│              └── Atribuicao soma
│                  └── Binario -
│                      ├── Variavel soma
│                      └── Inteiro 2
└── If
    ├── cond:  Binario ==
    │          ├── Variavel soma
    │          └── Inteiro 4
    ├── entao: Bloco
    │          └── Print
    │              └── Variavel soma
    └── senao: Bloco
               └── Print
                   └── Inteiro 0
```
(Para gerar essa árvore em texto: `formatar(analisar(codigo))`. Saída esperada do programa: `4`.)

### Árvore concreta × árvore abstrata

A **árvore sintática concreta** (árvore de derivação) tem um nó para **cada símbolo** usado na derivação: todo não-terminal aplicado e todo terminal lido. Para a expressão `soma + i`, ela é:
```
expressao
└─ igualdade
   └─ relacional
      └─ aditiva
         ├─ multiplicativa ─ unaria ─ primaria ─ IDENT(soma)
         ├─ "+"
         └─ multiplicativa ─ unaria ─ primaria ─ IDENT(i)
```
São 14 nós. A **AST** da mesma expressão tem 3: `Binario(+, Variavel soma, Variavel i)`.

A AST elimina três tipos de nó:

| O que é eliminado | Por que não faz falta para a execução |
|---|---|
| **Cadeias de não-terminais com um só filho** (`expressao → igualdade → relacional → aditiva`) | Esses níveis existem só para impor a precedência durante a análise. Depois que a árvore está montada, a precedência já está **na forma da árvore**: quem está mais fundo é avaliado antes. |
| **Parênteses** `(` `)` | Servem só para agrupar. O agrupamento já aparece como subárvore: em `(1 + 2) * 3`, o `+` é filho do `*`. Os testes mostram que `((7))` vira só `Inteiro(7)`. |
| **Pontuação e palavras-chave** (`;`, `{`, `}`, `=`, `for`, `while`, `if`, `else`, `print`) | Delimitam e identificam construções. Na AST, essa informação é o **tipo do nó** (`For`, `While`...) e a **posição nos campos**: `init`, `cond` e `atualizacao` substituem os dois `;` do `for`. |

### Justificativa de que a AST preserva a semântica

Para executar um programa, o interpretador precisa de quatro informações. A AST guarda todas:

1. **Que construção é.** O tipo do nó (`While`, `For`, `Binario`...) corresponde um a um às produções que têm significado próprio.
2. **Quais são as partes, e em que papel.** Os campos são nomeados (`cond`, `corpo`, `init`, `atualizacao`, `entao`, `senao`). No `for`, a ordem de execução *init → cond → corpo → atualizacao* depende só desses papéis, e não da posição dos `;` no texto.
3. **A ordem de avaliação das expressões.** A precedência e a associatividade ficam registradas na estrutura: `10 - 3 - 2` vira `Binario(-, Binario(-, 10, 3), 2)`. Uma subárvore é avaliada antes do nó pai, então a ordem é a mesma da árvore concreta.
4. **Os valores e nomes.** Os campos `valor` (`Inteiro`, `Booleano`), `nome` (`Variavel`, `Atribuicao`) e `op` guardam os lexemas que importam. O campo `linha` guarda a posição para as mensagens de erro semântico.

A construção da AST é uma função das árvores concretas válidas para as ASTs. Ela é **injetiva a menos de parênteses redundantes**: duas árvores concretas só geram a mesma AST se diferem por parênteses que não mudam o agrupamento, como `(x)` e `x`. Isso acontece porque cada símbolo eliminado é redundante: ou é determinado pelo tipo do nó (palavras-chave e pontuação), ou pela forma da árvore (níveis de precedência e parênteses). Logo, a AST tem a mesma informação semântica da árvore concreta, e executar a AST dá o mesmo resultado que a gramática define.

Os testes em `tests/validos/test_ast.py` comprovam isso:
- a AST de `1 + 2 * 3` tem o `*` como filho do `+`;
- os parênteses não geram nós;
- o `for` tem as três cláusulas nos campos certos;
- a linha é registrada nos nós.
