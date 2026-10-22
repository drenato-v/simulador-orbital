#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <math.h>
#include "planetas.h"

//Constante gravitacional
#define G 6.674e-11
#define TAM 50

typedef struct planetas
{

    char nome[TAM];
    double massa, x, y, velocidadex, velocidadey;

}Planetas;

Planetas* criar_planeta(const char* nome, double massa_kg, double x, double y, double velocidadex, double velocidadey)
{

    // sizeof(Planetas) reserva o tamanho da struct inteira (sizeof(planeta) seria só o tamanho de um ponteiro)
    Planetas* planeta = malloc(sizeof(Planetas));

    if(!planeta)   return NULL;
    
    // Sintaxe: strncpy(destino, origem, n)
    // nome ? nome : "" é um operador ternário que verifica se nome for diferente de NULL
    // caso True ele usa nome, caso contrário usa uma string vazia
    strncpy(planeta->nome, nome ? nome : "", TAM - 1);
    planeta->nome[TAM - 1] = '\0';
    planeta->massa = massa_kg;
    planeta->x = x;
    planeta->y = y;
    planeta->velocidadex = velocidadex;
    planeta->velocidadey = velocidadey;

    return planeta;
}

void deletarPlaneta(Planetas *planetas)
{

    free(planetas);

}

// Atualização orbital simples de planetas com base na Lei da Gravitação Universal de Newton e,
// especificamente, a Terceira Lei de Kepler modificada por Newton.
void atualizar_orbita(Planetas *planeta, double delta_t)
{

    const double massa_sol = 1.989e30;
    double aceleracaox, aceleracaoy;

    // Aceleraçãogravitacional(m/sˆ2)
    double raio_sol = sqrt(pow(planeta->x, 2) + pow(planeta->y, 2));

    // Aceleração gravitacional(vetorial)
    aceleracaox = - (G * massa_sol/pow(raio_sol, 3)) * planeta->x;
    aceleracaoy = - (G * massa_sol/pow(raio_sol, 3)) * planeta->y;

    // Atualizar velocidade
    planeta->velocidadex += aceleracaox * delta_t;
    planeta->velocidadey += aceleracaoy * delta_t;

    planeta->x += planeta->velocidadex * delta_t;
    planeta->y += planeta->velocidadey * delta_t;

}

void imprimir_planeta(const Planetas *planetas)
{

    printf("Planeta: %s\nMassa: %f\n ", planetas->nome, planetas->massa);

}

