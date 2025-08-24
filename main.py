from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import psycopg2
import os
import urllib.parse

# Modelo para os dados que a API vai receber
class Resposta(BaseModel):
    nome: str
    idade: int
    peso: float
    altura: float
    doenca_cronica: bool

# Conexão com o banco usando DATABASE_URL
def connect():
    db_url = os.getenv("DATABASE_URL")
    if db_url is None:
        raise Exception("Variável DATABASE_URL não está definida")

    result = urllib.parse.urlparse(db_url)

    return psycopg2.connect(
        dbname=result.path[1:],  # remove a barra inicial
        user=result.username,
        password=result.password,
        host=result.hostname,
        port=result.port
    )

# Criar a aplicação FastAPI
app = FastAPI()

# Habilitar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Em produção, especifique os domínios confiáveis
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Endpoint para servir o formulário HTML
@app.get("/", response_class=HTMLResponse)
def serve_form():
    with open("form.html", "r", encoding="utf-8") as f:
        return f.read()

# Endpoint para inserir dados
@app.post("/responder/")
def responder(resposta: Resposta):
    try:
        conn = connect()
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO questionario_saude (nome, idade, peso, altura, doenca_cronica)
            VALUES (%s, %s, %s, %s, %s)
        """, (resposta.nome, resposta.idade, resposta.peso, resposta.altura, resposta.doenca_cronica))
        conn.commit()
        cur.close()
        conn.close()
        return {"status": "ok", "mensagem": f"Obrigado, {resposta.nome}! Seus dados foram registrados com sucesso."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Endpoint para listar dados
@app.get("/respostas/")
def listar_respostas():
    conn = connect()
    cur = conn.cursor()
    cur.execute("SELECT nome, idade, peso, altura, doenca_cronica FROM questionario_saude")
    rows = cur.fetchall()
    cur.close()
    conn.close()

    respostas = []
    for row in rows:
        respostas.append({
            "nome": row[0],
            "idade": row[1],
            "peso": row[2],
            "altura": row[3],
            "doenca_cronica": row[4]
        })

    return respostas