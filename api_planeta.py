import math
import json
import os
import requests

from flask import Flask, jsonify, request

PLANETAS = [
    "mercury", "venus", "earth", "mars",
    "jupiter", "saturn", "uranus", "neptune"
]

API_URL = "https://api.api-ninjas.com/v1/planets?name={}"
# A chave é lida da variável de ambiente API_NINJAS_KEY para não ficar exposta no código
# Exemplo (terminal): export API_NINJAS_KEY="sua_chave_aqui"
API_KEY = os.environ.get("API_NINJAS_KEY")
TIMEOUT = 10

#fetch_planeta(buscar planeta)
def fetch_planeta(nome):

    if not API_KEY:
        print("Erro: defina a variável de ambiente API_NINJAS_KEY com a sua chave da API Ninjas.")
        return None

    try:

        #Cria um dicionário de cabeçalhos(headers) para a requisição e autentificação HTTP perante a API
        #X-Api-Key é o nome do cabeçalho exigido pela API da API Ninjas
        #API_KEY é uma variável global que guarda a chave da API
        headers = {"X-Api-Key": API_KEY}

        #"requests.get()" envia uma requisição HTTP do tipo GET
        #"API_URL.format(nome)" insere o nome do planeta dentro da URL-base
        #BASE: "https://api.api-ninjas.com/v1/planets?name={}"
        #"https://api.api-ninjas.com/v1/planets?name=mars"
        #headers=headers envia o dicionário de cabeçalhos HTTP
        #timeout define o tempo máximo de espera pela resposta(em segundos)
        resp = requests.get(API_URL.format(nome), headers=headers, timeout=TIMEOUT) 

        #Essa função é responsável por verificar se a solicitação foi bem sucedida
        #resp é o objeto de resposta retornado pela biblioteca request
        #Raise-for_status() é um método desse objeto que verifica se o código de status HTTP
        #está na faixa de sucesso(200-299) ou de erro(400-500)
        resp.raise_for_status()

        #".json" é um método que analisa o corpo da resposta como json e retorna um dicionário e uma lista.
        dados = resp.json()

        #isinstance verifica se a resposta é uma alista e dados garante que a lista não é vazia
        return dados[0] if isinstance(dados, list) and dados else None
    

    #requests.RequestException captura qualquer erro de rede ou requisição e "e" armazena essa resposta para imprimir
    except requests.RequestException as e:
        print(f"Erro ao obter {nome}: {e}")
        return None


def parse_planeta(dados):
    
    if not dados:
        return None

    #Método que tenta encontrar o valor da chave no dicionário
    name = dados.get("englishName") or dados.get("name") or dados.get("id")

    #Mass_raw(Massa bruta)
    mass_raw = dados.get("mass")
    massa_kg = None
    if mass_raw is not None:
        try:

            # A API Ninjas informa a massa em massas de Júpiter
            # Convertendo para kg (1 massa de Júpiter = 1.898e27 kg)
            massa_kg = float(mass_raw) * 1.898e27
            
        except (TypeError, ValueError):
            massa_kg = None

    #O semieixo maior é a metade da distância mais longa através de uma elipse 
    #ou a distância do centro ao ponto mais distante da elipse. 
    semi_eixo_maior = dados.get("semi_major_axis")
    raio_orbital_m = None
    if semi_eixo_maior is not None:
        try:
            
            #Raio orbital(em unidade astronômica(AU) → converter para metros)
            raio_orbital_m = float(semi_eixo_maior) * 1.496e11  # 1 AU em metros
        except (TypeError, ValueError):
            raio_orbital_m = None

    # Período orbital (em dias)
    periodo_dias = None
    if "period" in dados:
        try:
            periodo_dias = float(dados["period"])
        except (TypeError, ValueError):
            periodo_dias = None

    # Velocidade média orbital (m/s)
    velocidade_media_m_s = None
    if raio_orbital_m is not None and periodo_dias:
        try:

            # Converte período em dias para segundos
            periodo_s = periodo_dias * 24.0 * 3600.0

            # A velocidade orbital média é a velocidade constante que o corpo precisa manter 
            # para completar sua obra elíptica ao redor da Sol
            # Fórmula da velocidade orbital média
            # math.pi retorna o valor da constante matemática PI
            velocidade_media_m_s = 2.0 * math.pi * raio_orbital_m / periodo_s
        except (TypeError, ValueError):
            velocidade_media_m_s = None

    # --------------------------------------------------------
    # Adição: Cálculo das componentes vetoriais (x, y)
    # --------------------------------------------------------
    # Para simplificar o modelo orbital inicial, podemos supor:
    # - O Sol está no centro do sistema (0, 0)
    # - O planeta inicia em (x, y) = (raio_orbital_m, 0)
    # - A velocidade é tangente à órbita circular, portanto (vx, vy) = (0, velocidade_media_m_s)
    # Isso cria uma base vetorial adequada para integrações futuras.
    pos_x = raio_orbital_m if raio_orbital_m is not None else 0.0
    pos_y = 0.0
    vel_x = 0.0
    vel_y = velocidade_media_m_s if velocidade_media_m_s is not None else 0.0

    # --------------------------------------------------------
    # Retorno final com todos os campos (escalares e vetoriais)
    # --------------------------------------------------------
    return {
        "nome": name,
        "massa_kg": massa_kg,
        "raio_orbital_m": raio_orbital_m,
        "periodo_dias": periodo_dias,
        "velocidade_media_m_s": velocidade_media_m_s,

        # Novos campos vetoriais (posição e velocidade)
        # Servirão diretamente para simulações físicas 2D.
        "posicao": {"x": pos_x, "y": pos_y},
        "velocidade": {"x": vel_x, "y": vel_y}
    }


def salvar_json(dados, filename="planetas.json"):

    # __FILE__ é uma variável especial do Python que armazena o caminho atual do arquivo.py
    # os.path.dirname extrai apenas o diretório onde o arquivo .py está
    # os.path.join() identifica o separador correto de pastas e cria o caminho final do arquivo 
    # os.path.join(...) junta o diretório com o nome do arquivo(filename) de forma segura e compatível com o SO
    caminho = os.path.join(os.path.dirname(__file__), filename)
    try:

        # with é um gerenciador de contexto. Ele garante que o arquivo seja fechado mesmo se ocorrem erros
        # open abre o arquivo especificado
        # w -> modo write(escrita); se o arquivo existir será sobrescrito, caso contrário será criado.
        # enconding="utf-8" garante que o arquivo use a decodificação UTF-8(Suporte a acentos e caracteres especiais)
        # as f cria uma variável temporária para interagir com o arquivo aberto
        with open(caminho, "w", encoding="utf-8") as f:

            # json.dump() é uma função da biblioteca json. Ela converte o conteúdo dados em texto JSON e grava diretamente no arquivo f
            # indent=4 formata o JSON com indentação de 4 espaços
            # ensure_ascii permite caractéres acentuados
            # Python percorre dados recursivamente se for lista ou dicionários e converte cada tipo no seu equivalente JSON
            # e grava o texto no arquivo
            json.dump(dados, f, indent=4, ensure_ascii=False)
        print(f"Dados salvos em: {caminho}")

    # OSError caputura qualquer erro relacionado ao sistema operacional e guarda o objeto do erro na variável
    except OSError as e:
        print(f"Erro ao salvar arquivo JSON: {e}")


def main():
    resultado = []
    for p in PLANETAS:
        dados = fetch_planeta(p)

        
        #      # DEBUG: inspecionar resposta crua da API
        # print(f"\n--- DEBUG: {p} ---")
        # if dados is None:
        #     print("Resposta: None ou erro na requisição")
        #     continue
        # print("Status keys:", list(dados.keys())[:20])
        # print("englishName:", dados.get("englishName"))
        # print("mass raw:", dados.get("mass"))
        # print("semimajorAxis:", dados.get("semimajorAxis"))
        # print("sideralOrbit:", dados.get("sideralOrbit"))
        # # opcional: salvar uma amostra em arquivo para inspeção
        # with open(f"debug_{p}.json", "w", encoding="utf-8") as f:
        #     import json
        #     json.dump(dados, f, indent=2, ensure_ascii=False)

        planeta = parse_planeta(dados)
        


        if planeta:
            resultado.append(planeta)

    if resultado: 
        salvar_json(resultado)
    else:
        print("Nenhum dado válido coletado.")

# Quando é executado um arquivo python diretamente, python define a varíavel interna do script __name__ como "__main__"
# Porém se o arquivo for importado __name__ recebe o nome do arquivo.
# Evita que o main() seja executado por engano
if __name__ == "__main__":

    # Chama a função main
    main()

# Flask é uma clase da biblioteca flask que representa o servidor Web
# Flask usa o nome para determinar internamente a pasta base da aplicação
app = Flask(__name__)

# __file__ representa armazena o caminho completo do arquivo atual.
# os.path.dirname() pega apenas o diretório atual da aplicação
# os.path.join() junta esse diretório com o arquivo
ARQUIVO_JSON = os.path.join(os.path.dirname(__file__), "planetas.json")


def carregar_json(filename=ARQUIVO_JSON):

    # Verificação da existência do arquivo
    if not os.path.exists(filename):
        return []
    
    try:

        # with() garante que o arquivo será fechado automaticamente após a leitura
        with open(filename, "r", encoding="utf-8") as f:

            # Lê o conteúdo do arquivo e converte de texto JSON para objeto Python
            return json.load(f)
        
    except (OSError, json.JSONDecodeError):
        return []

# Essa linha é um decorador em Python. Um decorador é uma função especial que modifica o comportamento de outra função sem precisar alterar o código interno dela.
# Ou seja, o Flask usa decoradores para associar URLs a funções Python.
# Sintaxe: @app.route(<Rota>, methods=<Métodos HTTP permitidos>)

# @ indica que a linha seguinte é um decorador aplicado à função que vem logo abaixo.
# App é um objeto WSGI application, compatível com servidores HTTP Python, e serve como o ponto de entrada backend
# route() é um método interno do objeto Flask que registra rotas na aplicação.
# O primeiro argumento de route() é o caminho da URL
# O parâmetro methods indica quais métodos HTTP essa rota aceita.
@app.route("/planetas", methods=["GET"])

# Retorna todos os planetas salvos em JSON
def listar_planetas():
    dados = carregar_json()

    if not dados:
        # jsonify é uma função do Flask que converte objetos Python (como dicionários) em uma resposta de formato JSON
        # Conversão para JSON: A função pega os dados em formato Python, como dicionários ou listas, e os serializa (converte)
        # em uma string JSON.
        # Criação de resposta: Retorna um objeto de resposta do Flask que pode ser enviado de volta para o cliente.
        # Configuração automática: jsonify também define automaticamente as informações necessárias nos cabeçalhos da resposta
        # como o Content-Type para application/json e o código de status HTTP
        return jsonify({"erro": "Nenhum dado disponível. Atualize os dados."}), 404
    
    return jsonify(dados)

# O primeiro argumento de route() pode utilizar rotas dinâmicas onde <nome> vira um parâmetro de rota passado à função
@app.route("/planetas/<nome>", methods=["GET"])

# Retorna informações de um planeta específico
def obter_planeta(nome):
    
    dados = carregar_json()
    nome_lower = nome.lower()
    for p in dados:

        if p["nome"].lower() == nome_lower:
            return jsonify(p)
        
    return jsonify({"erro": f"Planeta '{nome}' não encontrado."}), 404

# Cria uma rota chamada "Atualizar" que só aceita requisições POST. Essa rota vai atualizar o JSON local com dados novos
# de uma API externa
@app.route("/atualizar", methods=["POST"])
def atualizar_dados():
    # Atualiza os dados dos planetas a partir da API externa
    resultado = []

    for p in PLANETAS:
        dados = fetch_planeta(p)
        planeta = parse_planeta(dados)

        if planeta:
            resultado.append(planeta)

    if resultado:
        salvar_json(resultado)
        return jsonify({"mensagem": "Dados atualizados com sucesso.", "total": len(resultado)})
    
    else:

        return jsonify({"erro": "Falha ao atualizar dados."}), 500

if __name__ == "__main__":
    # Executa o servidor Flask localmente
    # debug=True ativa o modo de depuração
    # host="0.0.0.0" faz o servidor aceitar conexões de qualquer IP da rede local
    # port=5000 define a porta onde a API ficará disponível
    app.run(debug=True, host="0.0.0.0", port=5000)