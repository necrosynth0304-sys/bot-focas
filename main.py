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
    "Harp seal pup", "Pagophilus groenlandicus pup", "Weddell seal face",
    "Leptonychotes weddellii", "Saimaa ringed seal", "Pusa hispida saimensis",
    "Baikal seal face", "Funny seal", "Baby seal rolling", "Spotted seal pup",
    "Seal waving", "Fat seal", "Cute seal"
]

# --- LISTA NEGRA (Anti-Fóssil) ---
PALAVRAS_PROIBIDAS = [
    "fossil", "skeleton", "skull", "bone", "museum", "taxidermy", 
    "map", "diagram", "drawing", "sketch", "art", "illustration", "anatomy"
]

# --- BACKUP PREMIUM (Imagens HD Garantidas) ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/800px-Harp_seal_pup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/800px-Weddell_Seal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/800px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/3/30/Monachus_schauinslandi_midway_closeup.jpg/800px-Monachus_schauinslandi_midway_closeup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/0/06/Leopard_Seal_%28Hydrurga_leptonyx%29.jpg/800px-Leopard_Seal_%28Hydrurga_leptonyx%29.jpg"
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
    url_lower = url.lower()
    for proibida in PALAVRAS_PROIBIDAS:
        if proibida in url_lower: return False
    return True

async def buscar_foca_wikipedia():
    links_usados = carregar_historico()
    termo = random.choice(TERMOS_FOFOS)
    offset = random.randint(0, 15)
    
    headers = {'User-Agent': 'FocaBotEducation/7.0'}
    
    # MUDANÇA CRUCIAL AQUI: &iiurlwidth=800
    # Isso pede para a Wiki entregar uma versão .JPG de 800px, perfeita para o Discord
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=30&gsroffset={offset}&format=json"
        f"&prop=imageinfo&iiprop=url&iiurlwidth=800"
    )

    print(f"Buscando: {termo} (Solicitando Thumbnail)")

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]: return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for pid in pages:
                    info = pages[pid].get("imageinfo", [{}])[0]
                    
                    # Prioriza a 'thumburl' (versão leve) se existir, senão pega a 'url' original
                    url_img = info.get("thumburl", info.get("url"))
                    
                    if url_img and eh_imagem_segura(url_img) and url_img not in links_usados:
                        imagens_candidatas.append(url_img)
                
                if not imagens_candidatas: return None
                return random.choice(imagens_candidatas)
        except Exception as e:
            print(f"Erro: {e}")
            return None

# --- CRIAÇÃO DO EMBED ---
def criar_embed(url_imagem):
    embed = discord.Embed(title="🦭 Aqui está sua foca!", color=0x3498db)
    embed.set_image(url=url_imagem)
    embed.set_footer(text="Imagem gerada via Wikimedia Commons")
    return embed

# --- BOTÕES E COMANDOS ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        
        nova_imagem = None
        for _ in range(3):
            nova_imagem = await buscar_foca_wikipedia()
            if nova_imagem: break
            
        if nova_imagem is None: nova_imagem = random.choice(BACKUP_FOCAS)
            
        salvar_historico(nova_imagem)
        embed_novo = criar_embed(nova_imagem)
        
        await interaction.followup.send(embed=embed_novo, view=BotaoFocaView())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online com FIX DE IMAGEM!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await buscar_foca_wikipedia()
        
        if imagem_url is None: imagem_url = await buscar_foca_wikipedia()
        if imagem_url is None: imagem_url = random.choice(BACKUP_FOCAS)

        salvar_historico(imagem_url)
        embed_inicial = criar_embed(imagem_url)
        
        await ctx.send(embed=embed_inicial, view=BotaoFocaView())

keep_alive.keep_alive()
bot.run(TOKEN)
