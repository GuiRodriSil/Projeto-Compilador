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

## Análise sintática

### Técnica adotada: descendente recursiva preditiva (LL(1))

O parser ([src/parser.py](../src/parser.py)) tem **um método para cada não-terminal** da EBNF: `programa`, `comando`, `bloco`, `atribuicao`, `impressao`, `condicional`, `laco_while`, `laco_for`, `expressao`, `igualdade`, `relacional`, `aditiva`, `multiplicativa`, `unaria` e `primaria`. Cada método funciona assim:
- um terminal da produção vira uma chamada a `_esperar(tipo)`;
- um não-terminal vira uma chamada ao método correspondente;
- `{ ... }` vira um laço `while`;
- `[ ... ]` vira um `if`;
- uma escolha entre alternativas é decidida olhando **um único token** à frente (`self.atual`).

O parser não faz retrocesso (backtracking).

**Por que a técnica é compatível com a gramática do item (a).** Um parser descendente recursivo sem retrocesso exige uma gramática LL(1), e a gramática satisfaz as condições:

1. **Não há recursão à esquerda.** As regras de operadores usam repetição (`aditiva = multiplicativa { ("+"|"-") multiplicativa }`) em vez de `aditiva = aditiva "+" multiplicativa`. Com recursão à esquerda, o método `aditiva()` chamaria a si mesmo sem consumir nenhum token, em laço infinito.

2. **Os conjuntos FIRST das alternativas são disjuntos.**

   | Alternativa de `comando` | FIRST |
   |---|---|
   | atribuição | `IDENT` |
   | impressão | `print` |
   | condicional | `if` |
   | `while` | `while` |
   | `for` | `for` |
   | bloco | `{` |

   Em `primaria`, os FIRST são `INT`, `true`, `false`, `IDENT` e `(`. Em `unaria`, o `-` não pertence a FIRST(`primaria`). Logo, um único token decide a alternativa.

3. **Partes opcionais e repetições não conflitam com FOLLOW.** O token que inicia cada parte opcional ou repetida não pode aparecer logo depois dela:

   | Parte opcional ou repetida | Token que a inicia | FOLLOW (o que vem depois) |
   |---|---|---|
   | `[ "else" bloco ]` | `else` | FOLLOW(`condicional`) = FIRST(`comando`) ∪ {`}`, fim de arquivo} |
   | `{ ("+" \| "-") ... }` | `+` `-` | FOLLOW(`aditiva`) = {`<` `>` `<=` `>=` `==` `!=` `)` `;`} |
   | `{ ("*" \| "/") ... }` | `*` `/` | FOLLOW(`multiplicativa`) = FOLLOW(`aditiva`) ∪ {`+`, `-`} |

   Nenhum token da coluna do meio aparece na coluna da direita da mesma linha. Assim, ao ver `else`, `+` ou `*`, o parser sabe com certeza que deve entrar na parte opcional ou repetida.

**Como `while` e `for` são tratados.** Ao ver o token `while` ou `for`, o método `comando` chama `laco_while()` ou `laco_for()`. Esses métodos seguem a produção símbolo a símbolo.

`laco_for()` implementa `"for" "(" atribuicao ";" expressao ";" atribuicao ")" bloco` nesta ordem:
1. `_esperar("(")`;
2. `atribuicao()`: **inicialização**;
3. `_esperar(";")`;
4. `expressao()`: **condição**;
5. `_esperar(";")`;
6. `atribuicao()`: **atualização**;
7. `_esperar(")")`;
8. `bloco()`.

Como a gramática não tem alternativa vazia para nenhuma cláusula, o parser não tem como "pular" uma delas: se o token esperado não está lá, ele lança `ParserError`.

### Árvores sintáticas

**`1 + 2 * 3`.** Árvore de derivação (concreta), resumida:
```
expressao
└─ igualdade
   └─ relacional
      └─ aditiva
         ├─ multiplicativa ─ unaria ─ primaria ─ 1
         ├─ "+"
         └─ multiplicativa
            ├─ unaria ─ primaria ─ 2
            ├─ "*"
            └─ unaria ─ primaria ─ 3
```
AST:
```
      (+)
     /   \
    1    (*)
        /   \
       2     3        valor = 1 + 6 = 7
```

**`(1 + 2) * 3`:**
```
expressao ─ igualdade ─ relacional ─ aditiva
└─ multiplicativa
   ├─ unaria ─ primaria
   │           ├─ "("
   │           ├─ expressao ─ … ─ aditiva
   │           │                   ├─ multiplicativa ─ … ─ 1
   │           │                   ├─ "+"
   │           │                   └─ multiplicativa ─ … ─ 2
   │           └─ ")"
   ├─ "*"
   └─ unaria ─ primaria ─ 3
```
AST:
```
        (*)
       /   \
     (+)    3
    /   \
   1     2            valor = 3 * 3 = 9
```

**Por que as duas árvores são diferentes.** Em `1 + 2 * 3`, o `*` só pode ser gerado dentro de `multiplicativa`, que é filho de `aditiva`. Por isso o `*` fica **mais fundo** na árvore e é avaliado primeiro. Em `(1 + 2) * 3`, os parênteses fazem `primaria` voltar a `expressao`. Assim o `+` vai para dentro de um operando do `*` e passa a ser avaliado primeiro. A forma da árvore define a ordem de avaliação, e por isso os resultados são diferentes (7 e 9).

**`while (x > 0) { print(x); x = x - 1; }`:**
```
While
├─ cond:  (>) ─ x , 0
└─ corpo: Bloco
          ├─ Print ─ x
          └─ Atribuicao x ─ (-) ─ x , 1
```

**`for (i = 0; i < 5; i = i + 1) { soma = soma + i; }`, com as três cláusulas destacadas:**
```
For
├─ [1] init:        Atribuicao i ─ 0
├─ [2] cond:        (<) ─ i , 5
├─ [3] atualizacao: Atribuicao i ─ (+) ─ i , 1
└─ corpo:           Bloco
                    └─ Atribuicao soma ─ (+) ─ soma , i
```
(Essas árvores são geradas por `src.ast_nodes.formatar`.)

### Justificativa formal

**Precedência.** O parser segue a cadeia `igualdade → relacional → aditiva → multiplicativa → unaria → primaria`, e cada método só chama o do nível seguinte. Logo:
- um operador de nível *k* só tem como operandos subárvores de nível maior ou igual a *k + 1*;
- um operador de precedência menor nunca fica abaixo de um de precedência maior, a não ser entre parênteses (`primaria → "(" expressao ")"`).

Isso é exatamente a tabela de precedência da seção 3 do `gramatica.md`. Os testes `test_precedencia_multiplicacao_sobre_soma`, `test_comparacao_abaixo_da_aritmetica` e `test_igualdade_abaixo_da_relacional` comprovam o comportamento.

**Associatividade.**
- **Esquerda, para `+ - * /`.** O laço `while` de `aditiva` e `multiplicativa` faz `esq = Binario(op, esq, proximo)`. Em `a - b - c`, a primeira iteração cria `(a - b)` e a segunda cria `((a - b) - c)`. Por indução no número de operadores, a árvore sempre cresce para a esquerda (teste `test_associatividade_esquerda_subtracao`).
- **Direita, para o `-` unário.** `unaria → "-" unaria` é recursiva à direita, então `- - 4` vira `-(-4)`.
- **Não associativos, para os operadores relacionais e de igualdade.** `[ ... ]` aceita no máximo um operador. Um segundo operador gera erro (teste `test_relacionais_encadeados`).

**Rejeição das entradas inválidas do item (a).** O parser aceita uma sequência de tokens se e somente se ela é derivável de `programa`. Isso vale porque o parser é LL(1): em cada passo existe no máximo uma produção aplicável, e todo token inesperado leva a `ParserError`. Para os exemplos do item (a):

| Exemplo | Resultado |
|---|---|
| `for (i = 0; i < 10) { … }` | Depois de `expressao()`, `_esperar(";")` encontra `)`. Erro: *esperado ';' após a condição do for, encontrado ')'*. |
| `x = (1 + ;` | `primaria()` encontra `;`, que não está em FIRST(`primaria`). Erro: *expressão esperada*. |
| Exemplos 4 e 5 (semânticos) | São sintaticamente válidos e chegam ao interpretador, como devem. |
| Exemplo 2 (léxico) | Não chega ao parser: o lexer rejeita antes. |

Os testes em `tests/invalidos/test_parser_invalido.py` cobrem também `for` com cláusula vazia, `for` sem chaves, `while` sem parênteses, bloco não fechado e `else` sem `if`.

### Comparação com a análise SLR(1)

A alternativa escolhida para comparação é a **SLR(1)** (*Simple LR*). Ela é ascendente: lê os tokens empilhando-os (*shift*) e substitui o lado direito de uma produção pelo lado esquerdo (*reduce*) até chegar ao símbolo inicial. Sua construção segue três passos:
1. a gramática é aumentada com uma nova produção inicial `S' → programa`;
2. constrói-se a coleção canônica de **itens LR(0)**, que forma o autômato de estados (funções *closure* e *goto*);
3. monta-se a tabela ACTION/GOTO, colocando uma redução `A → α` apenas nos tokens de **FOLLOW(A)**.

Não comparamos com a **LR(0)**, porque ela nem se aplica à gramática da MiniLang. Na forma recursiva à esquerda que um parser LR usaria (`aditiva → aditiva "+" multiplicativa | multiplicativa`), o estado que contém o item `aditiva → multiplicativa •` também contém `multiplicativa → multiplicativa • "*" unaria`. A LR(0) reduz sem olhar o próximo token, então nesse estado ela teria um **conflito shift/reduce**. A SLR(1) resolve o conflito: só reduz se o próximo token pertence a FOLLOW(`aditiva`), e `*` não pertence.

| Critério | Descendente recursivo LL(1) (adotado) | SLR(1) |
|---|---|---|
| Direção | Descendente: parte de `programa` e prevê as produções | Ascendente: parte dos tokens e reduz até `programa` |
| Decisão | 1 token à frente, usando FIRST e FOLLOW das alternativas | Estado do autômato LR(0) + 1 token, com FOLLOW para as reduções |
| Classe de gramáticas | LL(1): não aceita recursão à esquerda nem prefixos comuns | SLR(1): aceita recursão à esquerda; é estritamente maior que LL(1) |
| Precedência e associatividade | Por níveis de não-terminais; a associatividade à esquerda vem do laço `while` | Natural: a recursão à esquerda já gera associatividade à esquerda |
| Construção | Escrito diretamente a partir da EBNF, um método por regra | Coleção de itens com dezenas de estados; na prática exige um gerador (yacc, PLY) |
| Mensagens de erro | Contextualizadas, porque cada método sabe onde está ("após a condição do for") | Genéricas: uma entrada vazia em ACTION diz só "token inesperado no estado *n*" |
| Rastreabilidade | O código espelha a gramática, e a pilha de chamadas é a árvore em construção | A relação entre estado e gramática é indireta e difícil de explicar ao usuário |

**Vantagens da SLR(1):** reconhece uma classe maior de gramáticas, aceita a recursão à esquerda sem transformar a gramática e expressa a associatividade à esquerda de forma natural.

**Limitações da SLR(1):** a tabela é grande e difícil de construir e verificar à mão. Ainda aparecem conflitos em gramáticas que precisariam de LALR(1) ou LR(1) canônico. As mensagens de erro são pobres.

**Por que não foi escolhida:** o poder extra da SLR(1) não é necessário, porque a gramática da MiniLang já foi escrita em forma LL(1), sem recursão à esquerda e com FIRST disjuntos. Usar SLR(1) exigiria um gerador externo ou montar à mão um autômato de dezenas de estados. Também pioraria as mensagens de erro, que são centrais no cenário do projeto: uma plataforma didática para alunos que precisam "enxergar" o compilador funcionando.



## Interpretador

O interpretador ([src/interpreter.py](../src/interpreter.py)) percorre a AST recursivamente. Há um método `_exec_<Nó>` para cada comando e um método `avaliar` para as expressões. As verificações semânticas são feitas **durante a execução**: cada operação confere os tipos dos valores antes de ser aplicada.

Para executar um arquivo: `python -m src.interpreter exemplos/programa_valido.ml`.

### Tabela de símbolos

**Estrutura.** A tabela é um dicionário (tabela hash) `nome → (tipo, valor)`, em que `tipo ∈ {int, bool}`. Há **um único escopo global**, porque escopo aninhado está fora do escopo do projeto. Um `{ ... }` não cria escopo novo, e a variável de controle do `for` continua existindo depois do laço.

| Operação | Assinatura | Comportamento | Custo |
|---|---|---|---|
| Inserção | `inserir(nome, valor, linha)` | Se `nome` não existe, cria a entrada `(tipo_de(valor), valor)`. Se existe com o mesmo tipo, atualiza o valor. Se existe com outro tipo, lança *tipo incompatível*. | O(1) em média |
| Busca | `buscar(nome, linha)` | Devolve o valor. Se `nome` não existe, lança *variável 'nome' não definida*. | O(1) em média |

**Por que essa tabela é suficiente.** As verificações semânticas exigidas são três, e cada uma usa uma informação da tabela:

| Verificação | Como a tabela atende |
|---|---|
| Variável não definida | A presença da chave registra se a variável já recebeu atribuição. `buscar` falha se ela não recebeu. |
| Tipo incompatível | O tipo armazenado permite recusar uma reatribuição com tipo diferente. Os tipos dos operandos vêm dos valores (`tipo_de`), então os operadores podem conferir os tipos. |
| Condição de laço não booleana | O valor buscado tem tipo conhecido, e `_condicao` exige `bool`. |

Não há funções nem escopos aninhados. Por isso não é preciso uma pilha de escopos nem guardar a aridade ou a assinatura de funções.

### Semântica operacional

**Notação:**
- σ é o estado, isto é, o conteúdo da tabela de símbolos;
- ⟨e, σ⟩ ⇓ v significa "a expressão *e* avaliada no estado σ resulta no valor *v*";
- ⟨c, σ⟩ → σ' significa "o comando *c* executado em σ leva ao estado σ'";
- **erro** interrompe a execução com `SemanticError`.

**Expressões**

| Regra | Semântica |
|---|---|
| Literal | ⟨n, σ⟩ ⇓ n; ⟨true, σ⟩ ⇓ true; ⟨false, σ⟩ ⇓ false |
| Variável | ⟨x, σ⟩ ⇓ σ(x) se x ∈ dom(σ); senão **erro** "variável não definida" |
| Unário | ⟨e, σ⟩ ⇓ n, n ∈ int ⟹ ⟨-e, σ⟩ ⇓ −n; se n ∈ bool, **erro** de tipo |
| Aritmético | ⟨e₁, σ⟩ ⇓ n₁ e ⟨e₂, σ⟩ ⇓ n₂, ambos int ⟹ ⟨e₁ ⊕ e₂, σ⟩ ⇓ n₁ ⊕ n₂, com ⊕ ∈ {+, −, *}. Se algum operando for bool, **erro** de tipo. |
| Divisão | Como o aritmético, mas com n₂ ≠ 0 e resultado trunc(n₁ / n₂), truncado em direção a zero. Se n₂ = 0, **erro** "divisão por zero". |
| Relacional | n₁ e n₂ int ⟹ ⟨e₁ ⋈ e₂, σ⟩ ⇓ (n₁ ⋈ n₂) ∈ bool, com ⋈ ∈ {<, >, <=, >=} |
| Igualdade | v₁ e v₂ do mesmo tipo ⟹ ⟨e₁ == e₂, σ⟩ ⇓ (v₁ = v₂); `!=` dá a negação. Tipos diferentes dão **erro**. |

Os operandos são avaliados da esquerda para a direita: primeiro e₁, depois e₂.

**Comandos**

| Comando | Semântica |
|---|---|
| Atribuição | ⟨e, σ⟩ ⇓ v ⟹ ⟨x = e, σ⟩ → σ[x ↦ v]. Se x ∈ dom(σ) e o tipo de σ(x) é diferente do tipo de v, **erro**. |
| Print | ⟨e, σ⟩ ⇓ v ⟹ ⟨print(e), σ⟩ → σ, e v é escrito na saída (`true`/`false` para booleanos) |
| Bloco | ⟨c₁, σ⟩ → σ₁, …, ⟨cₙ, σₙ₋₁⟩ → σₙ ⟹ ⟨{c₁ … cₙ}, σ⟩ → σₙ. O bloco vazio deixa σ igual. |
| If | Se ⟨e, σ⟩ ⇓ true, executa o bloco *entao*. Se ⇓ false, executa o *senao*; sem `else`, o estado fica σ. Se o valor não é bool, **erro**. |
| While | ⟨e, σ⟩ ⇓ false ⟹ ⟨while(e) S, σ⟩ → σ. ⟨e, σ⟩ ⇓ true e ⟨S, σ⟩ → σ' ⟹ ⟨while(e) S, σ⟩ → ⟨while(e) S, σ'⟩, ou seja, repete. Se o valor não é bool, **erro**. |
| For | ⟨for(I; e; A) S, σ⟩ executa I primeiro e depois repete: **testa** e; se false, termina; se true, **executa** S, **executa** A e volta ao teste. Se o valor não é bool, **erro**. |
| Programa | Executa os comandos em sequência a partir de σ₀ = ∅. |

**Relação entre o `for` e o `while`.** Pela semântica acima, `for (I; e; A) S` tem o mesmo efeito que `I; while (e) { S A }`. A implementação segue exatamente essa ordem: `executar(init)`, depois um laço que faz `_condicao(cond)`, `executar(corpo)` e `executar(atualizacao)`.

**Limite de iterações.** Cada laço conta suas iterações. Se passar de `max_iteracoes` (100 000 por padrão), lança *limite de iterações excedido (possível laço infinito)*. Isso não muda a semântica dos programas que terminam dentro do limite. É uma proteção para que a suíte de testes nunca trave.

### Justificativa formal

**Executa os programas válidos.** Um programa válido passou pelo lexer e pelo parser e, portanto, tem uma AST. O interpretador define um caso para cada tipo de nó (os métodos `_exec_*` e os ramos de `avaliar`), e cada caso implementa a regra correspondente da tabela acima. Por indução estrutural sobre a AST:
- **casos base:** literais e variáveis são avaliados conforme as regras;
- **passo indutivo:** se os filhos de um nó são avaliados ou executados corretamente, o nó também é, porque o método combina os resultados dos filhos exatamente como a regra manda.

Para os laços, a indução é sobre o número de iterações:
- se a condição é falsa na entrada, o estado não muda (teste *laço que não executa*);
- se cada iteração executa o corpo corretamente, *n* iterações levam ao estado σₙ dado por *n* aplicações da regra.

Os testes de `tests/validos/test_interpreter_valido.py` conferem a saída e o estado final da tabela.

**Rejeita os programas inválidos.** Cada restrição semântica da seção 2 do `gramatica.md` tem um único ponto de verificação no código, executado antes da operação que poderia violá-la:

| Restrição | Onde é verificada |
|---|---|
| Variável definida antes do uso | `TabelaSimbolos.buscar`. Toda leitura de variável passa por ela, inclusive na condição e na atualização do `for`. |
| Operandos `int` em `+ - * /`, `-` unário e `< > <= >=` | `_exigir_int` |
| `==` e `!=` com tipos iguais | `_binario` |
| Condição booleana em `if`, `while` e `for` | `_condicao`. É chamada **antes de cada iteração**, então uma condição que deixa de ser bool no meio do laço também é rejeitada. |
| Divisão por zero | `_binario`, antes de dividir |
| Tipo consistente na reatribuição | `TabelaSimbolos.inserir` |

Como não existe caminho de execução que aplique uma operação sem passar pelo seu ponto de verificação, nenhum programa que viole uma restrição termina normalmente: ele sempre para com `SemanticError`, que indica a linha.

Os casos exigidos pelo enunciado estão em `tests/invalidos/test_interpreter_invalido.py`:
- **condição não booleana em laço:** `while (x)` com `x` int, e um `for` com condição `i + 1`;
- **variável de controle não definida:** `while (contador < 5)` sem atribuição anterior, além de variáveis não definidas na condição e na atualização do `for`.

As verificações são **dinâmicas**: o erro aparece quando o comando é executado. Por isso, o que foi impresso antes do erro continua na saída. Um erro dentro de um ramo que nunca é executado não é detectado. Essa limitação é conhecida e aceitável num interpretador. Ela seria eliminada por uma fase de análise semântica estática antes da execução, que ficou fora do escopo.
