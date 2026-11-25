# Projeto do Compilador  

Projeto academido desenvolvido para a disciplina de Linguagens formais e Compiladores 


## Requisitos

- Python 3.10+
- Dependências de teste: `pip install -r requirements.txt` (pytest)

Os comandos abaixo devem ser executados na raiz do projeto.

## Rodando os exemplos

```bash
python -m src.interpreter exemplos/<arquivo>.ml
```

| Exemplo | Resultado esperado |
| --- | --- |
| `exemplos/programa_valido.ml` | Executa e imprime a saída do programa |
| `exemplos/programa_invalido.ml` | Erro sintático: `;` ausente na condição do `for` |
| `exemplos/simbolo_inexistente.ml` | Erro léxico: caractere inválido `%` |
| `exemplos/divisao_zero.ml` | Erro semântico: divisão por zero |

## Rodando os testes

```bash
python -m pytest            # todos os testes
python -m pytest -v         # com o nome de cada teste
python -m pytest tests/validos      # só os casos válidos
python -m pytest tests/invalidos    # só os casos inválidos
```

## Alunos 

| Nome | Função |
| --- | --- |
