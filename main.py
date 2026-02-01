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
# User agent mais "comum" para evitar bloqueios
USER_AGENT = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
LARGURA_ALVO = 720

# --- LISTAS DE IMAGENS ---

CATEGORIAS_WIKI = [
    "Category:Phocidae_pups",
    "Category:Pagophilus_groenlandicus_pups",
    "Category:Pusa_hispida_saimensis",
    "Category:Leptonychotes_weddellii_faces",
    "Category:Phoca_vitulina_resting",
    "Category:Swimming_Phocidae"
]

LINKS_UNSPLASH = [
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=720",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=720",
    "https://images.unsplash.com/photo-1596700811968-3e4b1022831d?q=80&w=720",
    "https://images.unsplash.com/photo-1596850849929-a1c9752d50a2?q=80&w=720",
    "https://images.unsplash.com/photo-1621774332247-925762da2921?q=80&w=720",
    "https://images.unsplash.com/photo-1520668478635-c598dc21564f?q=80&w=720",
    "https://images.unsplash.com/photo-1526487672230-67a57a091497?q=80&w=720",
    "https://images.unsplash.com/photo-1588661803738-8c5443a571f5?q=80&w=720"
]

# Link de emergência absoluta (direto e leve)
LINK_EMERGENCIA = "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/640px-Harp_seal_pup.jpg"

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE): return []
    try:
        with open(HISTORICO_FILE, "r") as f: return json.load(f)
    except: return []

def salvar_historico(link):
    historico = carregar_historico()
    if link in historico: return
    historico.append(link)
    if len(historico) > 600: historico.pop(0)
    try:
        with open(HISTORICO_FILE, "w") as f: json.dump(historico, f)
    except: pass

async def obter_url_wiki_720p():
    links_usados = carregar_historico()
    categoria = random.choice(CATEGORIAS_WIKI)
    
    url = (
        f"https://commons.wikimedia.org/w/api.php?action=query&format=json&generator=categorymembers"
        f"&gcmtitle={categoria}&gcmtype=file&gcmlimit=40&gcmshuffle=1"
        f"&prop=imageinfo&iiprop=url&iiurlwidth={LARGURA_ALVO}"
    )

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}, timeout=5) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                pages = data.get("query", {}).get("pages", {})
                
                candidatas = []
                for pid in pages:
                    info = pages[pid].get("imageinfo", [{}])[0]
                    if "thumburl" in info:
                        link = info["thumburl"]
                        if link.endswith(('.jpg', '.jpeg')) and link not in links_usados:
                            candidatas.append(link)
                return random.choice(candidatas) if candidatas else None
    except: return None

async def download_seguro(url):
    """Tenta baixar a imagem. Retorna bytes ou None."""
    if not url: return None
    try:
        # Aumentei o timeout para 10s para conexões lentas
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    if len(data) > 0:
                        return io.BytesIO(data)
    except:
        pass
    return None

async def enviar_foca_720p(destination, view=None):
    # 1. Escolha da Fonte
    if random.random() > 0.6: # 40% Wiki
        url = await obter_url_wiki_720p()
        fonte_display = "Wikipédia (Biologia)"
    else: # 60% Unsplash (Mais estável e HD)
        url = random.choice(LINKS_UNSPLASH)
        fonte_display = "Unsplash (HD)"
    
    if not url: 
        url = random.choice(LINKS_UNSPLASH)
    
    salvar_historico(url)

    # 2. Tenta Baixar (Plano A)
    arquivo_bytes = await download_seguro(url)

    # 3. Retry no Backup se falhar (Plano B)
    if arquivo_bytes is None:
        print("Download falhou. Tentando Unsplash backup...")
        url = random.choice(LINKS_UNSPLASH)
        fonte_display = "Backup Seguro"
        arquivo_bytes = await download_seguro(url)

    # 4. ENVIO FINAL
    if arquivo_bytes:
        # MODO UPLOAD (Melhor qualidade)
        nome_arquivo = f"foca_{random.randint(1000, 9999)}.jpg"
        discord_file = discord.File(arquivo_bytes, filename=nome_arquivo)
        
        embed = discord.Embed(title="🦭 Foca Chegou!", color=0x3498db)
        embed.set_image(url=f"attachment://{nome_arquivo}")
        embed.set_footer(text=f"Fonte: {fonte_display} | Upload Verificado")
        
        try:
            if view: await destination.send(file=discord_file, embed=embed, view=view)
            else: await destination.send(file=discord_file, embed=embed)
        except Exception as e:
            print(f"Erro envio Discord: {e}")
            # Se der erro no upload, cai para o modo Link
            await destination.send(url, view=view)
            
    else:
        # PLANO C: MODO LINK DIRETO (Sem download)
        # Se não conseguimos baixar, mandamos o link e o Discord que se vire para carregar
        print("Download impossível. Enviando link direto.")
        
        embed = discord.Embed(title="🦭 Foca (Modo Link)", color=0xe74c3c)
        embed.set_image(url=url) # Usa a URL que falhou o download
        embed.set_footer(text="Nota: Modo de conexão lenta ativado")
        
        try:
            if view: await destination.send(embed=embed, view=view)
            else: await destination.send(embed=embed)
        except:
            # Desespero total: Manda o link de emergência
            await destination.send(LINK_EMERGENCIA, view=view)

# --- CONFIGURAÇÃO BOT ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await enviar_foca_720p(interaction.followup, BotaoFocaView())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online. Sistema Anti-Queda ativado.')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        await enviar_foca_720p(ctx, BotaoFocaView())

keep_alive.keep_alive()
if TOKEN: bot.run(TOKEN)
