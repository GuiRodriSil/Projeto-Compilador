// Erro esperado: Erro léxico (linha 7, coluna 11): caractere inválido '%' 

soma_pares = 0;
i = 0;

for (i = 0; i <= 10; i = i + 1) {
    if (i % 2 == 0) {
        soma_pares = soma_pares + i;
    }
}

print(soma_pares);