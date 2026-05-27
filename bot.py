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
    def __init__(self, produtos, data):
        super().__init__(timeout=None)
        for pid, dados in produtos.items():
            btn = ui.Button(
                label=f"COMPRAR {dados['nome']} - {dados['preco']}", 
                custom_id=f"comprar_{pid}", 
                style=discord.ButtonStyle.success,
                emoji="🛒"
            )
            self.add_item(btn)

@bot.tree.command(name="ping")
async def ping(interaction):
    await interaction.response.send_message(f"Bot online! Latencia: {round(bot.latency * 1000)}ms")

@bot.tree.command(name="loja")
async def loja(interaction):
    data = load_data()
    
    embed = discord.Embed(
        title="🛒 LOJA VIRTUAL",
        description="Bem-vindo! Escolha seus produtos abaixo:",
        color=discord.Color.from_rgb(88, 101, 242)
    )
    embed.set_footer(text="Loja Virtual - Todos os direitos reservados")
    
    view = PainelLoja(data["produtos"], data)
    
    await interaction.response.send_message(embed=embed, view=view)

@bot.tree.command(name="config-loja")
async def config_loja(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    
    data = load_data()
    data["loja_channel"] = str(canal.id)
    save_data(data)
    
    await interaction.response.send_message(f"Canal da loja definido: {canal.mention}", ephemeral=True)

@bot.tree.command(name="add-produto")
async def add_produto(interaction, nome: str, preco: str, canal: discord.TextChannel, *, desc: str):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao.", ephemeral=True)
        return
    
    data = load_data()
    pid = str(len(data["produtos"]) + 1)
    
    data["produtos"][pid] = {
        "nome": nome,
        "preco": preco,
        "desc": desc
    }
    data["produto_canais"][pid] = str(canal.id)
    save_data(data)
    
    await interaction.response.send_message(f"Produto '{nome}' adicionado no canal {canal.mention}!", ephemeral=True)

@bot.tree.command(name="lista-produtos")
async def lista_produtos(interaction):
    if not is_admin(interaction.user):
        return
    
    data = load_data()
    e = discord.Embed(title="Lista de Produtos", color=discord.Color.blurple())
    
    for pid, d in data["produtos"].items():
        canal_id = data["produto_canais"].get(pid)
        canal = bot.get_channel(int(canal_id)) if canal_id else "Nenhum"
        e.add_field(name=f"ID {pid}", value=f"{d['nome']} - {d['preco']}\nCanal: {canal}")
    
    await interaction.response.send_message(embed=e, ephemeral=True)

@bot.tree.command(name="remove-produto")
async def remove_produto(interaction, pid: str):
    if not is_admin(interaction.user):
        return
    
    data = load_data()
    if pid in data["produtos"]:
        nome = data["produtos"][pid]["nome"]
        del data["produtos"][pid]
        if pid in data["produto_canais"]:
            del data["produto_canais"][pid]
        save_data(data)
        await interaction.response.send_message(f"Produto '{nome}' removido!", ephemeral=True)
    else:
        await interaction.response.send_message("Produto não encontrado.", ephemeral=True)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        cid = interaction.data.get("custom_id", "")
        if cid.startswith("comprar_"):
            pid = cid.replace("comprar_", "")
            data = load_data()
            prod = data["produtos"].get(pid)
            
            if prod:
                u = interaction.user
                g = interaction.guild
                
                try:
                    embed = discord.Embed(
                        title="🛒 CONFIRMAÇÃO DE COMPRA",
                        color=discord.Color.green()
                    )
                    embed.add_field(name="Produto", value=prod["nome"], inline=True)
                    embed.add_field(name="Preço", value=prod["preco"], inline=True)
                    embed.add_field(name="Descrição", value=prod["desc"], inline=False)
                    embed.set_footer(text="Aguarde a confirmação do pagamento")
                    
                    ch = await g.create_text_channel(f"compra-{u.name}")
                    await ch.set_permissions(u, view_channel=True, send_messages=True)
                    await ch.set_permissions(g.default_role, view_channel=False)
                    
                    await ch.send(content=f"{u.mention}", embed=embed)
                    await ch.send("💳 Envie o comprovante PIX aqui.")
                    
                    await interaction.response.send_message("✅ Canal privado criado!", ephemeral=True)
                except:
                    await interaction.response.send_message("Sem permissao.", ephemeral=True)

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
