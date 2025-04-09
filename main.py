import re # Para validação básica de formato do CPF
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field, field_validator
import uvicorn # Import uvicorn para rodar o app programaticamente se desejar

app = FastAPI(
    title="API de Validação de Cadastro e Termos",
    description="Uma API de exemplo para validar CPF, dados cadastrais e aceite de termos.",
    version="1.0.0"
)

# --- Mock de Banco de Dados ---
# Em uma aplicação real, você buscaria/salvaria esses dados em um banco de dados.
db_mock = {
    "79349171988": {"nome_completo": "Fulano de Tal Silva", "email": "fulano.silva@email.com", "aceitou_termos": False, "pontuacao" : "4500"},
    "89540115604": {"nome_completo": "Ciclana Souza", "email": "c.souza@email.net", "aceitou_termos": True, "pontuacao" : "2100"},
    "21874323518": {"nome_completo": "Beltrano Oliveira", "email": "beltrano@mail.org", "aceitou_termos": False, "pontuacao" : "230"},
}

# --- Modelos Pydantic para Request Body ---

class TermoPayload(BaseModel):
    """Modelo para o corpo da requisição do endpoint ValidaTermo."""
    cpf: str = Field(..., description="CPF do usuário (somente números)", examples=["11122233344"])
    aceitou: bool = Field(..., description="Flag indicando se o usuário aceitou os termos (true/false)")

    @field_validator('cpf')
    def validate_cpf_format(cls, v):
        """Valida se o CPF contém apenas 11 dígitos numéricos."""
        if not re.match(r'^\d{11}$', v):
            raise ValueError('CPF deve conter exatamente 11 dígitos numéricos.')
        return v

# --- Funções Auxiliares ---

def validar_cpf_logica(cpf: str) -> bool:
    """
    Função de validação de CPF (SIMPLIFICADA).
    IMPORTANTE: Esta é uma validação MUITO básica apenas para o exemplo.
    Uma validação real deve verificar os dígitos verificadores.
    Bibliotecas como 'validate-docbr' podem ser usadas para isso.
    """
    # Remove caracteres não numéricos (caso venham com máscara)
    cpf_numeros = re.sub(r'\D', '', cpf)

    # Verifica se tem 11 dígitos
    if len(cpf_numeros) != 11:
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11), que são inválidos
    if len(set(cpf_numeros)) == 1:
        return False

    # Adicione aqui a lógica de validação dos dígitos verificadores se necessário
    # Exemplo simples: para este mock, consideramos válido se existir no nosso 'banco'
    # return cpf_numeros in db_mock # Poderia ser uma regra de negócio específica

    # Para este exemplo genérico, vamos retornar True se passou nas verificações básicas.
    # Em um cenário real, implemente a validação completa dos dígitos verificadores.
    return True


# --- Endpoints da API ---

@app.get("/valida-cpf/{cpf}", tags=["Validação"])
async def valida_cpf_endpoint(cpf: str):
    """
    Valida se um CPF é potencialmente válido (formato e regras básicas).
    Retorna `{"valido": True}` ou `{"valido": False}`.
    *Nota: A validação implementada é simplificada.*
    """
    cpf_limpo = re.sub(r'\D', '', cpf) # Garante que só números sejam validados
    if len(cpf_limpo) != 11:
         return {"valido": False} # Formato inválido antes mesmo da lógica

    eh_valido = validar_cpf_logica(cpf_limpo)
    return {"valido": eh_valido}

@app.get("/valida-cadastro/{cpf}", tags=["Cadastro"])
async def valida_cadastro_endpoint(cpf: str):
    """
    Busca os dados cadastrais de um usuário pelo CPF.
    Retorna Nome completo, email e se aceitou os termos.
    Levanta um erro 404 se o CPF não for encontrado.
    """
    cpf_limpo = re.sub(r'\D', '', cpf)
    if len(cpf_limpo) != 11:
         raise HTTPException(status_code=400, detail="Formato de CPF inválido. Use 11 dígitos.")

    usuario = db_mock.get(cpf_limpo)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuário com CPF {cpf_limpo} não encontrado.")

    return {
        "nome_completo": usuario["nome_completo"],
        "email": usuario["email"],
        "aceitou_termos": usuario["aceitou_termos"]
    }

@app.get("/termos", tags=["Termos"])
async def get_termos_endpoint():
    """
    Retorna o link para o documento de termos de uso (PDF).
    """
    # Exemplo de link público para um PDF qualquer
    link_exemplo = "https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf"
    # Em um caso real, este link viria de uma configuração ou banco de dados.
    return {"link_termos": link_exemplo}

@app.post("/valida-termo", tags=["Termos"])
async def valida_termo_endpoint(payload: TermoPayload):
    """
    Registra o aceite (ou não aceite) dos termos de uso para um determinado CPF.
    Entrada: JSON com "cpf" (string, 11 dígitos) e "aceitou" (boolean).
    Retorna `{"status": "OK"}` em caso de sucesso.
    Levanta um erro 404 se o CPF não for encontrado no cadastro.
    """
    # A validação do formato do CPF e do tipo do 'aceitou' é feita pelo Pydantic (TermoPayload)
    cpf = payload.cpf # Já validado pelo Pydantic para ser 11 dígitos
    aceitou = payload.aceitou

    usuario = db_mock.get(cpf)
    if not usuario:
        raise HTTPException(status_code=404, detail=f"Usuário com CPF {cpf} não encontrado para atualizar termos.")

    # Atualiza o status no nosso 'banco de dados' mock
    db_mock[cpf]["aceitou_termos"] = aceitou
    print(f"Status de aceite dos termos atualizado para CPF {cpf}: {aceitou}") # Log no servidor

    return {"status": "OK"}

# NOVO Endpoint para validar o token
@app.post("/validar-token", tags=["Catálogo"], response_model=dict)
async def validar_token_endpoint(payload: TokenPayload):
    """
    Valida se o token fornecido é igual ao token fixo "1234".
    Retorna status 200 com {"valido": True} se correto.
    Levanta erro 400 (Bad Request) se o token estiver incorreto.
    """
    token_recebido = payload.token
    token_correto = "1234" # Token fixo para validação

    print(f"Recebido token para validação: '{token_recebido}'") # Log para debug

    if token_recebido == token_correto:
        print("Token VÁLIDO.")
        return {"valido": True, "status": "Token correto"} # Retorna 200 OK por padrão
    else:
        print("Token INVÁLIDO.")
        # Levanta uma exceção HTTP que resultará em status 400
        raise HTTPException(status_code=400, detail="Token inválido fornecido.")

# Endpoint para retornar o link do catálogo (chamado após validação bem-sucedida)
@app.get("/acessar-catalogo", tags=["Catálogo"], response_model=dict)
async def acessar_catalogo_endpoint():
    """ Retorna o link de acesso ao catálogo. """
    link_catalogo = "https://www.google.com/" # Link genérico fixo
    print("Endpoint /acessar-catalogo chamado.")
    return {"link_catalogo": link_catalogo}

# --- Para rodar o servidor (se executar este arquivo diretamente) ---
if __name__ == "__main__":
    # Use a porta 8000 como padrão, mas pode ser alterada
    uvicorn.run(app, host="127.0.0.1", port=8000)