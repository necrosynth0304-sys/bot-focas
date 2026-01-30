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

# --- LISTA DE EMERGÊNCIA (Caso a Wikipédia falhe) ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/2/25/Saimaa_Ringed_Seal_Phoca_hispida_saimensis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/5/5d/Phoca_vitulina_at_hirtshals_oceanarium.jpg/800px-Phoca_vitulina_at_hirtshals_oceanarium.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/c/c2/Harbor_Seal_at_Monterey_Bay.jpg/800px-Harbor_Seal_at_Monterey_Bay.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/9/9c/Phoca_largha_image.jpg/800px-Phoca_largha_image.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg/800px-Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/2/22/Pusa_sibirica_Baikal_seal_2.jpg/800px-Pusa_sibirica_Baikal_seal_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/800px-Weddell_Seal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Monachus_schauinslandi_midway_closeup.jpg/800px-Monachus_schauinslandi_midway_closeup.jpg"
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
    if len(historico) > 500:
        historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f:
        json.dump(historico, f)

async def buscar_foca_wikipedia():
    """
    Busca imagens na Wikipédia com identificação correta (User-Agent).
    """
    links_usados = carregar_historico()
    
    # Offset menor para garantir resultados (páginas 0 a 10)
    offset = random.randint(0, 10)
    
    # Cabeçalho OBRIGATÓRIO da Wikipédia
    headers = {
        'User-Agent': 'FocaBotEducation/1.0 (bot_estudante_python; contato@exemplo.com)'
    }
    
    # Termo de busca: Phocidae (família das focas)
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch=Phocidae filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=50&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp: # Adicionei o header aqui
                if resp.status != 200:
                    print(f"Erro Wiki: {resp.status}")
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
                        if url_imagem.endswith(('.jpg', '.jpeg', '.png')):
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
    print(f'Bot {bot.user} está online e identificado!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        # 1. Tenta buscar na Wikipédia
        imagem_url = await buscar_foca_wikipedia()
        
        # 2. Se a Wiki falhar, usa o Backup
        if imagem_url is None:
            print("Wiki falhou, usando backup...")
            imagem_url = random.choice(BACKUP_FOCAS)

        # 3. Envia
        await ctx.send(imagem_url)
        salvar_historico(imagem_url)
        print(f"Enviada: {imagem_url}")

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
