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
            return {"produtos": {}, "loja_channel": None}
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {"produtos": {}, "loja_channel": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(member):
    return any(r.name == "Admin" for r in member.roles)

class LojasButton(ui.Button):
    def __init__(self, pid, nome, preco):
        super().__init__(
            label=f"💰 COMPRAR {nome} - {preco}",
            custom_id=f"comprar_{pid}",
            style=discord.ButtonStyle.success
        )
        self.pid = pid
        self.nome = nome
        self.preco = preco

    async def callback(self, interaction):
        pid = self.custom_id.replace("comprar_", "")
        data = load_data()
        prod = data["produtos"].get(pid)
        
        if prod:
            user = interaction.user
            guild = interaction.guild
            
            try:
                await interaction.response.defer()
                canal = await guild.create_text_channel(f"compra-{user.name}")
                await canal.set_permissions(user, view_channel=True, send_messages=True)
                await canal.set_permissions(guild.default_role, view_channel=False)
                
                embed = discord.Embed(title="Confirmacao de Compra", color=discord.Color.green())
                embed.add_field(name="Produto", value=prod["nome"])
                embed.add_field(name="Preco", value=prod["preco"])
                embed.add_field(name="Descricao", value=prod["desc"])
                
                await canal.send(content=f"{user.mention}", embed=embed)
                await canal.send("ENVIE O PIX!")
                await interaction.followup.send("Canal Criado!", ephemeral=True)
            except:
                await interaction.followup.send("Erro!", ephemeral=True)

@bot.tree.command(name="ping", description="Verifica se o bot esta online")
async def ping(interaction):
    await interaction.response.send_message(f"Online! {round(bot.latency*1000)}ms")

@bot.tree.command(name="loja", description="Mostra a loja virtual")
async def cmd_loja(interaction):
    data = load_data()
    embed = discord.Embed(title="LOJA VIRTUAL", description="Escolha:", color=discord.Color.gold())
    for pid, d in data["produtos"].items():
        embed.add_field(name=d["nome"], value=f"{d['preco']} - {d['desc'][:50]}")
    
    view = ui.View()
    for pid, d in data["produtos"].items():
        view.add_item(LojasButton(pid, d["nome"], d["preco"]))
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="loja-canal", description="Define canal da loja")
async def cmd_loja_canal(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    data["loja_channel"] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Canal: {canal.mention}", ephemeral=True)

@bot.tree.command(name="enviar-loja", description="Envia loja para o canal")
async def cmd_enviar_loja(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    canal = bot.get_channel(int(data.get("loja_channel", 0)))
    if not canal:
        await interaction.response.send_message("Canal nao definido", ephemeral=True)
        return
    
    embed = discord.Embed(title="LOJA VIRTUAL", description="Escolha:", color=discord.Color.gold())
    for pid, d in data["produtos"].items():
        embed.add_field(name=d["nome"], value=f"{d['preco']}")
    
    view = ui.View()
    for pid, d in data["produtos"].items():
        view.add_item(LojasButton(pid, d["nome"], d["preco"]))
    
    await canal.send(embed=embed, view=view)
    await interaction.response.send_message("Enviado!", ephemeral=True)

@bot.tree.command(name="add-produto", description="Adiciona produto")
async def cmd_add_produto(interaction, nome: str, preco: str, canal: discord.TextChannel, *, desc: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    pid = str(len(data["produtos"]) + 1)
    data["produtos"][pid] = {"nome": nome, "preco": preco, "desc": desc}
    save_data(data)
    await interaction.response.send_message(f"Produto {nome} adicionado!", ephemeral=True)

@bot.tree.command(name="lista-produtos", description="Lista produtos")
async def cmd_lista_produtos(interaction):
    if not is_admin(interaction.user):
        return
    data = load_data()
    for pid, d in data["produtos"].items():
        await interaction.response.send_message(f"{pid}. {d['nome']} - {d['preco']}", ephemeral=True)

@bot.tree.command(name="remove-produto", description="Remove produto")
async def cmd_remove_produto(interaction, pid: str):
    if not is_admin(interaction.user):
        return
    data = load_data()
    if pid in data["produtos"]:
        del data["produtos"][pid]
        save_data(data)
        await interaction.response.send_message("Removido!", ephemeral=True)

@bot.tree.command(name="sync", description="Sincroniza comandos")
async def cmd_sync(interaction):
    if not is_admin(interaction.user):
        return
    await bot.tree.sync()
    await interaction.response.send_message("Sincronizado!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    await bot.tree.sync()
    print("Pronto!")

if __name__ == "__main__":
    bot.run(TOKEN)
