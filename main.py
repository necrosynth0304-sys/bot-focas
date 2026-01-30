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
USER_AGENT = 'FocaBotEducation/13.0 (Scientific Filter)'
MAX_DOWNLOAD_SIZE = 10 * 1024 * 1024 # 10MB limit

# --- CATEGORIAS CIENTÍFICAS (Blindagem Total) ---
# Em vez de pesquisar texto, o bot vai entrar nestas "gavetas" da Wikipédia.
# É biologicamente impossível ter um corvo ou uma carta aqui dentro.
CATEGORIAS_SEGURAS = [
    "Category:Phocidae_pups",                 # Filhotes de focas (Geral)
    "Category:Pagophilus_groenlandicus_pups", # Filhotes de Foca-harpa (As brancas fofas)
    "Category:Pusa_hispida_saimensis",        # Foca-anelada-de-saimaa (Gordinhas e raras)
    "Category:Leptonychotes_weddellii_faces", # Rostos de Foca-de-weddell (As sorridentes)
    "Category:Phoca_vitulina_resting",        # Foca-comum descansando
    "Category:Swimming_Phocidae",             # Focas nadando
    "Category:Halichoerus_grypus_pups"        # Filhotes de Foca-cinzenta
]

# --- BACKUP HÍBRIDO (Garantia de Fofura HD) ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/640px-Harp_seal_pup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/640px-Weddell_Seal.jpg",
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=800",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=800",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/640px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES AUXILIARES ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE): return []
    try: with open(HISTORICO_FILE, "r") as f: return json.load(f)
    except: return []

def salvar_historico(link):
    historico = carregar_historico()
    if link in historico: return
    historico.append(link)
    if len(historico) > 600: historico.pop(0)
    try: with open(HISTORICO_FILE, "w") as f: json.dump(historico, f)
    except: pass

# --- NÚCLEO DE BUSCA CIENTÍFICA ---

async def buscar_foca_cientifica():
    links_usados = carregar_historico()
    # Escolhe uma categoria biológica segura
    categoria = random.choice(CATEGORIAS_SEGURAS)
    
    # NOVA URL DA API:
    # action=query
    # generator=categorymembers -> Lista membros de uma categoria
    # gcmtitle={categoria} -> Nome da categoria
    # gcmtype=file -> Só queremos arquivos (imagens)
    # gcmlimit=50 -> Pega 50 opções
    # gcmshuffle=1 -> Embaralha os resultados na fonte (Variedade!)
    # prop=imageinfo&iiprop=url&iiurlwidth=640 -> Pede a URL do thumbnail de 640px
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
                if resp.status != 200: return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]: return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for pid in pages:
                    info = pages[pid].get("imageinfo", [{}])[0]
                    
                    # Prioriza a versão thumb (leve)
                    if "thumburl" in info:
                        url_img = info["thumburl"]
                        # Filtro final: Apenas JPG/JPEG
                        if url_img.lower().endswith(('.jpg', '.jpeg')) and url_img not in links_usados:
                            imagens_candidatas.append(url_img)
                
                if not imagens_candidatas: return None
                # Como a API já embaralhou com gcmshuffle=1, pegamos a primeira disponível
                return imagens_candidatas[0]
    except Exception as e:
        print(f"Erro Científico: {e}")
        return None

# --- NÚCLEO DE ENVIO (Upload > Embed) ---

async def enviar_foca_blindada(destination, view=None):
    imagem_url = await buscar_foca_cientifica()
    
    # Retry
    if imagem_url is None: imagem_url = await buscar_foca_cientifica()
    # Fallback
    if imagem_url is None: imagem_url = random.choice(BACKUP_FOCAS)
    
    salvar_historico(imagem_url)

    # --- PLANO A: UPLOAD ---
    try:
        timeout_dl = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout_dl) as session:
            async with session.get(imagem_url) as resp:
                if resp.status == 200:
                    tamanho = int(resp.headers.get('Content-Length', 0))
                    if tamanho < MAX_DOWNLOAD_SIZE:
                        data = await resp.read()
                        arquivo_imagem = io.BytesIO(data)
                        arquivo = discord.File(arquivo_imagem, filename="foca_cientifica.jpg")
                        
                        embed = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
                        embed.set_image(url="attachment://foca_cientifica.jpg")
                        embed.set_footer(text="Fonte: Categoria Científica (Wiki)")
                        
                        await destination.send(file=arquivo, embed=embed, view=view)
                        return
    except Exception: pass

    # --- PLANO B: LINK EMBED ---
    try:
        embed = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
        embed.set_image(url=imagem_url)
        await destination.send(embed=embed, view=view)
    except:
        await destination.send(f"Foca fugiu: {imagem_url}", view=view)

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
    print(f'Bot {bot.user} online! MODO CIENTÍFICO ATIVADO.')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        await enviar_foca_blindada(ctx, BotaoFocaView())

keep_alive.keep_alive()
if TOKEN: bot.run(TOKEN)
