import discord
from discord.ext import commands
from discord.ui import Button, View
import random
import os
import keep_alive

# --- CONFIGURAÇÃO ---
TOKEN = os.environ.get('DISCORD_TOKEN')

# --- O BANCO DE FOCAS (A Lista Mágica) ---
# Estas imagens estão hospedadas no Unsplash.
# O final "?w=600" garante que venham leves e rápidas.
FOCAS_PREMIUM = [
    # -- BEBÊS (Focas Brancas) --
    "https://images.unsplash.com/photo-1596501170388-72439369d12d?w=600",
    "https://images.unsplash.com/photo-1596700811968-3e4b1022831d?w=600",
    "https://images.unsplash.com/photo-1621774332247-925762da2921?w=600",
    "https://images.unsplash.com/photo-1622349326084-3b2d73352745?w=600",
    "https://images.unsplash.com/photo-1596850849929-a1c9752d50a2?w=600",
    
    # -- ENGRAÇADAS / ROSTOS --
    "https://images.unsplash.com/photo-1550953686-2533df870f70?w=600", # Sorrindo
    "https://images.unsplash.com/photo-1592336332158-4c3797c5552b?w=600", # Bigodes
    "https://images.unsplash.com/photo-1514336021669-e70d4948a432?w=600", # Olhando pra cima
    "https://images.unsplash.com/photo-1458944510526-7876a4413156?w=600", # Bocejando
    
    # -- GORDINHAS / NA ÁGUA --
    "https://images.unsplash.com/photo-1520668478635-c598dc21564f?w=600",
    "https://images.unsplash.com/photo-1526487672230-67a57a091497?w=600",
    "https://images.unsplash.com/photo-1588661803738-8c5443a571f5?w=600",
    "https://images.unsplash.com/photo-1553335017-c866d997b69c?w=600",
    "https://images.unsplash.com/photo-1549480376-793540e1b997?w=600",
    "https://images.unsplash.com/photo-1526253457597-c8340d828a2b?w=600",
    "https://images.unsplash.com/photo-1610996886475-4704040a45d0?w=600",
    
    # -- VIBE DE PRAIA --
    "https://images.unsplash.com/photo-1552064973-206e2338c239?w=600",
    "https://images.unsplash.com/photo-1582236894050-093228a0e9c8?w=600",
    "https://images.unsplash.com/photo-1601673892706-03c004d80365?w=600"
]

intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

# --- SISTEMA SIMPLES ---

class BotaoFocaView(View):
    def __init__(self):
        super().__init__(timeout=None)

    @discord.ui.button(label="Mais uma!", style=discord.ButtonStyle.primary, emoji="🔄")
    async def botao_callback(self, interaction: discord.Interaction, button: Button):
        # Sorteia da lista
        imagem = random.choice(FOCAS_PREMIUM)
        
        embed = discord.Embed(title="🦭 Foca!", color=0x3498db)
        embed.set_image(url=imagem)
        
        # Responde editando ou enviando nova (usamos response.send_message para nova)
        await interaction.response.send_message(embed=embed, view=BotaoFocaView())

@bot.event
async def on_ready():
    print(f'Bot {bot.user} online. Modo Otimizado (Sem bugs).')

@bot.command()
async def foca(ctx):
    # Sorteia da lista
    imagem = random.choice(FOCAS_PREMIUM)
    
    embed = discord.Embed(title="🦭 Foca!", color=0x3498db)
    embed.set_image(url=imagem)
    
    await ctx.send(embed=embed, view=BotaoFocaView())

keep_alive.keep_alive()
if TOKEN: bot.run(TOKEN)
