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
USER_AGENT = 'FocaBot/16.0 (HighRes 720p Edition)'
LARGURA_ALVO = 720  # Resolução solicitada

# --- FONTE 1: CATEGORIAS CIENTÍFICAS (WIKIPEDIA) ---
CATEGORIAS_WIKI = [
    "Category:Phocidae_pups",
    "Category:Pagophilus_groenlandicus_pups", # Harpa
    "Category:Pusa_hispida_saimensis",        # Saimaa (Gordinha)
    "Category:Leptonychotes_weddellii_faces", # Weddell (Sorrindo)
    "Category:Phoca_vitulina_resting",
    "Category:Swimming_Phocidae"
]

# --- FONTE 2: UNSPLASH (Lista Curada HD) ---
# O parâmetro &w=720 obriga o servidor deles a entregar em 720p
LINKS_UNSPLASH = [
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=720",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=720",
    "https://images.unsplash.com/photo-1596700811968-3e4b1022831d?q=80&w=720",
    "https://images.unsplash.com/photo-1596850849929-a1c9752d50a2?q=80&w=720",
    "https://images.unsplash.com/photo-1621774332247-925762da2921?q=80&w=720",
    "https://images.unsplash.com/photo-1520668478635-c598dc21564f?q=80&w=720",
    "https://images.unsplash.com/photo-1526487672230-67a57a091497?q=80&w=720",
    "https://images.unsplash.com/photo-1458944510526-7876a4413156?q=80&w=720"
]

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
    """Busca URL na Wiki forçando largura de 720px"""
    links_usados = carregar_historico()
    categoria = random.choice(CATEGORIAS_WIKI)
    
    # iiurlwidth=720 -> O segredo do 720p na Wiki
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
                    # Pega o thumburl (que virá com 720px)
                    if "thumburl" in info:
                        link = info["thumburl"]
                        if link.endswith(('.jpg', '.jpeg')) and link not in links_usados:
                            candidatas.append(link)
                
                return random.choice(candidatas) if candidatas else None
    except: return None

async def download_seguro(url):
    """
    Baixa a imagem e verifica se ela é válida (Anti-Fantasma).
    Retorna (BytesIO, Tamanho) ou (None, 0).
    """
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}) as resp:
                if resp.status == 200:
                    data = await resp.read()
                    
                    # VERIFICAÇÃO CRÍTICA: Se baixou 0 bytes, é fantasma.
                    if len(data) == 0:
                        print("Alerta: Download de 0 bytes detectado.")
                        return None
                    
                    return io.BytesIO(data)
                else:
                    print(f"Erro HTTP: {resp.status}")
                    return None
    except Exception as e:
        print(f"Erro Download: {e}")
        return None

async def enviar_foca_720p(destination, view=None):
    # 1. Decide a fonte (50% Wiki, 50% Unsplash para variar e garantir velocidade)
    if random.random() > 0.5:
        url = await obter_url_wiki_720p()
        fonte_nome = "Wiki (720p)"
    else:
        url = random.choice(LINKS_UNSPLASH)
        fonte_nome = "Unsplash (720p)"
    
    # Se a Wiki falhar, cai pro Unsplash (que é garantido)
    if not url:
        url = random.choice(LINKS_UNSPLASH)
        fonte_nome = "Unsplash Backup"
        
    salvar_historico(url)
    
    # 2. Tenta Baixar (Validação Anti-Fantasma)
    arquivo_bytes = await download_seguro(url)
    
    # Se falhar o download da primeira opção, tenta o Backup IMEDIATAMENTE
    if arquivo_bytes is None:
        print("Download falhou. Tentando backup seguro...")
        url = random.choice(LINKS_UNSPLASH)
        arquivo_bytes = await download_seguro(url) # Tenta baixar o backup
        fonte_nome = "Backup de Emergência"

    # 3. Envio
    if arquivo_bytes:
        # Gera nome aleatório para quebrar cache do Discord
        nome_arquivo = f"foca_720p_{random.randint(1000, 9999)}.jpg"
        discord_file = discord.File(arquivo_bytes, filename=nome_arquivo)
        
        embed = discord.Embed(title="🦭 Foca em 720p", color=0x3498db)
        embed.set_image(url=f"attachment://{nome_arquivo}")
        embed.set_footer(text=f"Fonte: {fonte_nome} | Status: Verificado ✅")
        
        try:
            if view:
                await destination.send(file=discord_file, embed=embed, view=view)
            else:
                await destination.send(file=discord_file, embed=embed)
        except Exception as e:
            print(f"Erro ao enviar pro Discord: {e}")
            # Se der erro de envio, manda só o link como último recurso
            await destination.send(f"Erro no upload, mas aqui está: {url}", view=view)
    else:
        # Se TUDO falhar (internet caiu na Koyeb), manda mensagem de erro
        await destination.send("A conexão com o oceano caiu... Tente novamente em 5 segundos.", view=view)

# --- BOTÕES ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        await interaction.response.defer()
        await enviar_foca_720p(interaction.followup, BotaoFocaView())

# --- INIT ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online. Modo 720p + Anti-Fantasma ativado.')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        await enviar_foca_720p(ctx, BotaoFocaView())

keep_alive.keep_alive()
if TOKEN: bot.run(TOKEN)
