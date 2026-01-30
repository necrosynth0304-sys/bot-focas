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
    # Mantém o histórico com no máximo 500 links para não pesar
    if len(historico) > 500:
        historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def buscar_foca_blindada():
    """
    Usa o LoremFlickr com tags científicas para evitar confusão.
    """
    links_usados = carregar_historico()
    
    # Gera um número aleatório para "quebrar o cache" e forçar imagem nova
    seed = random.randint(1, 99999999)
    
    # URL MELHORADA:
    # harp+seal = Foca da Groenlândia
    # phocidae = Nome científico da família das focas (garante que é animal)
    # marine+mammal = Mamífero marinho
    url_base = f"https://loremflickr.com/800/600/harp+seal,phocidae,marine+mammal?random={seed}"

    async with aiohttp.ClientSession() as session:
        # allow_redirects=True segue o link até a imagem real (.jpg)
        async with session.get(url_base, allow_redirects=True) as resp:
            if resp.status == 200:
                # O site redireciona para a URL final da imagem
                url_final = str(resp.url)
                
                # Verificação de repetição
                if url_final in links_usados:
                    return "REPETIDO"
                
                return url_final
            else:
                return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        # Tenta pegar a imagem
        imagem_url = await buscar_foca_blindada()

        # Se vier repetida, o bot tenta mais uma vez sozinho (segunda chance)
        if imagem_url == "REPETIDO":
            imagem_url = await buscar_foca_blindada()
        
        # Se deu certo e não é repetida
        if imagem_url and imagem_url != "REPETIDO":
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Enviada: {imagem_url}")
        else:
            await ctx.send("A foca fugiu... Tente de novo!")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive() # Mantém vivo na Koyeb
bot.run(TOKEN) # Inicia o bot
