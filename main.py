import discord
from discord.ext import commands
import aiohttp
import json
import random
import os
import keep_alive # Importa o nosso sistema anti-sono

# --- CONFIGURAÇÃO ---
# Pega o Token direto das configurações da Koyeb (Segurança máxima)
TOKEN = os.environ['DISCORD_TOKEN']

HISTORICO_FILE = "historico_focas.json"
SUBREDDIT_URL = "https://www.reddit.com/r/seals/hot.json?limit=100"

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES DE LÓGICA ---

def carregar_historico():
    """Lê o arquivo de histórico para saber quais imagens já foram usadas."""
    if not os.path.exists(HISTORICO_FILE):
        return []
    with open(HISTORICO_FILE, "r") as f:
        try:
            return json.load(f)
        except json.JSONDecodeError:
            return [] # Se o arquivo estiver corrompido, retorna lista vazia

def salvar_historico(link):
    """Adiciona um novo link ao histórico e salva no arquivo."""
    historico = carregar_historico()
    historico.append(link)
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def pegar_foca_da_internet():
    """
    Vai até o Reddit fingindo ser um navegador Chrome e pega imagens.
    """
    links_usados = carregar_historico()
    
    # --- A MÁGICA DA CAMUFLAGEM ---
    # Esse cabeçalho faz o Reddit achar que somos um usuário normal no Chrome
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }

    async with aiohttp.ClientSession() as session:
        async with session.get(SUBREDDIT_URL, headers=headers) as resp:
            # Se der erro (ex: 429 ou 403), avisa no log
            if resp.status != 200:
                print(f"Erro ao acessar Reddit: Código {resp.status}")
                return None

            try:
                data = await resp.json()
                posts = data['data']['children']
            except:
                print("Erro ao ler o JSON do Reddit")
                return None

            # Filtra apenas o que é imagem
            imagens_candidatas = []
            for post in posts:
                # O .get previne erros se o post não tiver url
                url = post['data'].get('url', '')
                if url.endswith(('.jpg', '.png', '.gif', '.jpeg')):
                    imagens_candidatas.append(url)

            # --- LÓGICA DO "NUNCA REPETIR" ---
            random.shuffle(imagens_candidatas) 
            
            for imagem in imagens_candidatas:
                if imagem not in links_usados:
                    # ACHAMOS! É uma imagem nova.
                    return imagem
            
            # Se acabar o loop e não achar nada
            return "ESGOTADO"

# --- COMANDOS DO BOT ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está online e camuflado!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await pegar_foca_da_internet()

        if imagem_url is None:
            await ctx.send("Minhas conexões com o oceano falharam... (Erro de acesso ao Reddit)")
        
        elif imagem_url == "ESGOTADO":
            await ctx.send("Caramba! Você já viu TODAS as focas recentes. Espere novas postagens no Reddit!")
        
        else:
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Foca enviada: {imagem_url}")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive() # Mantém o bot acordado na Koyeb
bot.run(TOKEN) # Liga o bot
