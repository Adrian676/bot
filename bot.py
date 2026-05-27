import discord
from discord.ext import commands
from discord import ui
import json
import os

# TOKEN - configure no Railway (ou .env)
TOKEN = os.environ.get("TOKEN")
if not TOKEN:
    print("❌ TOKEN não configurado! Configure a variável TOKEN.")
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

def salvar_produtos(dados):
    com abrir(ARQUIVO_PRODUTOS, "w") como f:
        json.espéjar(dados, f, garantir_ascii=Falso, recuperar=2)

def é_admin(membro):
    retornar qualificador(r.nome == NOME_FUNÇÃO_ADMIN para r em membro.pais)

@bot.tree.comando(nome="ping")
assíncrono def ping(interação):
    esperar interação.resposta.enviar_mensagem(f"✅ Bot online! Latência: {redondo(robô.latência * 1000)}em")

@bot.tree.comando(nome="loja")
assíncrono def loja(interação):
    p = carregar_produtos()
    se não p:
        esperar interação.resposta.enviar_mensagem("Nenhum produto disponível.", efêmero=Verdadeiro)
        retornar
    e = discórdia.Incorporar(título="🛒 Loja Virtual", cor=discórdia.Cor.azul())
    para pid, d em p.itens():
        e.adicionar_campo(nome=f"{pid}. {d['nome']}", valor=f"💰 {d['preco']}\n{d['desc']}")
    visualização = ui.Ver()
    para pid, d em p.itens():
        btn = ui.Botão(rótulo=f"Comprar {d['nome']}", ID_personalizado=f"comprar_{pid}", estilo=discórdia.Estilo de botão.verde)
        visualizar.item_adicionário(btn)
    esperar interação.resposta.enviar_mensagem(incorporar=e, visualizar=visualizar)

@bot.tree.comando(nome="criar")
assíncrono def corar(interação, nome: str, preco: str, *, desc: str):
    se não é_admin(interação.usuário):
        esperar interação.resposta.enviar_mensagem("❌ Sem permissão.", efêmero=Verdadeiro)
        retornar
    p = carregar_produtos()
    pid = str(len(p) + 1)
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem(f"✅ Produto '{nome}" Criado!", efêmero=Verdadeiro)

@bot.tree.comando(nome="produtos")
assíncrono def produtos(interação):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    e = discórdia.Incorporar(título="📦 Produtos", cor=discórdia.Cor.desfocar())
    para pid, d em p.itens():
        e.adicionar_campo(nome=f"ID {pid}", valor=f"*{d['nome']}* - {d['preco']}")
    esperar interação.resposta.enviar_mensagem(incorporar=e, efêmero=Verdadeiro)

@bot.tree.comando(nome="editar")
assíncrono def editar(interação, pid: str, nome: str, preco: str, *, desc: str):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    se pid não em p:
        esperar interação.resposta.enviar_mensagem("❌ Produto não encontrado.", efêmero=Verdeiro)
        retornar
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem("✅ Produto atualizado!", efêmero=Verdeiro)

@bot.tree.comando(nome="excluir")
assíncrono def excluir(interação, pid: str):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    se pid não em p:
        esperar interação.resposta.enviar_mensagem("❌ Produto não encontrado.", efêmero=Verdeiro)
        retornar
    nome = p[pid]["nome"]
    faça p[pid]
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem(f"✅ Produto '{nome}' excluído!", efêmero=Verdeiro)

@bot.evento
assíncrono def on_interação(interação):
    se interação.tipo == discórdia.Tipo de interação.componente:
        cid = interação.dados.pegar("id_personalizado", "")
        se ácido.começa com("comprar_"):
            pid = cid.substituir("comprar_", "")
            p = carregar_produtos()
            prod = p.pegar(pid)
            se produção:
                u = interação.usuário
                g = interação.guilda
                tentar:
                    ch = esperar g.criar_canal de texto_(f"compra-{você.nome}")
                    esperar ch.definir_permissões(u, view_channel=Verdeiro, enviar_mensagens=Verdeiro)
                    esperar ch.definir_permissões(g.função_padrão, visualizar_canal=Falso)
                    e = discórdia.Incorporar(título="🛒 Nova Compra", cor=discórdia.Cor.verde())
                    e.adicionar_campo(nome="Produto", valor=prod["nome"])
                    e.adicionar_campo(nome="Preço", valor=prod["preco"])
                    e.adicionar_campo(nome="Descrição", valor=prod["desc"])
                    esperar ch.enviar(conteúdo=f"{você.menção}", incorporar=e)
                    esperar ch.enviar("💳 **Envie o compressor PIX aqui.**")
                    esperar interação.resposta.enviar_mensagem("✅ Canal privado criado!", efêmero=Verdeiro)
                exceto:
                    esperar intervenção.resposta.enviar_mensagem("❌ Sem permissão.", efêmero=Verdeiro)

@bot.evento
assíncrono def pronto para_ligado():
    imprimir(f"✅ Bot online: {robô.usuário}")
    esperar robô.árvore.sincronizar()

se __nome__ == "__principal__":
    robô.correr(SÍMBOLO)
