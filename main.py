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
    if len(historico) > 500:
        historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def buscar_foca_wikipedia():
    """
    Busca imagens reais e científicas de focas no Wikimedia Commons.
    """
    links_usados = carregar_historico()
    
    # Sorteia um "ponto de partida" aleatório nos resultados (0 a 500)
    # Isso garante que cada vez pegamos uma foca diferente no meio das milhares que existem
    offset = random.randint(0, 500)
    
    # URL da API da Wikipédia (Wikimedia Commons)
    # gsrsearch=Phocidae|Pinniped -> Busca pela família das focas
    # gsrnamespace=6 -> Apenas arquivos de mídia (imagens)
    # prop=imageinfo&iiprop=url -> Queremos o link direto da imagem
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch=Phocidae|Pinniped filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=5&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    print(f"Erro na API Wiki: {resp.status}")
                    return None
                
                data = await resp.json()
                
                # O JSON da wiki é meio complexo, precisamos navegar nele
                if "query" not in data or "pages" not in data["query"]:
                    print("Nenhuma foca encontrada nesse offset.")
                    return None
                
                pages = data["query"]["pages"]
                
                # Lista de possíveis imagens retornadas
                imagens_candidatas = []
                
                for page_id in pages:
                    page = pages[page_id]
                    if "imageinfo" in page:
                        url_imagem = page["imageinfo"][0]["url"]
                        # Filtra para garantir que é imagem comum (jpg, png)
                        if url_imagem.endswith(('.jpg', '.jpeg', '.png', '.gif')):
                             imagens_candidatas.append(url_imagem)
                
                # Embaralha as candidatas
                random.shuffle(imagens_candidatas)
                
                for img in imagens_candidatas:
                    if img not in links_usados:
                        return img
                        
                return "REPETIDO"
                
        except Exception as e:
            print(f"Erro técnico: {e}")
            return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está conectado na Wikipédia!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await buscar_foca_wikipedia()

        # Tentativa extra se der erro ou repetido
        if imagem_url == "REPETIDO" or imagem_url is None:
            print("Tentando segunda busca...")
            imagem_url = await buscar_foca_wikipedia()
        
        if imagem_url and imagem_url != "REPETIDO":
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Enviada: {imagem_url}")
        else:
            # Se falhar mesmo assim, enviamos uma foca de emergência (link fixo)
            await ctx.send("As focas selvagens estão escondidas... Aqui vai uma clássica:")
            await ctx.send("https://upload.wikimedia.org/wikipedia/commons/2/25/Saimaa_Ringed_Seal_Phoca_hispida_saimensis.jpg")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
