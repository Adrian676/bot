import discord
from discord.ext import commands
from discord import ui
import json
import os

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("TOKEN not configured!")
    exit()

ADMIN_ROLE_NAME = "Admin"
PRODUTOS_FILE = "produtos.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_products():
    try:
        if not os.path.exists(PRODUTOS_FILE):
            return {}
        with open(PRODUTOS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_products(data):
    with open(PRODUTOS_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(member):
    return any(r.name == ADMIN_ROLE_NAME for r in member.roles)

@bot.tree.command(name="ping")
async def ping(interaction):
    await interaction.response.send_message(f"Bot online! Latency: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="loja")
async def loja(interaction):
    p = load_products()
    if not p:
        await interaction.response.send_message("Nenhum produto.", ephemeral=True)
        return
    e = discord.Embed(title="Loja Virtual", color=discord.Color.blue())
    for pid, d in p.items():
        e.add_field(name=f"{pid}. {d['nome']}", value=f"{d['preco']} - {d['desc']}")
    view = ui.View()
    for pid, d in p.items():
        btn = ui.Button(label=f"Comprar {d['nome']}", custom_id=f"comprar_{pid}", style=discord.ButtonStyle.green)
        view.add_item(btn)
    await interaction.response.send_message(embed=e, view=view)

@bot.tree.command(name="criar")
async def criar(interaction, nome: str, preco: str, *, desc: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    p = load_products()
    pid = str(len(p) + 1)
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    save_products(p)
    await interaction.response.send_message(f"Produto {nome} criado!", ephemeral=True)

@bot.tree.command(name="produtos")
async def produtos(interaction):
    if not is_admin(interaction.user):
        return
    p = load_products()
    e = discord.Embed(title="Produtos", color=discord.Color.blurple())
    for pid, d in p.items():
        e.add_field(name=f"ID {pid}", value=f"{d['nome']} - {d['preco']}")
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="editar")
async def editar(interaction, pid: str, nome: str, preco: str, *, desc: str):
    if not is_admin(interaction.user):
        return
    p = load_products()
    if pid not in p:
        await interaction.response.send_message("Nao encontrado.", ephemeral=True)
        return
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    save_products(p)
    await interaction.response.send_message("Produto atualizado!", ephemeral=True)

@bot.tree.command(name="excluir")
async def excluir(interaction, pid: str):
    if not is_admin(interaction.user):
        return
    p = load_products()
    if pid not in p:
        await interaction.response.send_message("Nao encontrado.", ephemeral=True)
        return
    nome = p[pid]["nome"]
    del p[pid]
    save_products(p)
    await interaction.response.send_message(f"Produto {nome} excluido!", ephemeral=True)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        cid = interaction.data.get("custom_id", "")
        if cid.startswith("comprar_"):
            pid = cid.replace("comprar_", "")
            p = load_products()
            prod = p.get(pid)
            if prod:
                u = interaction.user
                g = interaction.guild
                try:
                    ch = await g.create_text_channel(f"compra-{u.name}")
                    await ch.set_permissions(u, view_channel=True, send_messages=True)
                    await ch.set_permissions(g.default_role, view_channel=False)
                    e = discord.Embed(title="Nova Compra", color=discord.Color.green())
                    e.add_field(name="Produto", value=prod["nome"])
                    e.add_field(name="Preco", value=prod["preco"])
                    e.add_field(name="Descricao", value=prod["desc"])
                    await ch.send(content=f"{u.mention}", embed=e)
                    await ch.send("Envie o comprovante PIX aqui.")
                    await interaction.response.send_message("Canal criado!", ephemeral=True)
                except:
                    await interaction.response.send_message("Sem permissao.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
