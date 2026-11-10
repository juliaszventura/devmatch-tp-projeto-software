"""Gera os seis DSS do item 4(c) em PNG e em um arquivo editavel draw.io.

Os diagramas usam apenas atores externos e a caixa-preta DevMatch. As
mensagens de resposta sao representadas por setas tracejadas.
"""

from pathlib import Path
from xml.etree import ElementTree as ET
from PIL import Image, ImageDraw, ImageFont


OUT = Path(__file__).resolve().parent
SCALE = 2
FONT_DIR = Path('/System/Library/Fonts/Supplemental')
FONT = ImageFont.truetype(str(FONT_DIR / 'Arial.ttf'), 20 * SCALE)
FONT_BOLD = ImageFont.truetype(str(FONT_DIR / 'Arial Bold.ttf'), 20 * SCALE)
FONT_SMALL = ImageFont.truetype(str(FONT_DIR / 'Arial.ttf'), 18 * SCALE)
FONT_TITLE = ImageFont.truetype(str(FONT_DIR / 'Arial Bold.ttf'), 26 * SCALE)

INK = '#172334'
BLUE = '#234f78'
BLUE_PALE = '#eaf2f9'
GRAY = '#67788b'
FRAME = '#aebdcc'
NOTE = '#fff7df'


DIAGRAMS = [
    dict(
        code='UC03', title='Enviar e negociar proposta',
        lanes=['Freelancer', 'DevMatch', 'Cliente'],
        steps=[
            ('msg', 'Freelancer', 'DevMatch', 'enviarProposta(projetoId, dados)'),
            ('start', 'alt [projeto aberto e dados válidos]'),
            ('ret', 'DevMatch', 'Freelancer', 'propostaEnviada(propostaId)'),
            ('ret', 'DevMatch', 'Cliente', 'propostaRecebida(propostaId)'),
            ('else', '[projeto encerrado ou dados inválidos]'),
            ('ret', 'DevMatch', 'Freelancer', 'envioRecusado(motivo)'),
            ('end',),
            ('start', 'opt [negociação em andamento]'),
            ('msg', 'Cliente', 'DevMatch', 'proporAlteracao(propostaId, dados)'),
            ('ret', 'DevMatch', 'Freelancer', 'novaVersao(propostaId)'),
            ('msg', 'Freelancer', 'DevMatch', 'responderNegociacao(propostaId, decisao)'),
            ('ret', 'DevMatch', 'Cliente', 'respostaRegistrada(propostaId)'),
            ('end',),
            ('note', 'O aceite da proposta pertence ao UC05.'),
        ],
    ),
    dict(
        code='UC04', title='Publicar e gerenciar projeto',
        lanes=['Cliente', 'DevMatch'],
        steps=[
            ('msg', 'Cliente', 'DevMatch', 'publicarProjeto(dados)'),
            ('start', 'alt [dados válidos]'),
            ('ret', 'DevMatch', 'Cliente', 'projetoPublicado(projetoId)'),
            ('else', '[dados inválidos]'),
            ('ret', 'DevMatch', 'Cliente', 'publicacaoRecusada(motivo)'),
            ('end',),
            ('start', 'opt [edição permitida]'),
            ('msg', 'Cliente', 'DevMatch', 'editarProjeto(projetoId, alteracoes)'),
            ('ret', 'DevMatch', 'Cliente', 'projetoAtualizado(projetoId)'),
            ('end',),
            ('start', 'opt [pausa solicitada]'),
            ('msg', 'Cliente', 'DevMatch', 'pausarProjeto(projetoId)'),
            ('ret', 'DevMatch', 'Cliente', 'recebimentoPausado(projetoId)'),
            ('end',),
            ('start', 'opt [encerramento solicitado]'),
            ('msg', 'Cliente', 'DevMatch', 'encerrarProjeto(projetoId)'),
            ('ret', 'DevMatch', 'Cliente', 'projetoEncerrado(projetoId)'),
            ('end',),
            ('note', 'A edição preserva as propostas já negociadas.'),
        ],
    ),
    dict(
        code='UC06', title='Formalizar e acompanhar contrato',
        lanes=['Cliente', 'DevMatch', 'Freelancer'],
        steps=[
            ('note', 'Pré-condição: proposta aceita no UC05.'),
            ('msg', 'Cliente', 'DevMatch', 'formalizarContrato(propostaId, marcos)'),
            ('ret', 'DevMatch', 'Cliente', 'contratoParaConfirmacao(contratoId)'),
            ('ret', 'DevMatch', 'Freelancer', 'contratoParaConfirmacao(contratoId)'),
            ('msg', 'Freelancer', 'DevMatch', 'confirmarContrato(contratoId)'),
            ('msg', 'Cliente', 'DevMatch', 'confirmarContrato(contratoId)'),
            ('start', 'alt [depósito validado no UC08]'),
            ('msg', 'Cliente', 'DevMatch', 'consultarContrato(contratoId)'),
            ('ret', 'DevMatch', 'Cliente', 'contratoAtivo(dados)'),
            ('else', '[depósito pendente]'),
            ('msg', 'Cliente', 'DevMatch', 'consultarContrato(contratoId)'),
            ('ret', 'DevMatch', 'Cliente', 'aguardandoCustodia(dados)'),
            ('end',),
            ('start', 'opt [alteração posterior de contrato ativo]'),
            ('msg', 'Cliente', 'DevMatch', 'proporAlteracaoContrato(contratoId, dados)'),
            ('ret', 'DevMatch', 'Freelancer', 'alteracaoPendente(contratoId)'),
            ('msg', 'Freelancer', 'DevMatch', 'confirmarAlteracaoContrato(contratoId)'),
            ('ret', 'DevMatch', 'Cliente', 'contratoAtualizado(contratoId)'),
            ('end',),
        ],
    ),
    dict(
        code='UC07', title='Gerenciar marcos e entregas',
        lanes=['Freelancer', 'DevMatch', 'Cliente'],
        steps=[
            ('msg', 'Freelancer', 'DevMatch', 'registrarEntrega(marcoId, dados, anexos)'),
            ('ret', 'DevMatch', 'Freelancer', 'entregaRegistrada(entregaId)'),
            ('ret', 'DevMatch', 'Cliente', 'entregaDisponivel(entregaId)'),
            ('start', 'alt [cliente aprova]'),
            ('msg', 'Cliente', 'DevMatch', 'avaliarEntrega(entregaId, aprovar)'),
            ('ret', 'DevMatch', 'Freelancer', 'entregaAprovada(entregaId)'),
            ('else', '[cliente solicita ajustes]'),
            ('msg', 'Cliente', 'DevMatch', 'avaliarEntrega(entregaId, ajustes, motivo)'),
            ('ret', 'DevMatch', 'Freelancer', 'ajustesSolicitados(motivo)'),
            ('end',),
            ('note', 'A aprovação inicia a liberação do marco no UC08.'),
            ('note', 'Prazo de avaliação vencido: aplicar regra contratual.'),
        ],
    ),
    dict(
        code='UC08', title='Gerenciar custódia, pagamentos e repasses',
        lanes=['Cliente', 'DevMatch', 'Gateway', 'Analista financeiro'],
        steps=[
            ('msg', 'Cliente', 'DevMatch', 'iniciarDeposito(marcoId, valor)'),
            ('msg', 'DevMatch', 'Gateway', 'criarCobranca(transacaoId, valor)'),
            ('ret', 'DevMatch', 'Cliente', 'instrucoesPagamento(transacaoId)'),
            ('msg', 'Gateway', 'DevMatch', 'confirmarDeposito(transacaoId, status)'),
            ('start', 'alt [pagamento confirmado]'),
            ('ret', 'DevMatch', 'Cliente', 'custodiaConfirmada(marcoId)'),
            ('else', '[falha ou cancelamento]'),
            ('ret', 'DevMatch', 'Cliente', 'depositoNaoConfirmado(motivo)'),
            ('end',),
            ('start', 'alt [custódia confirmada e liberação autorizada]'),
            ('msg', 'DevMatch', 'Gateway', 'solicitarRepasse(marcoId, valorLiquido)'),
            ('msg', 'Gateway', 'DevMatch', 'confirmarRepasse(transacaoId, status)'),
            ('else', '[custódia confirmada e reembolso decidido no UC09]'),
            ('msg', 'DevMatch', 'Gateway', 'solicitarReembolso(marcoId, valor)'),
            ('msg', 'Gateway', 'DevMatch', 'confirmarReembolso(transacaoId, status)'),
            ('end',),
            ('msg', 'Analista financeiro', 'DevMatch', 'consultarTransacao(transacaoId)'),
            ('ret', 'DevMatch', 'Analista financeiro', 'dadosTransacao(dados)'),
            ('note', 'Sem aprovação ou decisão, o valor permanece bloqueado.'),
            ('note', 'Liberação decorre de aprovação (UC07) ou mediação (UC09).'),
            ('note', 'Divisão do valor combina repasse e reembolso parciais.'),
        ],
    ),
    dict(
        code='UC09', title='Abrir e mediar disputa',
        lanes=['Solicitante', 'DevMatch', 'Outra parte', 'Administrador'],
        steps=[
            ('msg', 'Solicitante', 'DevMatch', 'abrirDisputa(contratoId, motivo, evidencias)'),
            ('ret', 'DevMatch', 'Solicitante', 'disputaRegistrada(disputaId)'),
            ('ret', 'DevMatch', 'Outra parte', 'disputaAberta(disputaId)'),
            ('msg', 'Outra parte', 'DevMatch', 'responderDisputa(disputaId, resposta)'),
            ('msg', 'Administrador', 'DevMatch', 'consultarDossie(disputaId)'),
            ('ret', 'DevMatch', 'Administrador', 'contratoMensagensEntregasTransacoes()'),
            ('msg', 'Administrador', 'DevMatch', 'decidirDisputa(disputaId, decisao, motivo)'),
            ('ret', 'DevMatch', 'Solicitante', 'decisaoRegistrada(disputaId)'),
            ('ret', 'DevMatch', 'Outra parte', 'decisaoRegistrada(disputaId)'),
            ('note', 'Decisão: liberar, reembolsar ou dividir o valor (UC08).'),
        ],
    ),
]


def xy_positions(n):
    if n == 2:
        return [360, 1320]
    if n == 3:
        return [170, 840, 1510]
    return [140, 600, 1080, 1530]


def line(draw, points, fill, width=2, dash=False):
    points = [(int(x * SCALE), int(y * SCALE)) for x, y in points]
    if not dash:
        draw.line(points, fill=fill, width=width * SCALE)
        return
    (x1, y1), (x2, y2) = points
    import math
    length = math.hypot(x2 - x1, y2 - y1)
    dx, dy = (x2 - x1) / length, (y2 - y1) / length
    pos = 0
    while pos < length:
        end = min(pos + 10 * SCALE, length)
        draw.line([(x1 + dx * pos, y1 + dy * pos), (x1 + dx * end, y1 + dy * end)], fill=fill, width=width * SCALE)
        pos += 16 * SCALE


def add_vertex(root, ident, label, x, y, w, h, style):
    cell = ET.SubElement(root, 'mxCell', id=ident, value=label, style=style, vertex='1', parent='1')
    ET.SubElement(cell, 'mxGeometry', x=str(x), y=str(y), width=str(w), height=str(h), attrib={'as': 'geometry'})


def add_edge(root, ident, x1, y1, x2, y2, style):
    cell = ET.SubElement(root, 'mxCell', id=ident, value='', style=style, edge='1', parent='1')
    geom = ET.SubElement(cell, 'mxGeometry', relative='1', attrib={'as': 'geometry'})
    ET.SubElement(geom, 'mxPoint', x=str(x1), y=str(y1), attrib={'as': 'sourcePoint'})
    ET.SubElement(geom, 'mxPoint', x=str(x2), y=str(y2), attrib={'as': 'targetPoint'})


def render(d):
    width = 1680
    top = 184
    y = top
    positioned = []
    stack = []
    frames = []
    for step in d['steps']:
        kind = step[0]
        if kind == 'start':
            frames.append({'start': y - 24, 'end': None, 'label': step[1], 'dividers': []})
            stack.append(frames[-1])
            positioned.append((y, step))
            y += 48
        elif kind == 'else':
            stack[-1]['dividers'].append(y - 20)
            positioned.append((y, step))
            y += 48
        elif kind == 'end':
            stack.pop()['end'] = y - 13
            y += 16
        elif kind == 'note':
            positioned.append((y, step))
            y += 58
        else:
            positioned.append((y, step))
            y += 67
    height = y + 55
    positions = dict(zip(d['lanes'], xy_positions(len(d['lanes']))))
    im = Image.new('RGB', (width * SCALE, height * SCALE), 'white')
    dr = ImageDraw.Draw(im)
    dr.rectangle((0, 0, width * SCALE, 71 * SCALE), fill=BLUE)
    dr.text((35 * SCALE, 20 * SCALE), f"{d['code']}  |  {d['title']}", fill='white', font=FONT_TITLE)

    root = ET.Element('root')
    ET.SubElement(root, 'mxCell', id='0')
    ET.SubElement(root, 'mxCell', id='1', parent='0')
    add_vertex(root, 'title', f"{d['code']}  |  {d['title']}", 0, 0, width, 71,
               'rounded=0;whiteSpace=wrap;html=1;fillColor=#234f78;strokeColor=none;fontColor=#ffffff;fontStyle=1;fontSize=26;align=left;spacingLeft=35;')

    for i, frame in enumerate(frames):
        y0, y1 = frame['start'], frame['end']
        tab_width = max(370, int((dr.textbbox((0, 0), frame['label'], font=FONT_SMALL)[2]) / SCALE + 25))
        frame['tab_width'] = tab_width
        dr.rectangle((30 * SCALE, y0 * SCALE, (width - 30) * SCALE, y1 * SCALE), outline=FRAME, width=2 * SCALE)
        dr.rectangle((30 * SCALE, y0 * SCALE, (30 + tab_width) * SCALE, (y0 + 36) * SCALE), fill=BLUE_PALE, outline=FRAME, width=2 * SCALE)
        dr.text((42 * SCALE, (y0 + 6) * SCALE), frame['label'], fill=INK, font=FONT_SMALL)
        add_vertex(root, f'frame{i}', '', 30, y0, width - 60, y1 - y0,
                   'rounded=0;whiteSpace=wrap;html=1;fillColor=none;strokeColor=#aebdcc;strokeWidth=2;')
        add_vertex(root, f'frame{i}_tab', frame['label'], 30, y0, tab_width, 36,
                   'rounded=0;whiteSpace=wrap;html=1;fillColor=#eaf2f9;strokeColor=#aebdcc;fontSize=18;align=left;spacingLeft=10;')
        for j, div_y in enumerate(frame['dividers']):
            line(dr, [(30, div_y), (width - 30, div_y)], FRAME)
            add_edge(root, f'frame{i}_divider{j}', 30, div_y, width - 30, div_y,
                     'endArrow=none;strokeColor=#aebdcc;strokeWidth=2;')

    for i, lane in enumerate(d['lanes']):
        x = positions[lane]
        is_system = lane == 'DevMatch'
        color = BLUE if is_system else BLUE_PALE
        text_color = 'white' if is_system else INK
        dr.rounded_rectangle(((x - 135) * SCALE, 91 * SCALE, (x + 135) * SCALE, 143 * SCALE),
                             radius=9 * SCALE, fill=color, outline=BLUE, width=2 * SCALE)
        box = dr.textbbox((0, 0), lane, font=FONT_BOLD)
        dr.text(((x * SCALE - (box[2] - box[0]) / 2), 103 * SCALE), lane, fill=text_color, font=FONT_BOLD)
        line(dr, [(x, 143), (x, height - 24)], GRAY, dash=True)
        add_vertex(root, f'lane{i}', lane, x - 135, 91, 270, 52,
                   ('rounded=1;arcSize=12;whiteSpace=wrap;html=1;fillColor=' +
                    ('#234f78;strokeColor=#234f78;fontColor=#ffffff;' if is_system else '#eaf2f9;strokeColor=#234f78;fontColor=#172334;') +
                    'fontSize=20;fontStyle=1;'))
        add_edge(root, f'lane{i}_line', x, 143, x, height - 24,
                 'endArrow=none;dashed=1;dashPattern=4 4;strokeColor=#67788b;strokeWidth=1;')

    # A etiqueta do fragmento deve ficar acima das linhas de vida.
    for i, frame in enumerate(frames):
        y0 = frame['start']
        tab_width = frame['tab_width']
        dr.rectangle((30 * SCALE, y0 * SCALE, (30 + tab_width) * SCALE, (y0 + 36) * SCALE),
                     fill=BLUE_PALE, outline=FRAME, width=2 * SCALE)
        dr.text((42 * SCALE, (y0 + 6) * SCALE), frame['label'], fill=INK, font=FONT_SMALL)
        add_vertex(root, f'frame{i}_tabfront', frame['label'], 30, y0, tab_width, 36,
                   'rounded=0;whiteSpace=wrap;html=1;fillColor=#eaf2f9;strokeColor=#aebdcc;fontSize=18;align=left;spacingLeft=10;')

    for i, (row_y, step) in enumerate(positioned):
        kind = step[0]
        if kind in ('msg', 'ret'):
            _, src, dst, label = step
            x1, x2 = positions[src], positions[dst]
            yline = row_y + 30
            color = INK if kind == 'msg' else GRAY
            line(dr, [(x1, yline), (x2, yline)], color, width=2, dash=kind == 'ret')
            sign = 1 if x2 > x1 else -1
            line(dr, [(x2 - 12 * sign, yline - 7), (x2, yline), (x2 - 12 * sign, yline + 7)], color, width=2)
            text_box = dr.textbbox((0, 0), label, font=FONT)
            tw = text_box[2] - text_box[0]
            tx = (x1 + x2) * SCALE / 2 - tw / 2
            ty = (row_y - 5) * SCALE
            dr.rectangle((tx - 7 * SCALE, ty - 2 * SCALE, tx + tw + 7 * SCALE, ty + 26 * SCALE), fill='white')
            dr.text((tx, ty), label, fill=color, font=FONT)
            add_edge(root, f'm{i}_line', x1, yline, x2, yline,
                     f'endArrow={"open" if kind == "ret" else "block"};endFill={0 if kind == "ret" else 1};'
                     f'strokeColor={"#67788b" if kind == "ret" else "#172334"};strokeWidth=2;'
                     f'{"dashed=1;dashPattern=8 5;" if kind == "ret" else ""}')
            add_vertex(root, f'm{i}_label', label, int((x1 + x2) / 2 - tw / SCALE / 2 - 7),
                       row_y - 7, int(tw / SCALE + 14), 30,
                       f'rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;'
                       f'fontSize=20;fontColor={"#67788b" if kind == "ret" else "#172334"};')
        elif kind == 'else':
            text_value = step[1]
            tb = dr.textbbox((0, 0), text_value, font=FONT_SMALL)
            text_width = (tb[2] - tb[0]) / SCALE
            dr.rectangle((39 * SCALE, (row_y - 11) * SCALE,
                          (54 + text_width) * SCALE, (row_y + 21) * SCALE), fill='white')
            dr.text((42 * SCALE, (row_y - 9) * SCALE), text_value, fill=INK, font=FONT_SMALL)
            add_vertex(root, f'else{i}', text_value, 42, row_y - 11, int(text_width + 14), 31,
                       'rounded=0;whiteSpace=wrap;html=1;fillColor=#ffffff;strokeColor=none;fontSize=18;align=left;')
        elif kind == 'note':
            text_value = step[1]
            box = dr.textbbox((0, 0), text_value, font=FONT_SMALL)
            bw = min(width - 80, (box[2] - box[0]) / SCALE + 34)
            x0 = (width - bw) / 2
            dr.rounded_rectangle((x0 * SCALE, (row_y - 8) * SCALE, (x0 + bw) * SCALE, (row_y + 31) * SCALE),
                                 radius=5 * SCALE, fill=NOTE, outline='#d8c384', width=SCALE)
            dr.text(((x0 + 17) * SCALE, (row_y - 2) * SCALE), text_value, fill=INK, font=FONT_SMALL)
            add_vertex(root, f'note{i}', text_value, int(x0), row_y - 8, int(bw), 39,
                       'rounded=1;arcSize=10;whiteSpace=wrap;html=1;fillColor=#fff7df;strokeColor=#d8c384;fontSize=18;')

    filename = OUT / f'dss_{d["code"].lower()}.png'
    im.save(filename, optimize=True)
    return root, width, height, filename


def main():
    mxfile = ET.Element('mxfile', host='app.diagrams.net', modified='2026-11-10T00:00:00.000Z',
                        agent='DevMatch', version='24.7.17', type='device')
    for d in DIAGRAMS:
        root, w, h, filename = render(d)
        page = ET.SubElement(mxfile, 'diagram', id=d['code'], name=d['code'])
        model = ET.SubElement(page, 'mxGraphModel', dx='1000', dy='800', grid='1', gridSize='10',
                              guides='1', tooltips='1', connect='1', arrows='1', fold='1',
                              page='1', pageScale='1', pageWidth=str(w), pageHeight=str(h),
                              math='0', shadow='0')
        model.append(root)
        print(filename)
    target = OUT / 'sequencia_sistema.drawio'
    ET.ElementTree(mxfile).write(target, encoding='utf-8', xml_declaration=True)
    print(target)


if __name__ == '__main__':
    main()
