import discord
from discord.ext import commands
import json
import random
import os
import asyncio
from duckduckgo_search import AsyncDDGS # A nova biblioteca de busca
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ['DISCORD_TOKEN']
HISTORICO_FILE = "historico_focas.json"

# Termos de busca para variar as imagens (para não vir sempre as mesmas)
TERMOS_BUSCA = [
    "cute seal", "foca fofa", "baby seal", "funny seal", 
    "seal meme", "foca engraçada", "seal face", "harp seal"
]

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES DE LÓGICA ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE):
        return []
    with open(HISTORICO_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return []

def salvar_historico(link):
    historico = carregar_historico()
    historico.append(link)
    # Mantém o histórico com no máximo 500 links para não ficar gigante
    if len(historico) > 500:
        historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def buscar_foca_web():
    """
    Usa o DuckDuckGo para buscar imagens de focas na web.
    """
    links_usados = carregar_historico()
    termo = random.choice(TERMOS_BUSCA) # Escolhe um termo aleatório

    print(f"Buscando na web por: {termo}...")
    
    try:
        # Busca 20 imagens sobre o termo
        results = await AsyncDDGS().images(termo, region="wt-wt", safesearch="off", max_results=20)
        
        # O DuckDuckGo retorna uma lista de dicionários. Queremos só a URL da imagem.
        imagens_candidatas = [r['image'] for r in results]
        
        random.shuffle(imagens_candidatas)

        for imagem in imagens_candidatas:
            if imagem not in links_usados:
                return imagem
        
        return "REPETIDO" # Se todas as 20 já foram usadas (raro)

    except Exception as e:
        print(f"Erro na busca: {e}")
        return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online e buscando na Web!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await buscar_foca_web()

        if imagem_url is None:
            await ctx.send("Minhas buscas falharam... O DuckDuckGo não respondeu.")
        
        elif imagem_url == "REPETIDO":
            # Se deu azar de pegar só repetida, tenta de novo automaticamente (recursão simples)
            imagem_url = await buscar_foca_web() 
            if imagem_url and imagem_url != "REPETIDO":
                 await ctx.send(imagem_url)
                 salvar_historico(imagem_url)
            else:
                 await ctx.send("Estou vendo muitas focas repetidas, tente de novo em alguns segundos!")
        
        else:
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Enviada: {imagem_url}")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
