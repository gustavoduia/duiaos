// DuiaOS — escolha da tela principal quando há mais de um monitor.
// A tela embutida do notebook (eDP, LVDS ou DSI) é sempre a principal;
// sem ela (computador de mesa), vale o primeiro monitor.
.pragma library

function embutida(tela) {
    return /^(eDP|LVDS|DSI)/i.test(tela.name || "")
}

// Índice da tela principal numa lista de telas (Qt.application.screens)
function indicePrincipal(telas) {
    for (var i = 0; i < telas.length; i++) {
        if (embutida(telas[i]))
            return i
    }
    return 0
}

function principal(telas) {
    return telas.length > 0 ? telas[indicePrincipal(telas)] : null
}
