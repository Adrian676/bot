importar discórdia
de discórdia.ext importar comandos
de discórdia importar ui
importar json
importar os

TOKEN = os.meio ambiente.pegar("TOKEN")
se não TOKEN:
    imprimir("TOKEN não configurado!")
    sair()

NOME_FUNÇÃO_ADMIN = "Administrador"
PRODUTOS_FILE = "produtos.json"

intenções = discórdia.Intenções.padrão()
intenções.mensagem_conteúdo = Verdadeiro
intenções.guildas = Verdadeiro
bot = comandos.Botão(comando_prefixo="!", intenções=intenções)

def carregar_produtos():
    tentar:
        se não os.caminho.existe(ARQUIVO_PRODUTOS):
            retornar {}
        com abrir(ARQUIVO_PRODUTOS, "r") como f:
            retornar json.carregar(f)
    exceto:
        retornar {}

def salvar_produtos(dados):
    com abrir(ARQUIVO_PRODUTOS, "w") como f:
        json.despejar(dados, f, garantir_ascii=Falso, recuar=2)

def é_admin(membro):
    retornar qualquer(r.nome == NOME_FUNÇÃO_ADMIN para r em membro.papéis)

@bot.tree.comando(nome="ping")
assíncrono def ping(interação):
    esperar interação.resposta.enviar_mensagem(f"Bot online! Latência: {redondo(robô.latência * 1000)}em")

@bot.tree.comando(nome="loja")
assíncrono def loja(interação):
    p = carregar_produtos()
    se não p:
        esperar interação.resposta.enviar_mensagem("Nenhum produto.", efêmero=Verdadeiro)
        retornar
    e = discórdia.Incorporar(título="Loja Virtual", cor=discórdia.Cor.azul())
    para pid, d em p.itens():
        e.adicionar_campo(nome=f"{pid}. {d['nome']}", valor=f"{d['preco']} - {d['desc']}")
    visualização = ui.Ver()
    para pid, d em p.itens():
        btn = ui.Botão(rótulo=f"Comprar {d['nome']}", ID_personalizado=f"comprar_{pid}", estilo=discórdia.Estilo de botão.verde)
        visualizar.item_adicionar(btn)
    esperar interação.resposta.enviar_mensagem(incorporar=e, visualizar=visualizar)

@bot.tree.comando(nome="criar")
assíncrono def corar(interação, nome: str, preco: str, *, desc: str):
    se não é_admin(interação.usuário):
        esperar interação.resposta.enviar_mensagem("Sem permissão.", efêmero=Verdadeiro)
        retornar
    p = carregar_produtos()
    pid = str(len(p) + 1)
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem(f"Produto {nome} criado!", efêmero=Verdadeiro)

@bot.tree.comando(nome="produtos")
assíncrono def produtos(interação):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    e = discórdia.Incorporar(título="Produtos", cor=discórdia.Cor.desfocar())
    para pid, d em p.itens():
        e.adicionar_campo(nome=f"ID {pid}", valor=f"{d['nome']} - {d['preco']}")
    esperar interação.resposta.enviar_mensagem(incorporar=e, efêmero=Verdadeiro)

@bot.tree.comando(nome="editar")
assíncrono def editar(interação, pid: str, nome: str, preco: str, *, desc: str):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    se pid não em p:
        esperar interação.resposta.enviar_mensagem("Nao encontrado.", efêmero=Verdadeiro)
        retornar
    p[pid] = {"nome": nome, "preco": preco, "desc": desc}
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem("Produto atualizado!", efêmero=Verdadeiro)

@bot.tree.comando(nome="excluir")
assíncrono def excluir(interação, pid: str):
    se não é_admin(interação.usuário):
        retornar
    p = carregar_produtos()
    se pid não em p:
        esperar interação.resposta.enviar_mensagem("Nao encontrado.", efêmero=Verdadeiro)
        retornar
    nome = p[pid]["nome"]
    faça p[pid]
    salvar_produtos(p)
    esperar interação.resposta.enviar_mensagem(f"Produto {nome} excluído!", efêmero=Verdadeiro)

@bot.evento
assíncrono def on_interação(interação):
    se interação.tipo == discórdia.Tipo de interação.componente:
        cid = interação.dados.Pégar("id_personalizado", "")
        se ácido.começa com("comprar_"):
            pid = cid.substituto("comprar_", "")
            p = carregar_produtos()
            prod = p.Pégar(pid)
            se produção:
                u = interação.usuário
                g = interação.Guilda
                tentar:
                    ch = esperar g.criar_canal de texto_(f"compra-{você.nome}")
                    esperar ch.definir_permissões(u, view_channel=Verdadeiro, enviar_mensagens=Verdadeiro)
                    esperar ch.definir_permissões(g.função_padrão, visualizar_canal=Falso)
                    e = discórdia.Incorporar(título="Nova Compra", cor=discórdia.Cor.verde())
                    e.adicionar_campo(nome="Produto", valor=prod["nome"])
                    e.adicionar_campo(nome="Pré-co", valor=prod["preco"])
                    e.adicionar_campo(nome="Descricao", valor=prod["desc"])
                    esperar ch.invejar(conteúdo=f"{você.menção}", incorporar=e)
                    esperar ch.invejar("Envie o compressor PIX aqui.")
                    esperar interação.resposta.enviar_mensagem("Canal criado!", efêmero=Verdadeiro)
                exceto:
                    esperar interação.resposta.enviar_mensagem("Sem permissão.", efêmero=Verdadeiro)

@bot.evento
assíncrono def pronto para_ligado():
    imprimir(f"Bot online: {robô.usuário}")
    esperar robô.arvore.sincronizar()

se __nome__ == "__principal__":
    robô.corretor(SÍMBOLO)
