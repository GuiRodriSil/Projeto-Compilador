// Programa inválido da MiniLang: laço for mal formado (sem a cláusula de atualização)
// Erro esperado: Erro sintático (linha 6): esperado ';' após a condição do for, encontrado ')' 

soma = 0;
i = 0;
for (i = 0; i < 10)  {
    soma = soma + i;
}

print(soma);
