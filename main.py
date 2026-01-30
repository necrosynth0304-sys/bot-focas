import discord
from discord.ext import commands
from discord.ui import Button, View # Importação necessária para botões
import aiohttp
import json
import random
import os
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ['DISCORD_TOKEN']
HISTORICO_FILE = "historico_focas.json"

# --- LISTA DE TERMOS FILTRADA (Só Fofura/Gelo/Memes) ---
TERMOS_TOP_TIER = [
    "Harp seal pup",        # Bebê foca (aquelas brancas de pelo)
    "Baby seal ice",        # Bebê no gelo
    "Funny seal face",      # Cara engraçada
    "Laughing seal",        # Foca rindo
    "Chubby seal",          # Foca gorda/redonda
    "Weddell seal",         # Foca sorridente
    "Seal rolling",         # Foca rolando
    "Silly seal",           # Foca boba
    "Pusa hispida",         # Foca anelada
    "Spotted seal pup"      # Filhote manchado
]

# --- BACKUP DE EMERGÊNCIA (Links diretos HD) ---
BACKUP_FOCAS = [
    "https://upload.wikimedia.org/wikipedia/commons/2/25/Saimaa_Ringed_Seal_Phoca_hispida_saimensis.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/1/1a/Weddell_Seal.jpg/1024px-Weddell_Seal.jpg",
    "https://upload.wikimedia.org/wikipedia/commons/thumb/8/80/Grey_Seal_%28Halichoerus_grypus%29_2.jpg/1024px-Grey_Seal_%28Halichoerus_grypus%29_2.jpg",
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?q=80&w=1000",
    "https://images.unsplash.com/photo-1550953686-2533df870f70?q=80&w=1000"
]

# Configuração dos Intents
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- FUNÇÕES DE LÓGICA (Busca e Histórico) ---

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
    termo = random.choice(TERMOS_TOP_TIER)
    # Offset baixo (0-20) garante que pegamos as imagens mais relevantes do topo
    offset = random.randint(0, 20)
    
    # Identificação do bot para a Wikipédia não bloquear
    headers = {'User-Agent': 'FocaBotEducation/4.0 (Discord Bot; contato@seuserver.com)'}
    
    url = (
        f"https://commons.wikimedia.org/w/api.php?"
        f"action=query&generator=search&gsrsearch={termo} filetype:bitmap"
        f"&gsrnamespace=6&gsrlimit=20&gsroffset={offset}&format=json&prop=imageinfo&iiprop=url"
    )

    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(url, headers=headers) as resp:
                if resp.status != 200: return None
                data = await resp.json()
                
                if "query" not in data or "pages" not in data["query"]: return None
                
                pages = data["query"]["pages"]
                imagens = []
                
                for pid in pages:
                    if "imageinfo" in pages[pid]:
                        url_img = pages[pid]["imageinfo"][0]["url"]
                        if url_img.lower().endswith(('.jpg', '.jpeg', '.png')):
                             imagens.append(url_img)
                
                if not imagens: return None
                random.shuffle(imagens)
                
                for img in imagens:
                    if img not in links_usados:
                        return img
                return imagens[0]
                
        except Exception as e:
            print(f"Erro na busca: {e}")
            return None

# --- A CLASSE DO BOTÃO (Aqui acontece a mágica) ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None) # O botão não expira

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        # 1. Avisa o discord que recebemos o clique (para não dar 'Interação falhou')
        await interaction.response.defer()
        
        # 2. Busca nova imagem
        nova_imagem = await buscar_foca_wikipedia()
        if nova_imagem is None:
            nova_imagem = random.choice(BACKUP_FOCAS)
            
        salvar_historico(nova_imagem)
        
        # 3. Manda uma NOVA mensagem com a imagem e UM NOVO BOTÃO
        # Assim cria-se um ciclo infinito de botões
        await interaction.followup.send(content=nova_imagem, view=BotaoFocaView())

# --- COMANDOS ---

@bot.event
async def on_ready():
    print(f'Bot {bot.user} está pronto com sistema de botões v2!')

@bot.command()
async def foca(ctx):
    async with ctx.typing():
        imagem_url = await buscar_foca_wikipedia()
        
        if imagem_url is None:
            imagem_url = random.choice(BACKUP_FOCAS)

        salvar_historico(imagem_url)
        
        # Envia a mensagem acoplando a View (o botão)
        await ctx.send(content=imagem_url, view=BotaoFocaView())

# --- INICIALIZAÇÃO ---
keep_alive.keep_alive()
bot.run(TOKEN)
