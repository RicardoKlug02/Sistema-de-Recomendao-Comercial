from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle


def pdf_produtos_rede(dados):
    saida = BytesIO()
    documento = SimpleDocTemplate(saida, pagesize=landscape(A4), rightMargin=30, leftMargin=30,
                                  topMargin=32, bottomMargin=36, title="Códigos comprados pela rede",
                                  author="Rio Verde Representações")
    estilos = getSampleStyleSheet()
    celula = ParagraphStyle("celula", fontName="Helvetica", fontSize=8, leading=11)
    def p(valor):
        return Paragraph(escape(str(valor)), celula)
    conteudo = [Paragraph("Rio Verde Representações", estilos["Title"]),
                Paragraph("Códigos comprados pela rede", estilos["Heading2"]),
                p(f"Rede: {dados['rede']} | Fábrica: {dados['fabrica']}"),
                p(f"{dados['clientes']} estabelecimentos na rede | {dados['total']} códigos encontrados"), Spacer(1, 12)]
    linhas = [[p(v) for v in ("Código", "Produto", "Fábrica", "Último pedido", "Preço unitário", "Pedido", "Cliente da compra")]]
    for r in dados["produtos"]:
        preco = f"R$ {r['ultimo_preco']:,.2f}".replace(",", "@").replace(".", ",").replace("@", ".")
        linhas.append([p(v) for v in (r["sku"], r["nome"], r["fabrica"],
                       "/".join(reversed(r["ultima_compra"].split("-"))), preco, r["pedido"], r["cliente"])])
    if dados["produtos"]:
        tabela = LongTable(linhas, colWidths=[66, 190, 102, 75, 82, 70, 196], repeatRows=1, hAlign="LEFT")
        tabela.setStyle(TableStyle([("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#eaf0e6")),
                    ("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
                    ("TOPPADDING", (0, 0), (-1, -1), 7),
                    ("LINEBELOW", (0, 0), (-1, -1), .3, colors.HexColor("#d9e1d2"))]))
        conteudo.append(tabela)
    else:
        conteudo.append(p("Nenhum código comprado para os filtros selecionados."))
    conteudo.extend([Spacer(1, 12), p("Último preço unitário informado nos itens do último pedido encontrado na rede. "
                     "Pedidos no mesmo dia são desempatados pelo registro mais recente. Histórico importado."),
                     p(f"{dados['pedidos_sem_itens']} pedidos sem itens: seus códigos e preços não estão disponíveis neste relatório.")])
    def rodape(canvas, doc):
        canvas.setFont("Helvetica", 8)
        canvas.setFillColor(colors.HexColor("#55674b"))
        canvas.drawString(30, 20, "Rio Verde - Relatório comercial")
        canvas.drawRightString(landscape(A4)[0] - 30, 20, f"Página {doc.page}")
    documento.build(conteudo, onFirstPage=rodape, onLaterPages=rodape)
    return saida.getvalue()
