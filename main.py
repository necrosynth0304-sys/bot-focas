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

# --- LISTA DE TERMOS PARA VARIAR AS FOTOS ---
# O bot vai sortear um desses termos para buscar na Wikipédia
TERMOS_VARIADOS = [
    "Harp seal pup",        # Foca bebê peluda
    "Phoca vitulina",       # Foca comum
    "Funny seal",           # Foca engraçada (pode vir memes da wiki)
    "Sleeping seal",        # Foca dormindo
    "Grey seal face",       # Rosto de foca cinza
    "Leopard seal",         # Foca leopardo
    "Weddell seal",         # Foca de Weddell (aquelas gordinhas)
    "Elephant seal",        # Elefante marinho
    "Monachus",             # Foca-monge
    "Baby seal ice"         # Foca no gelo
]

# --- LISTA DE BACKUP (FOTOS HD GARANTIDAS) ---
# Se a busca falhar, ele pega uma dessas. Adicionei mais fotos bonitas.
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/2/25/Saimaa_Ringed_Seal_Phoca_hispida_saimensis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Phoca_vitulina_at_hirtshals_oceanarium.jpg/1024px-Phoca_vitulina_at_hirtshals_oceanarium.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Harbor_Seal_at_Monterey_Bay.jpg/1024px-Harbor_Seal_at_Monterey_Bay.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Leopard_Seal_%28Hydrurga_leptonyx%29.jpg/1024px-Leopard_Seal_%28Hydrurga_leptonyx%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg/1024px-Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/1024px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/1024px-Weddell_Seal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Monachus_schauinslandi_midway_closeup.jpg/1024px-Monachus_schauinslandi_midway_closeup.jpg",
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=1000", # Foca do Unsplash
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=1000",
    "https://images.unsplash.com/photo-1550953686-3536067888b6?q=80&w=1000"
]

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES ---

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
    links_usados = carregar_historico()
    
    # 1. Escolhe um termo aleatório da nossa lista (Variedade!)
    termo_escolhido = random.choice(TERMOS_VARIADOS)
    
    # 2. Escolhe uma "página" aleatória (0 a 20)
    offset = random.randint(0, 20)
    
    print(f"Buscando por: '{termo_escolhido}' na página {offset}")

    headers = {
        'User-Agent': 'FocaBotEducation/2.0 (bot_discord_estudos; contato@exemplo.com)'
    }
    
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo_escolhido} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=20&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200:
                    return None
                
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]:
                    return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for page_id in pages:
                    page = pages[page_id]
                    if "imageinfo" in page:
                        url_imagem = page["imageinfo"][0]["url"]
                        # Filtro reforçado de extensão
                        if url_imagem.lower().endswith(('.jpg', '.jpeg', '.png')):
                             imagens_candidatas.append(url_imagem)
                
                if not imagens_candidatas:
                    return None

                random.shuffle(imagens_candidatas)
                
                for img in imagens_candidatas:
                    if img not in links_usados:
                        return img
                        
                return imagens_candidatas[0]
                
        except Exception as e:
            print(f"Erro: {e}")
            return None

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está pronto e com vocabulário expandido!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        # Tenta a Wiki com o termo aleatório
        imagem_url = await buscar_foca_wikipedia()
        
        # Se falhar, tenta mais uma vez (às vezes é sorte)
        if imagem_url is None:
            imagem_url = await buscar_foca_wikipedia()

        # Se falhar DE NOVO, usa o Backup HD
        if imagem_url is None:
            print("Usando backup de emergência...")
            imagem_url = random.choice(BACKUP_FOCAS)

        await ctx.send(imagem_url)
        salvar_historico(imagem_url)
        print(f"Enviada: {imagem_url}")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
