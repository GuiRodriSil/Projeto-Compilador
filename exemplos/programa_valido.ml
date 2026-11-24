// Programa válido da MiniLang: usa atribuição, aritmética, while, for e if/else

x = 10;
y = 2 * (x + 5);
print(y);

// contagem regressiva com while
while (x > 0) {
    print(x);
    x = x - 1;
}

// soma de 0 a 4 com for
soma = 0;
for (i = 0; i < 5; i = i + 1) {
    soma = soma + i;
}

if (soma > 20) {
    print(soma);
} else {
    print(0);
}

ok = soma == 10;
print(ok);

z = 2;

print(z);
