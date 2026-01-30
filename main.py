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

# --- CONFIGURAÇÃO E CONSTANTES ---
TOKEN = os.environ.get('DISCORD_TOKEN')
HISTORICO_FILE = "historico_focas.json"
MAX_DOWNLOAD_SIZE = 8 * 1024 * 1024  # Limite de 8MB para evitar travar a memória RAM
USER_AGENT = 'FocaBotEducation/11.0 (Discord Bot; contato@seuserver.com)'

# --- LISTA VIP (Termos otimizados para fofura) ---
TERMOS_FOFOS = [
    "Harp seal pup", "Pagophilus groenlandicus pup", "Weddell seal face",
    "Leptonychotes weddellii", "Saimaa ringed seal", "Pusa hispida saimensis",
    "Baikal seal face", "Funny seal", "Baby seal rolling", "Spotted seal pup",
    "Seal waving", "Fat seal", "Cute seal", "Baby seal snow", "Phoca vitulina"
]

# --- LISTA NEGRA (Filtro de Conteúdo) ---
PALAVRAS_PROIBIDAS = [
    "fossil", "skeleton", "skull", "bone", "museum", "taxidermy", 
    "map", "diagram", "drawing", "sketch", "art", "illustration", 
    "anatomy", "dead", "carcass", "hunting", "skin"
]

# --- BACKUP HÍBRIDO (Wiki + Unsplash para redundância real) ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/thumb/6/63/Harp_seal_pup.jpg/640px-Harp_seal_pup.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/640px-Weddell_Seal.jpg",
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=800",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=800",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/640px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg"
]

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- GERENCIAMENTO DE HISTÓRICO (Com proteção contra corrupção) ---

def carregar_historico():
    if not os.path.exists(HISTORICO_FILE): return []
    try:
        with open(HISTORICO_FILE, "r") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        # Se o arquivo estiver corrompido, retorna lista vazia e reseta
        return []

def salvar_historico(link):
    historico = carregar_historico()
    if link in historico: return # Evita duplicatas na lista
    
    historico.append(link)
    if len(historico) > 500: historico.pop(0)
    
    try:
        with open(HISTORICO_FILE, "w") as f:
            json.dump(historico, f)
    except OSError:
        pass # Se falhar ao salvar, não crasha o bot

def eh_imagem_segura(url):
    url_lower = url.lower()
    for proibida in PALAVRAS_PROIBIDAS:
        if proibida in url_lower: return False
    return True

# --- MOTOR DE BUSCA (WIKIPÉDIA) ---

async def buscar_foca_wikipedia():
    links_usados = carregar_historico()
    termo = random.choice(TERMOS_FOFOS)
    offset = random.randint(0, 20)
    
    # URL Otimizada: Pede thumb de 640px (mais leve e rápido que 800px)
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=25&gsroffset={offset}&format=json"
        f"&prop=imageinfo&iiprop=url&iiurlwidth=640"
    )

    try:
        timeout = aiohttp.ClientTimeout(total=4) # Timeout curto para não travar
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, headers={'User-Agent': USER_AGENT}) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]: return None
                
                pages = data["query"]["pages"]
                imagens_candidatas = []
                
                for pid in pages:
                    info = pages[pid].get("imageinfo", [{}])[0]
                    # Só aceita se tiver thumburl (versão leve)
                    if "thumburl" in info:
                        url_img = info["thumburl"]
                        if eh_imagem_segura(url_img) and url_img not in links_usados:
                            imagens_candidatas.append(url_img)
                
                if not imagens_candidatas: return None
                return random.choice(imagens_candidatas)
    except Exception as e:
        print(f"[Log] Erro na busca Wiki: {e}")
        return None

# --- NÚCLEO DE ENVIO (Upload > Embed > Fallback) ---

async def enviar_foca_blindada(destination, view=None):
    # 1. Busca
    imagem_url = await buscar_foca_wikipedia()
    
    # 2. Retry Rápido
    if imagem_url is None: 
        imagem_url = await buscar_foca_wikipedia()
    
    # 3. Backup Final
    if imagem_url is None: 
        imagem_url = random.choice(BACKUP_FOCAS)
    
    salvar_historico(imagem_url)

    # --- PLANO A: UPLOAD (Prioridade) ---
    enviado = False
    try:
        timeout_dl = aiohttp.ClientTimeout(total=6)
        async with aiohttp.ClientSession(timeout=timeout_dl) as session:
            async with session.get(imagem_url) as resp:
                if resp.status == 200:
                    # Verifica tamanho do arquivo (Content-Length)
                    tamanho = int(resp.headers.get('Content-Length', 0))
                    if tamanho < MAX_DOWNLOAD_SIZE:
                        data = await resp.read()
                        arquivo_imagem = io.BytesIO(data)
                        arquivo = discord.File(arquivo_imagem, filename="foca.jpg")
                        
                        embed = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
                        embed.set_image(url="attachment://foca.jpg")
                        embed.set_footer(text="Fonte: Wiki Commons (Upload)")
                        
                        await destination.send(file=arquivo, embed=embed, view=view)
                        enviado = True
                    else:
                        print(f"[Log] Imagem muito grande ignorada: {tamanho} bytes")
    except Exception as e:
        print(f"[Log] Falha no Upload: {e}")

    # --- PLANO B: LINK EMBED (Se upload falhar ou arquivo for grande) ---
    if not enviado:
        try:
            embed_fallback = discord.Embed(title="🦭 Foca entregue!", color=0x3498db)
            embed_fallback.set_image(url=imagem_url)
            embed_fallback.set_footer(text="Fonte: Wiki Commons (Link)")
            await destination.send(embed=embed_fallback, view=view)
        except Exception:
            # --- PLANO C: TEXTO PURO (Desespero) ---
            await destination.send(f"Aqui está: {imagem_url}", view=view)

# --- VIEW DO BOTÃO ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        # Defer evita "A interação falhou" se a internet estiver lenta
        await interaction.response.defer()
        await enviar_foca_blindada(interaction.followup, BotaoFocaView())

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'>>> Bot {bot.user} INICIADO COM SUCESSO <<<')
    print('Sistemas: Wiki Search V11 | Anti-Crash | Botões Async')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        await enviar_foca_blindada(ctx, BotaoFocaView())

# Inicia servidor web e bot
keep_alive.keep_alive()

if TOKEN:
    bot.run(TOKEN)
else:
    print("ERRO CRÍTICO: Token não encontrado nas variáveis de ambiente.")
