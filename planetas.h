#ifndef PLANETAS_H
#define PLANETAS_H

typedef struct planetas Planetas;

//Decclaração do cabeçalho das funções
Planetas* criar_planeta(const char* nome, double massa_kg, double x, double y, double velocidadex, double velocidadey);
void deletarPlaneta(Planetas *planetas);

//Ações
void atualizar_orbita(Planetas* planeta, double delta_t);
void imprimir_planeta(const Planetas* planetas);

// Acesso controlado
const char* get_nome(const Planetas* planeta);
double get_raio_orbital(const Planetas* planeta);
double get_posicao(const Planetas* planeta);

#endif
