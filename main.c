// gcc main.c cJSON.c -o main
// ./main

#include <stdio.h>
#include <stdlib.h>
#include <math.h>
#include <string.h>
#include <locale.h>
#include "cJSON.h"
#include "planetas.h"

// Cabeçalho da função
char* ler_json(const char* caminho);

int main() 
{

    cJSON *planeta, *nome, *massa, *posicao, *velocidade, *json;
    double px = 0.0, py = 0.0, vx = 0.0, vy = 0.0;
    int tamanho;
    char* texto = ler_json("planetas.json");

    if (!texto) return 1;
    
    // Parse do JSON
    // printf("Conteúdo do JSON:\n%s\n", texto);
    json = cJSON_Parse(texto);

    if (!json) 
    {

        printf("Erro ao fazer parse do JSON!\n");
        free(texto);
        return 1;
    
    }

    // Verifica se o JSON é um array
    if (!cJSON_IsArray(json)) 
    {

        printf("O JSON não é um array!\n");
        cJSON_Delete(json);
        free(texto);
        return 1;
    
    }

    tamanho = cJSON_GetArraySize(json);
    printf("Total de planetas: %d\n\n", tamanho);

    // Percorre cada planeta do array
    for (int i = 0; i < tamanho; i++) 
    {

        cJSON* planeta = cJSON_GetArrayItem(json, i);

        cJSON* nome  = cJSON_GetObjectItemCaseSensitive(planeta, "nome");
        cJSON* massa = cJSON_GetObjectItemCaseSensitive(planeta, "massa_kg");
        
        //  NOVO: ler posicao e velocidade (array [x,y] ou objeto {x:..., y:...})
        cJSON* posicao   = cJSON_GetObjectItemCaseSensitive(planeta, "posicao");
        cJSON* velocidade= cJSON_GetObjectItemCaseSensitive(planeta, "velocidade");


        if (cJSON_IsArray(posicao)) {
            cJSON *p0 = cJSON_GetArrayItem(posicao, 0);
            cJSON *p1 = cJSON_GetArrayItem(posicao, 1);
            if (cJSON_IsNumber(p0)) px = p0->valuedouble;
            if (cJSON_IsNumber(p1)) py = p1->valuedouble;
        } else if (cJSON_IsObject(posicao)) {
            cJSON *jx = cJSON_GetObjectItemCaseSensitive(posicao, "x");
            cJSON *jy = cJSON_GetObjectItemCaseSensitive(posicao, "y");
            if (cJSON_IsNumber(jx)) px = jx->valuedouble;
            if (cJSON_IsNumber(jy)) py = jy->valuedouble;
        }

        if (cJSON_IsArray(velocidade)) {
            cJSON *v0 = cJSON_GetArrayItem(velocidade, 0);
            cJSON *v1 = cJSON_GetArrayItem(velocidade, 1);
            if (cJSON_IsNumber(v0)) vx = v0->valuedouble;
            if (cJSON_IsNumber(v1)) vy = v1->valuedouble;
        } else if (cJSON_IsObject(velocidade)) {
            cJSON *jvx = cJSON_GetObjectItemCaseSensitive(velocidade, "x");
            cJSON *jvy = cJSON_GetObjectItemCaseSensitive(velocidade, "y");
            if (cJSON_IsNumber(jvx)) vx = jvx->valuedouble;
            if (cJSON_IsNumber(jvy)) vy = jvy->valuedouble;
        }
        // if (cJSON_IsString(nome) && cJSON_IsNumber(massa) && cJSON_IsNumber(raio)) 
        // {

        //     printf("Planeta: %s\n", nome->valuestring);
        //     printf("Massa: %.2e kg\n", massa->valuedouble);
        //     printf("Raio orbital: %.2f m\n\n", raio->valuedouble);
        
        // }
    
    }

    cJSON_Delete(json);
    free(texto);

    return 0;

}

// Função para ler o conteúdo de um arquivo JSON inteiro para uma string
char* ler_json(const char* caminho) 
{
    FILE* arq = fopen(caminho, "r");
    if (!arq) 
    {

        printf("Erro ao abrir o arquivo %s\n", caminho);
        return NULL;

    }

    fseek(arq, 0, SEEK_END);
    long tamanho = ftell(arq);
    rewind(arq);

    char* buffer = malloc(tamanho + 1);
    if (!buffer) 
    {

        printf("Erro ao alocar memória!\n");
        fclose(arq);
        return NULL;

    }

    fread(buffer, 1, tamanho, arq);
    buffer[tamanho] = '\0';
    fclose(arq);

    return buffer;

}