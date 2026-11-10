from io import BytesIO
from xml.sax.saxutils import escape
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, LongTable, TableStyle


def pdf_visita(dados):
    saida = BytesIO()
    doc = SimpleDocTemplate(saida, pagesize=landscape(A4), leftMargin=30, rightMargin=30,
                            topMargin=30, bottomMargin=38, title='Preparação da visita',
                            author='Rio Verde Representações')
    estilos = getSampleStyleSheet()
    celula = ParagraphStyle('visita-celula', fontName='Helvetica', fontSize=8, leading=11)
    def p(v):
        return Paragraph(escape(str(v or '-')).replace('\n', '<br/>'), celula)
    def data(v):
        return '/'.join(reversed(str(v).split('-'))) if v else 'Sem histórico'
    origem = dados['origem']
    flow = [Paragraph('Rio Verde Representações', estilos['Title']),
            Paragraph('Preparação da visita', estilos['Heading2']),
            p(f"Cliente/rede: {dados['cliente']} | Fábrica: {dados['fabrica']}"),
            p(f"Análise em {data(dados['referencia'])} | Histórico disponível neste escopo: "
              f"{data(origem.get('inicio'))} a {data(origem.get('fim'))}"),
            p(f"Escopo: {origem['escopo']} | {len(dados['cadastros'])} cadastro(s) fiscal(is)"),
            p('Fonte: cabeçalhos e itens importados. Sugestões para avaliação comercial; não constituem pedido.'),
            Spacer(1, 10)]
    for secao in dados['secoes']:
        flow.append(Paragraph(escape(secao['titulo']), estilos['Heading2']))
        if not secao['itens']:
            flow.append(p('Nenhum produto para a seleção atual.'))
            continue
        titulos = ['Código / produto', 'Fábrica', 'Última compra / quantidade', 'Motivo da indicação', 'Pedido / CNPJ de origem']
        pesos = [180, 85, 100, 220, 196.89]
        if dados['mostrar_precos']:
            titulos.append('Último preço unitário'); pesos = [155, 75, 90, 190, 181.89, 90]
        linhas = [[p(t) for t in titulos]]
        for r in secao['itens']:
            u = r['ultima']
            valores = [f"{r['sku']}\n{r['nome']}", r['fabrica'],
                       f"{data(u.get('data'))}\n{u.get('quantidade', 0):g} unidades",
                       r['motivo'], f"Pedido {u.get('pedido') or '-'}\n{u.get('cliente') or '-'}\n"
                       f"CNPJ/CPF: {u.get('cnpj_cpf') or '-'}\nCódigos originais: {', '.join(str(c) for c in u.get('codigos', []))}"]
            if dados['mostrar_precos']:
                preco = ('R$ '+f"{r['preco']:,.2f}").replace(',', '@').replace('.', ',').replace('@', '.') if r['preco'] is not None else '-'
                valores.append(preco)
            linhas.append([p(v) for v in valores])
        tabela = LongTable(linhas, colWidths=pesos, repeatRows=1, hAlign='LEFT')
        tabela.setStyle(TableStyle([('BACKGROUND', (0,0), (-1,0), colors.HexColor('#eaf0e6')),
            ('VALIGN', (0,0), (-1,-1), 'TOP'), ('TOPPADDING', (0,0), (-1,-1), 7),
            ('BOTTOMPADDING', (0,0), (-1,-1), 7),
            ('LINEBELOW', (0,0), (-1,-1), .3, colors.HexColor('#d9e1d2'))]))
        flow.extend([tabela, Spacer(1, 10)])
    notas = ['Abandono: no mínimo três datas de compra, pelo menos 60 dias sem compra e intervalo superior a 2,5 vezes o ciclo médio.',
             'Recompra: pelo menos duas datas de compra; janela a partir de cinco dias antes do ciclo habitual e antes de duas vezes esse ciclo. Restrições e substituições vigentes são aplicadas.',
             f"{dados['sem_confirmacao']} produtos com recompra não confirmada por pedidos posteriores sem itens foram mantidos fora das listas. Confira as pendências na ficha do cliente.",
             'O agrupamento por rede utiliza os vínculos cadastrais atuais. Primeira compra significa primeira compra registrada na base.']
    if dados['mostrar_precos']:
        notas.append('Preço unitário médio ponderado pela quantidade dos códigos equivalentes no último pedido conhecido. Não representa preço atual ou oferta. Pedidos no mesmo dia são desempatados pelo registro mais recente.')
    flow.append(Paragraph('Critérios e referências', estilos['Heading2']))
    for nota in notas:
        flow.extend([p(nota), Spacer(1, 5)])
    def rodape(canvas, documento):
        canvas.setFont('Helvetica', 8)
        canvas.drawString(30, 19, 'Rio Verde - Uso comercial interno')
        canvas.drawRightString(landscape(A4)[0]-30, 19, f'Página {documento.page}')
    doc.build(flow, onFirstPage=rodape, onLaterPages=rodape)
    return saida.getvalue()


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
                p(f"{dados['clientes']} cadastros fiscais na rede | {dados['total']} códigos encontrados"), Spacer(1, 12)]
    linhas = [[p(v) for v in ("Código", "Produto", "Fábrica", "Último pedido", "Preço unitário", "Pedido", "Cadastro fiscal da compra")]]
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


def pdf_tabela(dados):
    """Exportação completa dos relatórios, com paginação e filtros identificados."""
    saida=BytesIO()
    doc=SimpleDocTemplate(saida,pagesize=landscape(A4),leftMargin=28,rightMargin=28,topMargin=30,bottomMargin=34,
                          title=dados['titulo'],author='Rio Verde Representações')
    styles=getSampleStyleSheet()
    cell=ParagraphStyle('relatorio-celula',fontName='Helvetica',fontSize=8,leading=11)
    def p(v):return Paragraph(escape(str(v).replace('—','-')),cell)
    def moeda(v):return ('R$ '+f'{v:,.2f}').replace(',','@').replace('.',',').replace('@','.')
    def valor(v,tipo):
        if v is None:return 'Sem base' if tipo=='percentual' else '-'
        if tipo=='moeda':return moeda(v)
        if tipo=='data':return '/'.join(reversed(v.split('-')))
        if tipo=='percentual':return f'{v:+.2f}%'.replace('.',',')
        if tipo=='numero':return f'{v:g}'.replace('.',',')
        return str(v)
    filtros=dados['filtros']
    flow=[Paragraph('Rio Verde Representações',styles['Title']),Paragraph(escape(dados['titulo']),styles['Heading2']),
          p(f"Período: {valor(dados['inicio'],'data')} a {valor(dados['fim'],'data')} | {dados['total']} registros"),
          p(f"Fábrica: {filtros['fabrica']} | Vendedor: {filtros['vendedor']} | Rede: {filtros['rede']}"),Spacer(1,12)]
    colunas=dados['colunas']
    if dados['linhas']:
        pesos=[2.2 if c['chave'] in ('cliente','codigo','regiao','situacao') else .55 if c['chave']=='uf' else 1.5 if c['formato']=='texto' else 1 for c in colunas]
        larguras=[(landscape(A4)[0]-56)*w/sum(pesos) for w in pesos]
        rows=[[p(c['titulo']) for c in colunas]]+[[p(valor(r.get(c['chave']),c['formato'])) for c in colunas] for r in dados['linhas']]
        table=LongTable(rows,colWidths=larguras,repeatRows=1,hAlign='LEFT')
        table.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),colors.HexColor('#eaf0e6')),
            ('VALIGN',(0,0),(-1,-1),'TOP'),('TOPPADDING',(0,0),(-1,-1),7),('BOTTOMPADDING',(0,0),(-1,-1),7),
            ('LINEBELOW',(0,0),(-1,-1),.3,colors.HexColor('#d9e1d2'))]))
        flow.append(table)
    else:flow.append(p('Nenhum registro encontrado com os filtros selecionados.'))
    flow.append(Spacer(1,12))
    for nota in dados['notas']:flow.extend([p(nota),Spacer(1,5)])
    def rodape(canvas,documento):
        canvas.setFont('Helvetica',8);canvas.setFillColor(colors.HexColor('#55674b'))
        canvas.drawString(28,18,'Rio Verde - Histórico importado')
        canvas.drawRightString(landscape(A4)[0]-28,18,f'Página {documento.page}')
    doc.build(flow,onFirstPage=rodape,onLaterPages=rodape)
    return saida.getvalue()
