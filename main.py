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
    
    # AJUSTE: Reduzi o offset para max 50 para garantir resultados
    # A Wiki retorna 50 resultados por vez. O offset muda a pagina.
    offset = random.randint(0, 50)
    
    # Termos de busca: "Phocidae" (Focas) OU "Grey seal" OU "Harbor seal"
    # filetype:bitmap garante que vem imagem (jpg/png) e não PDF ou som
    search_term = "Phocidae|Grey seal|Harbor seal|Elephant seal"
    
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={search_term} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=50&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    print(f"Buscando na Wiki com offset {offset}...")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]:
                    print("Wiki retornou vazio.")
                    return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for page_id in pages:
                    page = pages[page_id]
                    if "imageinfo" in page:
                        url_imagem = page["imageinfo"][0]["url"]
                        # Filtra apenas formatos de imagem comuns
                        if url_imagem.endswith(('.jpg', '.jpeg', '.png')):
                             imagens_candidatas.append(url_imagem)
                
                if not imagens_candidatas:
                    return None

                random.shuffle(imagens_candidatas)
                
                for img in imagens_candidatas:
                    if img not in links_usados:
                        return img
                        
                # Se todas forem repetidas, retorna a primeira mesmo assim para não falhar
                return imagens_candidatas[0]
                
        except Exception as e:
            print(f"Erro: {e}")
            return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está ONLINE e ATUALIZADO (Wiki V2)!')

@bot.command()
async def foca(ctx):
    # Avisa o Discord que estamos "digitando" (ajuda a saber se o bot travou)
    async with ctx.typing():
        imagem_url = await buscar_foca_wikipedia()
        
        if imagem_url:
            await ctx.send(imagem_url)
            salvar_historico(imagem_url)
            print(f"Sucesso: {imagem_url}")
        else:
            await ctx.send("Não achei nenhuma foca nesse mergulho... Tente de novo rapidinho!")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
