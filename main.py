import discord
from discord.ext import commands
import aiohttp
import json
import random
import os
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ['DISCORD_TOKEN']
HISTORICO_FILE = "historico_focas.json"

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
    # Mantém o histórico limpo (últimas 500)
    if len(historico) > 500:
        historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def buscar_foca_blindada():
    """
    Usa o LoremFlickr para pegar imagens sem levar bloqueio.
    """
    links_usados = carregar_historico()
    
    # Gera um número aleatório para "forçar" o site a dar uma imagem nova
    seed = random.randint(1, 9999999)
    
    # URL Mágica: Pede uma imagem de foca (seal) de 800x600 pixels
    # O parametro ?lock= ajuda a variar a imagem
    url_base = f"https://loremflickr.com/800/600/seal?lock={seed}"

    async with aiohttp.ClientSession() as session:
        # allow_redirects=True é o segredo. O site redireciona para a foto real (jpg)
        async with session.get(url_base, allow_redirects=True) as resp:
            if resp.status == 200:
                # Pegamos o link final da imagem (ex: flickr.com/foto123.jpg)
                url_final = str(resp.url)
                
                # Se por um acaso cair uma repetida, avisamos o bot
                if url_final in links_usados:
                    return "REPETIDO"
                
                return url_final
            else:
                return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online e pronto!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        # Tenta pegar a imagem
        imagem_url = await buscar_foca_blindada()

        # Lógica de tentativa (se der repetido, tenta mais uma vez na hora)
        if imagem_url == "REPETIDO":
            imagem_url = await buscar_foca_blindada()
        
        if imagem_url and imagem_url != "REPETIDO":
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Enviada: {imagem_url}")
        else:
            await ctx.send("As focas estão tímidas... Tente novamente em alguns segundos!")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
