"""DuiaOS — Ilha de Aplicativos: opções e efeitos de minimizar (ADR 050).

Só a biblioteca padrão (testável sem o Qt).

Opções da Ilha ficam em ~/.config/duiaos/preferencias.conf, seção [ilha]
(Configurações › Barra e Ilha e o botão direito no fundo da Ilha):

  tamanho            tamanho dos ícones, 32–80 (padrão 46)
  ampliacao          sim/nao: ícones crescem sob o mouse, como no macOS
  tamanho_ampliado   tamanho máximo com a ampliação, até 128 (padrão 72)
  posicao            base, esquerda ou direita
  ocultar            sim/nao: some e reaparece ao encostar o mouse na borda
  minimizar          genio, escala ou nenhum
  indicadores        sim/nao: ponto embaixo dos aplicativos abertos
  animar_abrir       sim/nao: o ícone pula enquanto o aplicativo abre
  recentes           sim/nao: até 3 aplicativos usados há pouco, depois dos fixados
  clique_minimiza    sim/nao: clicar no aplicativo que está na frente minimiza a janela

Minimizar com efeito: o labwc não tem animações, então a Ilha faz o efeito por
cima de tudo. Ela captura a tela (grim) antes e depois de minimizar; a região
que mudou é a janela (regiao_alterada); a imagem dela "escorre" até o ícone.
"""

PADROES = {"tamanho": 46, "ampliacao": True, "tamanho_ampliado": 72, "posicao": "base", "ocultar": False,
           "minimizar": "genio", "indicadores": True, "animar_abrir": True, "recentes": False,
           "clique_minimiza": False}
POSICOES = ("base", "esquerda", "direita")
EFEITOS = ("genio", "escala", "nenhum")
LIMITES = {"tamanho": (32, 80), "tamanho_ampliado": (32, 128)}


def _inteiro(texto, padrao):
    try:
        return int(float(texto))
    except (TypeError, ValueError):
        return padrao


def ler_opcoes(secao):
    """Seção [ilha] (dicionário de textos) → opções limpas, com os padrões no que faltar ou estiver errado."""
    secao = secao or {}
    opcoes = dict(PADROES)
    for chave, padrao in PADROES.items():
        if chave not in secao:
            continue
        valor = str(secao[chave]).strip().lower()
        if isinstance(padrao, bool):
            opcoes[chave] = valor in ("sim", "1", "true", "ligado")
        elif isinstance(padrao, int):
            minimo, maximo = LIMITES[chave]
            opcoes[chave] = max(minimo, min(maximo, _inteiro(valor, padrao)))
        elif chave == "posicao":
            opcoes[chave] = valor if valor in POSICOES else padrao
        elif chave == "minimizar":
            opcoes[chave] = valor if valor in EFEITOS else padrao
    # A ampliação nunca deixa o ícone menor que o tamanho normal
    opcoes["tamanho_ampliado"] = max(opcoes["tamanho_ampliado"], opcoes["tamanho"])
    return opcoes


def texto_da_opcao(chave, valor):
    """Valor vindo da interface → texto gravado nas preferências (ou None se não vale)."""
    if chave not in PADROES:
        return None
    padrao = PADROES[chave]
    if isinstance(padrao, bool):
        return "sim" if valor in (True, "sim", "true", 1, "1") else "nao"
    if isinstance(padrao, int):
        minimo, maximo = LIMITES[chave]
        return str(max(minimo, min(maximo, _inteiro(valor, padrao))))
    valor = str(valor)
    if chave == "posicao":
        return valor if valor in POSICOES else None
    if chave == "minimizar":
        return valor if valor in EFEITOS else None
    return None


# ------------------------------------------------------- região que mudou

def celulas_alteradas(antes, depois, largura, altura, linha_bytes, bpp, celula=4):
    """Compara duas imagens do mesmo tamanho (bytes crus, linha a linha) em células de celula×celula
    pixels. Devolve a grade [linha][coluna] de booleanos (True = mudou). Compara fatias de bytes
    (feito em C pelo Python), não pixel a pixel."""
    colunas, linhas = (largura + celula - 1) // celula, (altura + celula - 1) // celula
    grade = [[False] * colunas for _ in range(linhas)]
    largura_celula = celula * bpp
    for y in range(altura):
        inicio = y * linha_bytes
        linha_grade = grade[y // celula]
        for c in range(colunas):
            if linha_grade[c]:
                continue
            a = inicio + c * largura_celula
            b = min(a + largura_celula, inicio + largura * bpp)
            if antes[a:b] != depois[a:b]:
                linha_grade[c] = True
    return grade


def maior_regiao(grade):
    """Maior grupo de células alteradas que se tocam → (coluna, linha, largura, altura) em células, ou None."""
    linhas = len(grade)
    colunas = len(grade[0]) if linhas else 0
    visto = [[False] * colunas for _ in range(linhas)]
    melhor, melhor_tamanho = None, 0
    for y0 in range(linhas):
        for x0 in range(colunas):
            if not grade[y0][x0] or visto[y0][x0]:
                continue
            pilha, visto[y0][x0] = [(y0, x0)], True
            tamanho, x_min, x_max, y_min, y_max = 0, x0, x0, y0, y0
            while pilha:
                y, x = pilha.pop()
                tamanho += 1
                x_min, x_max, y_min, y_max = min(x_min, x), max(x_max, x), min(y_min, y), max(y_max, y)
                for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
                    if 0 <= ny < linhas and 0 <= nx < colunas and grade[ny][nx] and not visto[ny][nx]:
                        visto[ny][nx] = True
                        pilha.append((ny, nx))
            if tamanho > melhor_tamanho:
                melhor, melhor_tamanho = (x_min, y_min, x_max - x_min + 1, y_max - y_min + 1), tamanho
    return melhor


def aparar(grade, caixa, densidade=0.35):
    """Tira das bordas da caixa as faixas com poucas células alteradas (ex.: a barra de título da
    janela de baixo, que muda de cor quando ela ganha o foco)."""
    x, y, w, h = caixa

    def conta_linha(yy, x0, x1):
        return sum(1 for xx in range(x0, x1) if grade[yy][xx])

    def conta_coluna(xx, y0, y1):
        return sum(1 for yy in range(y0, y1) if grade[yy][xx])
    mudou = True
    while mudou and w > 2 and h > 2:
        mudou = False
        if conta_linha(y, x, x + w) < densidade * w:
            y, h, mudou = y + 1, h - 1, True
        if h > 2 and conta_linha(y + h - 1, x, x + w) < densidade * w:
            h, mudou = h - 1, True
        if conta_coluna(x, y, y + h) < densidade * h:
            x, w, mudou = x + 1, w - 1, True
        if w > 2 and conta_coluna(x + w - 1, y, y + h) < densidade * h:
            w, mudou = w - 1, True
    return x, y, w, h


def regiao_alterada(antes, depois, largura, altura, linha_bytes, bpp, celula=4, minimo=6):
    """Retângulo (x, y, w, h) em pixels da imagem onde estava a janela que sumiu, ou None se não
    deu para achar (nada mudou, ou mudou pouco demais para ser uma janela)."""
    if len(antes) != len(depois) or not antes:
        return None
    grade = celulas_alteradas(antes, depois, largura, altura, linha_bytes, bpp, celula)
    caixa = maior_regiao(grade)
    if not caixa:
        return None
    x, y, w, h = aparar(grade, caixa)
    if w < minimo or h < minimo:
        return None
    return x * celula, y * celula, min(w * celula, largura - x * celula), min(h * celula, altura - y * celula)


def ler_ppm(dados):
    """PPM binário (P6, o que o grim escreve) → (largura, altura, bytes RGB). None se não for P6."""
    if not dados.startswith(b"P6"):
        return None
    campos, posicao = [], 2
    while len(campos) < 3:
        while dados[posicao:posicao + 1].isspace():
            posicao += 1
        if dados[posicao:posicao + 1] == b"#":
            posicao = dados.index(b"\n", posicao) + 1
            continue
        fim = posicao
        while not dados[fim:fim + 1].isspace():
            fim += 1
        campos.append(int(dados[posicao:fim]))
        posicao = fim
    largura, altura, _maximo = campos
    return largura, altura, dados[posicao + 1:posicao + 1 + largura * altura * 3]
