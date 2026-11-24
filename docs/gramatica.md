# Definição formal da MiniLang

## 1. Alfabeto (tokens)

O alfabeto de entrada Σ são os caracteres ASCII imprimíveis mais espaço, tabulação e quebra de linha. O lexer agrupa esses caracteres nos tokens abaixo, que formam o alfabeto terminal da gramática.

| Categoria | Token | Lexema / padrão |
|---|---|---|
| Palavras reservadas | `IF`, `ELSE`, `WHILE`, `FOR`, `PRINT`, `TRUE`, `FALSE` | `if`, `else`, `while`, `for`, `print`, `true`, `false` |
| Identificador | `IDENT` | `[a-zA-Z_][a-zA-Z0-9_]*` (exceto palavras reservadas) |
| Inteiro | `INT` | `[0-9]+` (não pode ser seguido imediatamente de letra ou `_`) |
| Aritméticos | `PLUS`, `MINUS`, `STAR`, `SLASH` | `+`, `-`, `*`, `/` |
| Relacionais | `LT`, `GT`, `LE`, `GE`, `EQ`, `NE` | `<`, `>`, `<=`, `>=`, `==`, `!=` |
| Atribuição | `ASSIGN` | `=` |
| Delimitadores | `LPAREN`, `RPAREN`, `LBRACE`, `RBRACE`, `SEMI` | `(`, `)`, `{`, `}`, `;` |
| Fim de arquivo | `EOF` | — |

Ignorados pelo lexer (não viram tokens):
- espaços em branco: `[ \t\r\n]+`
- comentários de linha: `//[^\n]*`

Regras de desambiguação:
- **Maior casamento (maximal munch):** `<=` é um token `LE`, e não `<` seguido de `=`. O mesmo vale para `>=`, `==` e `!=`.
- **Prioridade de palavra reservada:** um lexema que casa com `IDENT` e também é palavra reservada é classificado como palavra reservada. Assim, `while` é `WHILE`, mas `whilex` é `IDENT`.
- **`!` sozinho é inválido:** `!` só existe como prefixo de `!=`.

## 2. Gramática EBNF

Notação: `{ X }` = zero ou mais repetições, `[ X ]` = opcional, `|` = alternativa, terminais entre aspas.

```ebnf
programa        = { comando } EOF ;

comando         = atribuicao ";"
                | impressao
                | condicional
                | laco_while
                | laco_for
                | bloco ;

bloco           = "{" { comando } "}" ;

atribuicao      = IDENT "=" expressao ;

impressao       = "print" "(" expressao ")" ";" ;

condicional     = "if" "(" expressao ")" bloco [ "else" bloco ] ;

laco_while      = "while" "(" expressao ")" bloco ;

laco_for        = "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco ;
(*                    ^inicialização ^condição   ^atualização
   As três cláusulas são obrigatórias: não existe alternativa vazia. *)

(* ---------- Expressões: precedência da menor para a maior ---------- *)
expressao       = igualdade ;

igualdade       = relacional [ ( "==" | "!=" ) relacional ] ;

relacional      = aditiva [ ( "<" | ">" | "<=" | ">=" ) aditiva ] ;

aditiva         = multiplicativa { ( "+" | "-" ) multiplicativa } ;

multiplicativa  = unaria { ( "*" | "/" ) unaria } ;

unaria          = "-" unaria
                | primaria ;

primaria        = INT
                | "true"
                | "false"
                | IDENT
                | "(" expressao ")" ;
```

### Decisões de projeto da gramática

1. **Uma regra para cada nível de precedência.** Cada nível de precedência é um não-terminal, e cada um só deriva o nível imediatamente mais forte. Por isso, em `1 + 2 * 3`, a multiplicação fica obrigatoriamente mais funda na árvore. A gramática não é ambígua.
2. **Sem recursão à esquerda.** A regra recursiva à esquerda `aditiva = aditiva "+" multiplicativa` foi trocada pela repetição `{ ... }`. Isso deixa a gramática pronta para o parser descendente recursivo do item (c). A associatividade à esquerda é obtida na construção da árvore: o laço do parser acumula os operandos da esquerda para a direita.
3. **Comparações não associativas.** Os níveis `igualdade` e `relacional` usam `[ ... ]` (no máximo um operador). Assim, `a < b < c` é erro sintático. Isso evita comparar um booleano com um inteiro, o que seria um erro de tipo.
4. **Sem "else pendurado" (dangling else).** `if`, `while` e `for` exigem um `bloco` com `{ }`, então todo `else` fica ligado a um único `if`.
5. **A atribuição é um comando, não uma expressão.** Por isso `for` usa a regra `atribuicao` na inicialização e na atualização, como pede a especificação.
6. **Restrições que a gramática livre de contexto não expressa**, verificadas na fase semântica:
   - uma variável precisa receber atribuição antes de ser lida;
   - `+ - * /`, o `-` unário e `< > <= >=` exigem operandos `int`;
   - `==` e `!=` exigem dois operandos do mesmo tipo;
   - as condições de `if`, `while` e `for` precisam ser `bool`;
   - divisão por zero é erro em tempo de execução (a divisão é inteira, truncada em direção a zero).

## 3. Tabela de precedência e associatividade

| Nível | Operadores | Associatividade | Não-terminal |
|---|---|---|---|
| 1 (menor) | `==` `!=` | não associativo | `igualdade` |
| 2 | `<` `>` `<=` `>=` | não associativo | `relacional` |
| 3 | `+` `-` (binários) | esquerda | `aditiva` |
| 4 | `*` `/` | esquerda | `multiplicativa` |
| 5 | `-` (unário) | direita | `unaria` |
| 6 (maior) | `( )`, literais, identificadores | — | `primaria` |

Exemplos:
- `1 + 2 * 3` é lido como `1 + (2 * 3)` (o nível 4 vence o nível 3), resultado 7.
- `10 - 3 - 2` é lido como `(10 - 3) - 2` (associatividade à esquerda), resultado 5.
- `- - 4` é lido como `-(-4)` (associatividade à direita), resultado 4.

## 4. Programas de exemplo comentados

### Exemplo 1: válido

```c
// soma dos números de 1 a 5 e contagem regressiva
x = 3;
soma = 0;
for (i = 1; i <= 5; i = i + 1) {
    soma = soma + i;
}
while (x > 0) {
    print(x);
    x = x - 1;
}
if (soma == 15) { print(soma); } else { print(0); }
```

**Justificativa:** todos os lexemas pertencem ao alfabeto. A sequência de tokens é derivável de `programa`:
- `for` segue `laco_for` com as três cláusulas (`atribuicao ; expressao ; atribuicao`);
- `while` segue `laco_while`;
- `if/else` segue `condicional`.

Na parte semântica:
- toda variável recebe atribuição antes de ser lida (`i` é definida pela inicialização do `for`);
- as condições `i <= 5`, `x > 0` e `soma == 15` são `bool`;
- a aritmética só usa `int`;
- não há divisão.

Saída esperada: `3`, `2`, `1`, `15`.

### Exemplo 2: inválido (léxico)

```c
x = 10;
y = x @ 2;
z = 1x;
```

**Justificativa:** o caractere `@` não inicia nenhum padrão da tabela de tokens: o autômato do lexer não tem transição para `@` a partir do estado inicial. Em `1x`, o padrão `INT` termina em `1` e é seguido de uma letra, o que a regra de `INT` proíbe. Não se aceita a divisão em `INT(1) IDENT(x)`, porque isso esconderia um erro de digitação. O erro é detectado antes da análise sintática.

Mensagem esperada: `Erro léxico (linha 2, coluna 7): caractere inválido '@'`.

### Exemplo 3: inválido (sintático, laço mal formado)

```c
soma = 0;
for (i = 0; i < 10) {
    soma = soma + i;
}
```

**Justificativa:** todos os tokens são válidos, então não há erro léxico. A regra `laco_for = "for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco` exige `";"` depois da condição, mas o parser encontra `")"`. Nenhuma derivação de `laco_for` produz essa sequência, porque a gramática não tem cláusula vazia para a atualização. A cadeia não pertence a L(G).

Mensagem esperada: `Erro sintático (linha 2): esperado ';' após a condição do for, encontrado ')'`.

### Exemplo 4: inválido (semântico, variável não definida no laço)

```c
while (contador < 5) {
    print(contador);
    contador = contador + 1;
}
```

**Justificativa:** o programa é léxica e sintaticamente correto: deriva de `laco_while`. Porém `contador` é lido na condição antes de qualquer atribuição. Isso viola a restrição semântica "uma variável precisa estar definida antes do uso". Essa restrição é dependente de contexto, não é expressável na gramática livre de contexto e é verificada pela busca na tabela de símbolos.

Mensagem esperada: `Erro semântico (linha 1): variável 'contador' não definida`.

### Exemplo 5: inválido (semântico, tipo incompatível e condição não booleana)

```c
x = 5;
while (x) {
    x = x - 1;
}
y = true + 1;
```

**Justificativa:** sintaticamente, `while (x)` é válido porque `IDENT` é uma `expressao`. Mas a condição de um laço precisa ser do tipo `bool`, e `x` é `int`. A restrição de tipo da condição foi violada, e a execução para no primeiro erro. A linha `y = true + 1;` também está errada, porque `+` exige dois `int` e recebe `bool + int`.

Mensagem esperada: `Erro semântico (linha 2): condição do while deve ser booleana, obtido int`.
