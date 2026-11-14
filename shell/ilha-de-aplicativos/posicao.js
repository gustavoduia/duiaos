// DuiaOS — onde ficam os balões da Ilha (menu do botão direito e pilha de Downloads), com a Ilha
// embaixo, à esquerda ou à direita. "ancora" é a distância do centro da Ilha até o ícone, ao
// longo da Ilha; a área é a camada por cima da área de trabalho (sem a faixa da Ilha).
.pragma library

function balao(posicao, larguraArea, alturaArea, ancora, largura, altura) {
    var margem = 8
    function limitar(v, maximo) { return Math.max(margem, Math.min(maximo - margem, v)) }
    if (posicao === "esquerda")
        return { x: 10, y: limitar(alturaArea / 2 + ancora - altura / 2, alturaArea - altura) }
    if (posicao === "direita")
        return { x: larguraArea - largura - 10, y: limitar(alturaArea / 2 + ancora - altura / 2, alturaArea - altura) }
    return { x: limitar(larguraArea / 2 + ancora - largura / 2, larguraArea - largura), y: alturaArea - altura - 10 }
}
