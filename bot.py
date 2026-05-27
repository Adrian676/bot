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

@bot.tree.command(name="loja")
async def loja(interaction):
    data = load_data()
    
    # Embed com cores e formato diferente
    embed = discord.Embed(
        title="╔══════════════════════════════════╗\n║        🛒  LOJA VIRTUAL  🛒        ║\n╚══════════════════════════════════╝",
        description="**▸▸ BEM-VINDO À LOJA ◂◂**\n\nEscolha seu produto abaixo:",
        color=discord.Color.from_rgb(255, 215, 0)  # Dourado
    )
    
    if data["produtos"]:
        produtos_texto = ""
        for pid, d in data["produtos"].items():
            produtos_texto += f"**▸ {d['nome']}**\n   │\n   ├─ 💵 Preço: `{d['preco']}`\n   └─ 📝 {d['desc'][:50]}...\n\n"
        
        embed.description += f"\n{produtos_texto}"
    else:
        embed.add_field(name="❌ Nenhum produto", value="Use /add-produto para adicionar", inline=False)
    
    embed.set_footer(text="© Loja Virtual 2025 | Clique em COMPRAR")
    embed.set_author(name="LOJA VIRTUAL", icon_url="https://i.imgur.com/SeuIcone.png")
    
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
        await interaction.response.send_message("Canal não encontrado.", ephemeral=True)
        return
    
    # Painel super bonito no canal
    embed = discord.Embed(
        title="╔═══════════════════════════════════════╗\n║     🛒🛒🛒  LOJA VIRTUAL  🛒🛒🛒      ║\n╚═══════════════════════════════════════╝",
        description="**🎉 BEM-VINDO! 🎉**\n\nEscolha abaixo o produto desejado:\n",
        color=discord.Color.from_rgb(255, 215, 0)
    )
    
    if data["produtos"]:
        for pid, d in data["produtos"].items():
            embed.add_field(
                name=f"📦 {pid}. {d['nome']}",
                value=f"💰 **Preço:** `{d['preco']}`\n📝 {d['desc'][:80]}...",
                inline=False
            )
    else:
        embed.add_field(name="❌ Sem produtos", value="Nenhum produto disponível", inline=False)
    
    embed.set_footer(text="© Loja Virtual 2025 | Clique no botão para comprar")
    
    view = PainelLoja(data["produtos"])
    
    await canal.send(embed=embed, view=view)
    await interaction.response.send_message(f"Loja enviada para {canal.mention}!", ephemeral=True)

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
    
    await interaction.response.send_message(f"✅ Produto '{nome}' adicionado!", ephemeral=True)

@bot.tree.command(name="lista-produtos")
async def lista_produtos(interaction):
    if not is_admin(interaction.user):
        return
    
    data = load_data()
    e = discord.Embed(title="📦 Lista de Produtos", color=discord.Color.blurple())
    
    for pid, d in data["produtos"].items():
        canal_id = data["produto_canais"].get(pid)
        canal = bot.get_channel(int(canal_id)) if canal_id else "Nenhum"
        e.add_field(name=f"ID {pid}", value=f"**{d['nome']}** - {d['preco']}\nCanal: {canal}")
    
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
        await interaction.response.send_message(f"✅ Produto '{nome}' removido!", ephemeral=True)
    else:
        await interaction.response.send_message("❌ Produto não encontrado.", ephemeral=True)

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
            
            # Embed bonito da compra
            embed = discord.Embed(
                title="╔══════════════════════════════════╗\n║    🧾 CONFIRMAÇÃO DE COMPRA    ║\n╚══════════════════════════════════╝",
                color=discord.Color.green()
            )
            embed.add_field(name="📦 Produto", value=prod["nome"], inline=True)
            embed.add_field(name="💰 Preço", value=prod["preco"], inline=True)
            embed.add_field(name="📝 Descrição", value=prod["desc"], inline=False)
            embed.set_footer(text="Aguarde confirmação do pagamento")
            
            await canal.send(content=f"{user.mention}", embed=embed)
            await canal.send("💳 **ENVIE O COMPROVANTE DO PIX AQUI**\n\n⏰ Aguarde aprovação para receber o produto.")
            
            await interaction.followup.send("✅ Canal privado criado!", ephemeral=True)
            
        except Exception as e:
            try:
                await interaction.followup.send(f"❌ Erro: {str(e)}", ephemeral=True)
            except:
                pass

@bot.event
async def on_ready():
    print(f"Bot online: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
