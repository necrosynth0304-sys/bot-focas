import discord
from discord.ext import commands
import aiohttp
import json
import random
import os
import keep_alive
import os

# --- CONFIGURAÇÃO ---
TOKEN = os.environ['DISCORD_TOKEN']
HISTORICO_FILE = "historico_focas.json"
SUBREDDIT_URL = "https://www.reddit.com/r/seals/hot.json?limit=100"

# Configuração dos Intents (Permissões do Bot)
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES DE LÓGICA (O Cérebro) ---

def carregar_historico():
    """Lê o arquivo de histórico para saber quais imagens já foram usadas."""
    if not os.path.exists(HISTORICO_FILE):
        return []
    with open(HISTORICO_FILE, "r") as f:
        return json.load(f)

def salvar_historico(link):
    """Adiciona um novo link ao histórico e salva no arquivo."""
    historico = carregar_historico()
    historico.append(link)
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def pegar_foca_da_internet():
    """
    Vai até o Reddit, pega 100 posts e tenta achar um que não esteja no histórico.
    """
    # 1. Carrega a memória do bot
    links_usados = carregar_historico()
    
    # User-Agent é como o bot se apresenta para o site (importante para não ser bloqueado)
    headers = {'User-Agent': 'FocaBot/1.0 (by seunome)'}

    async with aiohttp.ClientSession() as session:
        async with session.get(SUBREDDIT_URL, headers=headers) as resp:
            if resp.status != 200:
                return None # Erro ao acessar a internet

            data = await resp.json()
            posts = data['data']['children']

            # Filtra apenas o que é imagem (jpg, png, gif)
            imagens_candidatas = []
            for post in posts:
                url = post['data']['url']
                if url.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                    imagens_candidatas.append(url)

            # --- A LÓGICA DO "NUNCA REPETIR" ---
            random.shuffle(imagens_candidatas) # Embaralha as cartas
            
            for imagem in imagens_candidatas:
                if imagem not in links_usados:
                    # ACHAMOS! É uma imagem nova.
                    return imagem
            
            # Se o loop acabar e não achar nada, todas as 100 já foram usadas.
            return "ESGOTADO"

# --- COMANDO DO BOT ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online e pronto para distribuir focas!')

@bot.command()
async def foca(ctx):
    # Avisa que está pensando (opcional, mas bom para UX)
    async with ctx.typing():
        imagem_url = await pegar_foca_da_internet()

        if imagem_url is None:
            await ctx.send("Minhas conexões com o oceano falharam... Tente de novo.")
        
        elif imagem_url == "ESGOTADO":
            # Aqui você poderia limpar o histórico ou buscar de outro subreddit
            await ctx.send("Caramba! Você já viu TODAS as focas recentes. Espere novas postagens!")
        
        else:
            # Envia a foca e salva na memória
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Imagem enviada e salva: {imagem_url}")

keep_alive.keep_alive() # Inicia o servidor web
bot.run(TOKEN) # Inicia o bot

