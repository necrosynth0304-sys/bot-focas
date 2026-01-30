import discord
from discord.ext import commands
from discord.ui import Button, View
import aiohttp
import json
import random
import os
import io # Necessário para lidar com o arquivo da imagem
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
    
    headers = {'User-Agent': 'FocaBotEducation/8.0'}
    
    # Pede a imagem já redimensionada (800px) para ser mais rápido o download
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=30&gsroffset={offset}&format=json"
        f"&prop=imageinfo&iiprop=url&iiurlwidth=800"
    )

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
                    # Pega a versão thumb (leve)
                    url_img = info.get("thumburl", info.get("url"))
                    
                    if url_img and eh_imagem_segura(url_img) and url_img not in links_usados:
                        imagens_candidatas.append(url_img)
                
                if not imagens_candidatas: return None
                return random.choice(imagens_candidatas)
        except Exception as e:
            print(f"Erro busca: {e}")
            return None

async def enviar_foca_com_upload(destination, view=None):
    """
    Função mágica que baixa a imagem e faz upload para o Discord.
    Serve tanto para o comando !foca quanto para o botão.
    """
    imagem_url = await buscar_foca_wikipedia()
    
    # Lógica de tentativas
    if imagem_url is None: imagem_url = await buscar_foca_wikipedia()
    if imagem_url is None: imagem_url = random.choice(BACKUP_FOCAS)
    
    salvar_historico(imagem_url)
    
    # Tenta baixar a imagem
    async with aiohttp.ClientSession() as session:
        async with session.get(imagem_url) as resp:
            if resp.status == 200:
                # Lê os dados da imagem na memória
                data = await resp.read()
                arquivo_imagem = io.BytesIO(data)
                
                # Cria o arquivo para o Discord
                arquivo = discord.File(arquivo_imagem, filename="foca.jpg")
                
                # Cria o Embed e "aponta" para o arquivo que acabamos de criar
                embed = discord.Embed(title="🦭 Aqui está sua foca!", color=0x3498db)
                embed.set_image(url="attachment://foca.jpg") # Segredo: attachment://
                embed.set_footer(text="Imagem enviada via Upload Seguro")
                
                # Envia tudo junto: Embed + Arquivo + Botão
                if view:
                    await destination.send(file=arquivo, embed=embed, view=view)
                else:
                    await destination.send(file=arquivo, embed=embed)
            else:
                await destination.send("Falha ao baixar a foca :(", view=view)

# --- BOTÕES ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        # Defere a interação para ganhar tempo de download
        await interaction.response.defer()
        # Usa interaction.followup para enviar a nova mensagem
        await enviar_foca_com_upload(interaction.followup, BotaoFocaView())

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online! MODO UPLOAD ATIVADO.')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        # Usa a mesma função de upload para o comando
        await enviar_foca_com_upload(ctx, BotaoFocaView())

keep_alive.keep_alive()
bot.run(TOKEN)
