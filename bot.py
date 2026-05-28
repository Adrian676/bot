import discord
from discord.ext import commands
from discord import ui
import json
import os
from datetime import datetime

TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("TOKEN not configured!")
    exit()

DATA_FILE = "data.json"
FEEDBACK_FILE = "feedback.json"

intents = discord.Intents.default()
intents.message_content = True
intents.guilds = True
bot = commands.Bot(command_prefix="!", intents=intents)

def load_data():
    try:
        if not os.path.exists(DATA_FILE):
            return {"produtos": {}, "canal_loja": None, "canal_feedback": None}
        with open(DATA_FILE, "r") as f:
            dados = json.load(f)
            if "produtos" not in dados:
                dados["produtos"] = {}
            if "canal_loja" not in dados:
                dados["canal_loja"] = None
            if "canal_feedback" not in dados:
                dados["canal_feedback"] = None
            return dados
    except:
        return {"produtos": {}, "canal_loja": None, "canal_feedback": None}

def load_feedback():
    try:
        if not os.path.exists(FEEDBACK_FILE):
            return []
        with open(FEEDBACK_FILE, "r") as f:
            return json.load(f)
    except:
        return []

def save_feedback(data):
    with open(FEEDBACK_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def is_admin(member):
    return any(r.name == "Admin" for r in member.roles)

class FeedbackModal(ui.Modal, title="Avaliar Produto"):
    def __init__(self, produto):
        super().__init__()
        self.produto = produto
        self.nota = ui.TextInput(
            label="Nota (1-5)",
            placeholder="⭐⭐⭐⭐⭐",
            max_length=5,
            required=True
        )
        self.comentario = ui.TextInput(
            label="Comentario",
            placeholder="Escreva seu comentario...",
            style=discord.TextStyle.paragraph,
            required=False
        )
        self.add_item(self.nota)
        self.add_item(self.comentario)

    async def on_submit(self, interaction: discord.Interaction):
        nota = self.nota.value
        comentario = self.comentario.value if self.comentario.value else "Sem comentario"
        
        feedbacks = load_feedback()
        feedbacks.append({
            "produto": self.produto,
            "user": str(interaction.user),
            "nota": nota,
            "comentario": comentario,
            "data": str(datetime.now())
        })
        save_feedback(feedbacks)
        
        data = load_data()
        canal_id = data.get("canal_feedback")
        if canal_id:
            canal = bot.get_channel(int(canal_id))
            if canal:
                embed = discord.Embed(
                    title="╔═════════════════════════════════════════╗",
                    description="║     ⭐ NOVO FEEDBACK RECEBIDO     ⭐     ║",
                    color=discord.Color.purple()
                )
                embed.set_author(name="Loja Virtual")
                
                embed.add_field(name="📦 PRODUTO", value=f"**{self.produto}**", inline=True)
                embed.add_field(name="⭐ NOTA", value=nota, inline=True)
                embed.add_field(name="👤 USUÁRIO", value=str(interaction.user), inline=False)
                embed.add_field(name="💬 COMENTÁRIO", value=f"_{comentario}_", inline=False)
                embed.add_field(name="📅 DATA", value=datetime.now().strftime("%d/%m/%Y às %H:%M"), inline=True)
                
                embed.set_footer(text="Loja Virtual - Feedbacks")
                
                await canal.send(embed=embed)
                await canal.send("🆕 **NOVO FEEDBACK!** Ver acima ⬆️")
        
        await interaction.response.send_message("⭐ Obrigado pelo feedback!", ephemeral=True)

class BotaoComprar(ui.Button):
    def __init__(self, pid, nome, preco):
        super().__init__(
            label=f"COMPRAR {nome} - {preco}",
            custom_id=f"comprar_{pid}",
            style=discord.ButtonStyle.success
        )
        self.pid = pid
        self.nome = nome

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
            
            view_btn = ui.View(timeout=None)
            btn = ui.Button(
                label="⭐ AVALIAR",
                custom_id=f"avaliar_{prod['nome']}",
                style=discord.ButtonStyle.secondary
            )
            view_btn.add_item(btn)
            
            await canal.send("====================================================================================", view=view_btn)

            await canal.send("Apos receber o produto, clique para avaliar:", view=view_btn)
            
            await interaction.followup.send(f"Carrinho criado em {canal.mention}!", ephemeral=True)
        except:
            await interaction.followup.send("Erro ao criar canal!", ephemeral=True)

def criar_painel():
    data = load_data()
    embed = discord.Embed(
        title="=======LOJA VIRTUAL=======",
        description="Escolha:",
        color=discord.Color.from_rgb(255, 0, 0)
    )
    view = ui.View(timeout=None)
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
    await interaction.response.send_message("Produto adicionado!", ephemeral=True)

@bot.tree.command(name="loja-canal")
async def cmd_loja_canal(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    data = load_data()
    data["canal_loja"] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Canal da loja: {canal.mention}", ephemeral=True)

@bot.tree.command(name="feedback-canal")
async def cmd_feedback_canal(interaction, canal: discord.TextChannel):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    
    data = load_data()
    data["canal_feedback"] = str(canal.id)
    save_data(data)
    await interaction.response.send_message(f"Canal de feedback: {canal.mention}", ephemeral=True)

@bot.tree.command(name="painel-admin")
async def cmd_painel_admin(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    
    data = load_data()
    
    embed = discord.Embed(
        title="⚙️ PAINEL ADMIN - LOJA VIRTUAL",
        description="Configure sua loja:",
        color=discord.Color.blue()
    )
    
    loja_canal = bot.get_channel(int(data.get("canal_loja", 0))) if data.get("canal_loja") else "Nao configurado"
    feedback_canal = bot.get_channel(int(data.get("canal_feedback", 0))) if data.get("canal_feedback") else "Nao configurado"
    
    embed.add_field(name="🛒 Canal da Loja", value=str(loja_canal), inline=False)
    embed.add_field(name="📝 Canal de Feedback", value=str(feedback_canal), inline=False)
    
    produtos_count = len(data.get("produtos", {}))
    feedbacks_count = len(load_feedback())
    
    embed.add_field(name="📦 Produtos", value=str(produtos_count), inline=True)
    embed.add_field(name="💬 Total Feedbacks", value=str(feedbacks_count), inline=True)
    
    embed.set_footer(text="Loja Virtual - Painel Admin")
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

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
    await interaction.response.send_message("Loja enviada!", ephemeral=True)

@bot.tree.command(name="ver-feedback")
async def cmd_ver_feedback(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    
    feedbacks = load_feedback()
    if not feedbacks:
        await interaction.response.send_message("Nenhum feedback.", ephemeral=True)
        return
    
    embed = discord.Embed(title="💬 TODOS OS FEEDBACKS", color=discord.Color.purple())
    for f in feedbacks[-10:]:
        embed.add_field(
            name=f"📦 {f['produto']}",
            value=f"⭐ {f['nota']}\n💬 {f['comentario']}\n👤 {f['user']}\n📅 {f['data']}",
            inline=False
        )
    
    await interaction.response.send_message(embed=embed, ephemeral=True)

@bot.tree.command(name="atualizar-loja")
async def cmd_atualizar_loja(interaction):
    if not is_admin(interaction.user):
        await interaction.response.send_message("Sem permissao", ephemeral=True)
        return
    
    data = load_data()
    canal = bot.get_channel(int(data.get("canal_loja", 0)))
    if not canal:
        await interaction.response.send_message("Canal invalido", ephemeral=True)
        return
    
    embed, view = criar_painel()
    await canal.send(embed=embed, view=view)
    await interaction.response.send_message("Loja atualizada!", ephemeral=True)

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
    save_data({"produtos": {}, "canal_loja": None, "canal_feedback": None})
    save_feedback([])
    await interaction.response.send_message("Loja resetada!", ephemeral=True)

@bot.tree.command(name="sync")
async def cmd_sync(interaction):
    if not is_admin(interaction.user):
        return
    await bot.tree.sync()
    await interaction.response.send_message("Sincronizado!", ephemeral=True)

@bot.event
async def on_interaction(interaction):
    if interaction.type == discord.InteractionType.component:
        custom_id = interaction.data.get("custom_id", "")
        
        if custom_id.startswith("avaliar_"):
            produto = custom_id.replace("avaliar_", "")
            await interaction.response.send_modal(FeedbackModal(produto))

@bot.event
async def on_ready():
    print(f"Bot: {bot.user}")
    await bot.tree.sync()

if __name__ == "__main__":
    bot.run(TOKEN)
