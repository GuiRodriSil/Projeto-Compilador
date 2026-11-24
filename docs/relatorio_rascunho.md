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
