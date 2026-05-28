import discord
from discord.ext import commands
from discord import ui
import json
import os

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
            return {"produtos": {}, "canal_loja": None}
        with open(DATA_FILE, "r") as f:
            dados = json.load(f)
            if "produtos" not in dados:
                dados["produtos"] = {}
            return dados
    except:
        return {"produtos": {}, "canal_loja": None}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(member):
    return any(r.name == "Admin" for r in member.roles)

class BotaoComprar(ui.Button):
    def __init__(self, pid, nome, preco):
        super().__init__(
            label=f"COMPRAR {nome} - {preco}",
            custom_id=f"comprar_{pid}",
            style=discord.ButtonStyle.success
        )
        self.pid = pid
        self.nome = nome
        self.preco = preco

    async def callback(self, interaction):
        try:
            pid = self.custom_id.replace("comprar_", "")
            data = load_data()
            prod = data["produtos"].get(pid)
            
            if not prod:
                await interaction.response.send_message("Produto nao encontrado!", ephemeral=True)
                return
            
            user = interaction.user
            guild = interaction.guild
            
            await interaction.response.defer()
            
            canal = await guild.create_text_channel(f"compra-{user.name}")
            await canal.set_permissions(user, view_channel=True, send_messages=True)
            await canal.set_permissions(guild.default_role, view_channel=False)
            
            embed = discord.Embed(title="Confirmacao", color=discord.Color.from_rgb(255, 0, 0))
            embed.add_field(name="Produto", value=prod["nome"], inline=True)
            embed.add_field(name="Preco", value=prod["preco"], inline=True)
            embed.add_field(name="Descricao", value=prod["desc"], inline=False)
            
            await canal.send(content=f"{user.mention}", embed=embed)
            await canal.send("Pix: adrianalmarques80@gmail.com")
            
            await interaction.followup.send(f"Carrinho criado em {canal.mention}!", ephemeral=True)
        except Exception as e:
            try:
                await interaction.followup.send(f"Erro: O bot tem permissao para criar canais?", ephemeral=True)
            except:
                pass

def criar_painel():
    data = load_data()
    embed = discord.Embed(
        title="=======LOJA VIRTUAL=======",
        description="Escolha:",
        color=discord.Color.from_rgb(255, 0, 0)
    )
    view = ui.View()
    produtos = data.get("produtos", {})
    
    for pid, d in produtos.items():
        nome = d.get("nome", "Sem nome")
        preco = d.get("preco", "0")
        desc = d.get("desc", "")[:60]
        embed.add_field(name=nome, value=f"{preco} - {desc}")
        view.add_item(BotaoComprar(pid, nome, preco))
    return embed, view

@bot.tree.command(name="ping")
async def ping(interaction):
    await interaction.response.send_message(f"Online! {round(bot.latency*1000)}ms")

@bot.tree.command(name="loja")
async def cmd_loja(interaction):
    embed, view = criar_painel()
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="add-produto")
async def cmd_add_produto(interaction, nome: str, preco: str, canal: discord.TextChannel, *, desc: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    
    data = load_data()
    data["canal_loja"] = str(canal.id)
    pid = str(len(data["produtos"]) + 1)
    data["produtos"][pid] = {"nome": nome, "preco": preco, "desc": desc}
    save_data(data)
    
    embed, view = criar_painel()
    await canal.send(embed=embed, view=view)
    
    await interaction.response.send_message(f"Produto adicionado e enviado para {canal.mention}!", ephemeral=True)

@bot.tree.command(name="loja-canal")
async def cmd_loja_canal(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    data["canal_loja"] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Canal: {canal.mention}", ephemeral=True)

@bot.tree.command(name="enviar-loja")
async def cmd_enviar_loja(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    canal_id = data.get("canal_loja")
    if not canal_id:
        await interaction.response.send_message("Use /loja-canal primeiro", ephemeral=True)
        return
    
    canal = bot.get_channel(int(canal_id))
    if not canal:
        await interaction.response.send_message("Canal invalido", ephemeral=True)
        return
    
    embed, view = criar_painel()
    await canal.send(embed=embed, view=view)
    await interaction.response.send_message("Enviado!", ephemeral=True)

@bot.tree.command(name="lista-produtos")
async def cmd_lista_produtos(interaction):
    if not is_admin(interaction.user):
        return
    data = load_data()
    for pid, d in data["produtos"].items():
        await interaction.response.send_message(f"{pid}. {d['nome']} - {d['preco']}", ephemeral=True)

@bot.tree.command(name="remove-produto")
async def cmd_remove_produto(interaction, pid: str):
    if not is_admin(interaction.user):
        return
    data = load_data()
    if pid in data["produtos"]:
        del data["produtos"][pid]
        save_data(data)
        await interaction.response.send_message("Removido!", ephemeral=True)

@bot.tree.command(name="reset-loja")
async def cmd_reset_loja(interaction):
    if not is_admin(interaction.user):
        return
    data = {"produtos": {}, "canal_loja": None}
    save_data(data)
    await interaction.response.send_message("Loja resetada!", ephemeral=True)

@bot.tree.command(name="sync")
async def cmd_sync(interaction):
    if not is_admin(interaction.user):
        return
    await bot.tree.sync()
    await interaction.response.send_message("Sincronizado!", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
