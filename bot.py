import discord
from discord.ext import commands
from discord import ui
import json
import os
import asyncio

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("TOKEN not configured!")
    exit()

DATA_FILE = "data.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    try:
        if not os.path.exists(DATA_FILE):
            return {"produtos": {}, "loja_channel": None, "produto_canais": {}}
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"produtos": {}, "loja_channel": None, "produto_canais": {}}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(member):
    return any(r.name == "Admin" for r in member.roles)

class PainelLoja(ui.View):
    def __init__(self, produtos):
        super().__init__(timeout=None)
        for pid, dados in produtos.items():
            btn = ui.Button(
                label=f"💰 COMPRAR {dados['nome']} - {dados['preco']}", 
                custom_id=f"comprar_{pid}", 
                style=discord.ButtonStyle.success,
                emoji="🛒"
            )
            self.add_item(btn)

@bot.tree.command(name="ping")
async def ping(interaction):
    await interaction.response.send_message(f"Bot online! Latencia: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="sync")
async def sync(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    await bot.tree.sync()
    await interaction.response.send_message("Comandos sincronizados!", ephemeral=True)

@bot.tree.command(name="loja")
async def loja(interaction):
    data = load_data()
    
    embed = discord.Embed(
        title="╔══════════════════════════════════╗\n║        🛒  LOJA VIRTUAL  🛒        ║\n╚══════════════════════════════════╝",
        description="**Bem-vindo!**\nEscolha seu produto:\n",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    
    if data["produtos"]:
        for pid, d in data["produtos"].items():
            embed.add_field(name=f"📦 {d['nome']}", value=f"💰 {d['preco']}\n{d['desc'][:60]}", inline=False)
    else:
        embed.add_field(name="Sem produtos", value="Nenhum produto", inline=False)
    
    embed.set_footer(text="Clique em COMPRAR")
    
    view = PainelLoja(data["produtos"])
    await interaction.response.send_message(embed=embed, view=view, ephemeral=True)

@bot.tree.command(name="loja-canal")
async def loja_canal(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    
    data = load_data()
    data["loja_channel"] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Canal definido: {canal.mention}", ephemeral=True)

@bot.tree.command(name="enviar-loja")
async def enviar_loja(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    
    data = load_data()
    canal_id = data.get("loja_channel")
    if not canal_id:
        await interaction.response.send_message("Use /loja-canal primeiro", ephemeral=True)
        return
    
    canal = bot.get_channel(int(canal_id))
    if not canal:
        await interaction.response.send_message("Canal nao encontrado.", ephemeral=True)
        return
    
    embed = discord.Embed(
        title="╔═══════════════════════════════════════╗\n║     🛒🛒🛒  LOJA VIRTUAL  🛒🛒🛒      ║\n╚═══════════════════════════════════════╝",
        description="**Escolha abaixo:**\n",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    
    for pid, d in data["produtos"].items():
        embed.add_field(name=f"📦 {d['nome']}", value=f"💰 **{d['preco']}**\n{d['desc'][:80]}", inline=False)
    
    embed.set_footer(text="Clique no botao para comprar")
    
    view = PainelLoja(data["produtos"])
    await canal.send(embed=embed, view=view)
    await interaction.response.send_message(f"Enviado para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="add-produto")
async def add_produto(interaction, nome: str, preco: str, canal: discord.TextChannel, *, desc: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    
    data = load_data()
    pid = str(len(data["produtos"]) + 1)
    data["produtos"][pid] = {"nome": nome, "preco": preco, "desc": desc}
    data["produto_canais"][pid] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Produto '{nome}' adicionado!", ephemeral=True)

@bot.tree.command(name="lista-produtos")
async def lista_produtos(interaction):
    if not is_admin(interaction.user):
        return
    data = load_data()
    e = discord.Embed(title="Lista Produtos", color=discord.Color.blurple())
    for pid, d in data["produtos"].items():
        e.add_field(name=f"ID {pid}", value=f"{d['nome']} - {d['preco']}")
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="remove-produto")
async def remove_produto(interaction, pid: str):
    if not is_admin(interaction.user):
        return
    data = load_data()
    if pid in data["produtos"]:
        nome = data["produtos"][pid]["nome"]
        del data["produtos"][pid]
        save_data(data)
        await interaction.response.send_message(f"Produto '{nome}' removido!", ephemeral=True)
    else:
        await interaction.response.send_message("Nao encontrado.", ephemeral=True)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        if not custom_id.startswith("comprar_"):
            return
        
        pid = custom_id.replace("comprar_", "")
        data = load_data()
        prod = data["produtos"].get(pid)
        
        if not prod:
            return
        
        user = interaction.user
        guild = interaction.guild
        
        try:
            await interaction.response.defer()
            canal = await guild.create_text_channel(f"compra-{user.name}")
            await canal.set_permissions(user, view_channel=True, send_messages=True)
            await canal.set_permissions(guild.default_role, view_channel=False)
            
            embed = discord.Embed(title="Confirmacao", color=discord.Color.green())
            embed.add_field(name="Produto", value=prod["nome"], inline=True)
            embed.add_field(name="Preco", value=prod["preco"], inline=True)
            embed.add_field(name="Descricao", value=prod["desc"], inline=False)
            
            await canal.send(content=f"{user.mention}", embed=embed)
            await canal.send("ENVIE O COMPROVANTE PIX!")
            await interaction.followup.send("Canal criado!", ephemeral=True)
        except Exception as e:
            try:
                await interaction.followup.send(f"Erro: {str(e)}", ephemeral=True)
            except:
                pass

async def sync_commands():
    await bot.wait_until_ready()
    while not bot.is_closed():
        await bot.tree.sync()
        await asyncio.sleep(30)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    await bot.tree.sync()
    print("Comandos sincronizados!")
    bot.loop.create_task(sync_commands())

if __name__ == "__main__":
    bot.run(TOKEN)
