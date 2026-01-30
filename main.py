import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import json
import random
import os
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ['DISCORD_TOKEN']
HISTORICO_FILE = "historico_focas.json"

# --- LISTA VIP (Busca apenas espécies fofas/engraçadas) ---
TERMOS_FOFOS = [
    "Harp seal pup",         # A clássica foca branca de pelúcia
    "Pagophilus groenlandicus pup", # Nome científico da foca branca
    "Weddell seal face",     # Aquela que parece estar sorrindo
    "Leptonychotes weddellii", # Nome científico da sorridente
    "Saimaa ringed seal",    # A foca mais gorda e redonda que existe
    "Pusa hispida saimensis", # Nome científico da gordinha
    "Baikal seal face",      # Foca com olhos gigantes
    "Funny seal",            # Memes
    "Baby seal rolling"      # Foca rolando
]

# --- LISTA NEGRA (O Filtro Anti-Fóssil) ---
# Se o link tiver qualquer uma dessas palavras, o bot ignora.
PALAVRAS_PROIBIDAS = [
    "fossil", "skeleton", "skull", "bone", "museum", "taxidermy", 
    "map", "diagram", "drawing", "sketch", "art", "illustration",
    "dead", "carcass", "hunting", "skin", "anatomy", "chart"
]

# --- BACKUP PREMIUM (Imagens HD Garantidas) ---
# Se a busca falhar, ele usa essas aqui que eu selecionei a dedo.
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/2/25/Saimaa_Ringed_Seal_Phoca_hispida_saimensis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/1024px-Weddell_Seal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/1024px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Leopard_Seal_%28Hydrurga_leptonyx%29.jpg/1024px-Leopard_Seal_%28Hydrurga_leptonyx%29.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/e/e0/Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg/1024px-Pusa_hispida_ladogensis_-_Ladoga_Seal_-_Ladogaseehund.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Monachus_schauinslandi_midway_closeup.jpg/1024px-Monachus_schauinslandi_midway_closeup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/800px-Harp_seal_pup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/a/a2/Pusa_sibirica_Baikal_seal_3.jpg/800px-Pusa_sibirica_Baikal_seal_3.jpg"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE): return []
    with open(HISTORICO_FILE, "r") as f:
        try: return json.load(f)
        except: return []

def salvar_historico(link):
    historico = carregar_historico()
    historico.append(link)
    if len(historico) > 500: historico.pop(0) 
    with open(HISTORICO_FILE, "w") as f: json.dump(historico, f)

def eh_imagem_segura(url):
    """Verifica se a imagem tem palavras proibidas (ossos, mapas, etc)"""
    url_lower = url.lower()
    for proibida in PALAVRAS_PROIBIDAS:
        if proibida in url_lower:
            return False # Imagem ruim detectada
    return True # Imagem aprovada

async def buscar_foca_wikipedia():
    links_usados = carregar_historico()
    termo = random.choice(TERMOS_FOFOS)
    offset = random.randint(0, 10) # Busca nas primeiras páginas onde estão as melhores fotos
    
    headers = {'User-Agent': 'FocaBotEducation/5.0'}
    
    # Busca por imagens (bitmap)
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=30&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    print(f"Buscando: {termo} (Anti-Fóssil Ativado)")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]: return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for pid in pages:
                    if "imageinfo" in pages[pid]:
                        url_img = pages[pid]["imageinfo"][0]["url"]
                        
                        # FILTRAGEM RIGOROSA
                        # 1. Tem que ser JPG/PNG
                        # 2. NÃO pode ter palavras proibidas (fossil, map, etc)
                        # 3. NÃO pode ter sido usada recentemente
                        if (url_img.lower().endswith(('.jpg', '.jpeg', '.png')) and 
                            eh_imagem_segura(url_img) and 
                            url_img not in links_usados):
                                imagens_candidatas.append(url_img)
                
                if not imagens_candidatas: return None
                
                return random.choice(imagens_candidatas)
                
        except Exception as e:
            print(f"Erro: {e}")
            return None

# --- BOTÕES E COMANDOS ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        # Tenta buscar 3 vezes para garantir que acha algo bom
        nova_imagem = None
        for _ in range(3):
            nova_imagem = await buscar_foca_wikipedia()
            if nova_imagem: break
            
        if nova_imagem is None:
            nova_imagem = random.choice(BACKUP_FOCAS)
            
        salvar_historico(nova_imagem)
        await interaction.followup.send(content=nova_imagem, view=BotaoFocaView())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online! Filtro de fofura ativado.')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await buscar_foca_wikipedia()
        
        # Se a primeira busca falhar ou trouxer lixo filtrado, tenta de novo
        if imagem_url is None:
            imagem_url = await buscar_foca_wikipedia()
        
        # Se falhar tudo, Backup
        if imagem_url is None:
            imagem_url = random.choice(BACKUP_FOCAS)

        salvar_historico(imagem_url)
        await ctx.send(content=imagem_url, view=BotaoFocaView())

keep_alive.keep_alive()
bot.run(TOKEN)
