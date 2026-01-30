import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import json
import random
import os
import io
import asyncio
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ.get('DISCORD_TOKEN')
HISTORICO_FILE = "historico_focas.json"
USER_AGENT = 'FocaBotEducation/14.0 (Scientific Filter Fixed)'
MAX_DOWNLOAD_SIZE = 10 * 1024 * 1024 

# --- CATEGORIAS CIENTÍFICAS ---
CATEGORIAS_SEGURAS = [
    "Category:Phocidae_pups",
    "Category:Pagophilus_groenlandicus_pups",
    "Category:Pusa_hispida_saimensis",
    "Category:Leptonychotes_weddellii_faces",
    "Category:Phoca_vitulina_resting",
    "Category:Swimming_Phocidae",
    "Category:Halichoerus_grypus_pups"
]

# --- BACKUP ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/640px-Harp_seal_pup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/640px-Weddell_Seal.jpg",
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=800",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=800"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES (Indentações Corrigidas) ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE):
        return []
    try:
        with open(HISTORICO_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def salvar_historico(link):
    historico = carregar_historico()
    if link in historico:
        return
    historico.append(link)
    if len(historico) > 600:
        historico.pop(0)
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico, f)
    except:
        pass

async def buscar_foca_cientifica():
    links_usados = carregar_historico()
    categoria = random.choice(CATEGORIAS_SEGURAS)
    
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&format=json&generator=categorymembers"
        f"&gcmtitle={categoria}&gcmtype=file&gcmlimit=50&gcmshuffle=1"
        f"&prop=imageinfo&iiprop=url&iiurlwidth=640"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}) as resp:
                if resp.status != 200:
                    return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]:
                    return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for pid in pages:
                    info = pages[pid].get("imageinfo", [{}])[0]
                    if "thumburl" in info:
                        url_img = info["thumburl"]
                        if url_img.lower().endswith(('.jpg', '.jpeg')) and url_img not in links_usados:
                            imagens_candidatas.append(url_img)
                
                if not imagens_candidatas:
                    return None
                return random.choice(imagens_candidatas)
    except:
        return None

async def enviar_foca_blindada(destination, view=None):
    imagem_url = await buscar_foca_cientifica()
    if imagem_url is None:
        imagem_url = await buscar_foca_wikipedia_search() # Tenta busca comum se categoria falhar
    if imagem_url is None:
        imagem_url = random.choice(BACKUP_FOCAS)
    
    salvar_historico(imagem_url)

    try:
        timeout_dl = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout_dl) as session:
            async with session.get(imagem_url) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    arquivo_imagem = io.BytesIO(data)
                    arquivo = discord.File(arquivo_imagem, filename="foca_v14.jpg")
                    
                    embed = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
                    embed.set_image(url="attachment://foca_v14.jpg")
                    embed.set_footer(text="Fonte: Filtro Científico")
                    
                    await destination.send(file=arquivo, embed=embed, view=view)
                    return
    except:
        pass

    # Plano B (Link)
    try:
        embed = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
        embed.set_image(url=imagem_url)
        await destination.send(embed=embed, view=view)
    except:
        await destination.send(f"Foca fugiu: {imagem_url}", view=view)

# Função de busca secundária (Caso a categoria esteja vazia)
async def buscar_foca_wikipedia_search():
    url = "https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch=Harp seal pup filetype:bitmap&gsrlimit=20&format=json&prop=imageinfo&iiprop=url&iiurlwidth=640"
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}) as resp:
                data = await resp.json()
                pages = data["query"]["pages"]
                pid = random.choice(list(pages.keys()))
                return pages[pid]["imageinfo"][0]["thumburl"]
    except:
        return None

# --- BOTÕES E COMANDOS ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await enviar_foca_blindada(interaction.followup, BotaoFocaView())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online e corrigido!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        await enviar_foca_blindada(ctx, BotaoFocaView())

keep_alive.keep_alive()
if TOKEN:
    bot.run(TOKEN)
