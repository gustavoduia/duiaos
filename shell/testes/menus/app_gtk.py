# DuiaOS — aplicativo GTK 3 de teste para o leitor de menus (test_menus.py): imprime ACIONADO <item>.
import gi, sys
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk
w = Gtk.Window(title="Editor GTK de teste")
caixa = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
barra = Gtk.MenuBar()
grupo = Gtk.AccelGroup(); w.add_accel_group(grupo)
def menu(nome, itens):
    topo = Gtk.MenuItem.new_with_mnemonic(nome); m = Gtk.Menu(); topo.set_submenu(m)
    for it in itens: m.append(it)
    barra.append(topo); return m
def item(nome, tecla=None, cb=None, ativo=True):
    i = Gtk.MenuItem.new_with_mnemonic(nome)
    if tecla: k, mod = Gtk.accelerator_parse(tecla); i.add_accelerator("activate", grupo, k, mod, Gtk.AccelFlags.VISIBLE)
    i.set_sensitive(ativo)
    i.connect("activate", lambda *_: print("ACIONADO", nome.replace("_", ""), flush=True))
    return i
sub = Gtk.MenuItem.new_with_mnemonic("_Recentes"); sm = Gtk.Menu(); sub.set_submenu(sm); sm.append(item("relatorio.txt")); sm.append(item("notas.md"))
check = Gtk.CheckMenuItem.new_with_mnemonic("_Quebrar linhas"); check.set_active(True)
check.connect("toggled", lambda c: print("ACIONADO Quebrar linhas", c.get_active(), flush=True))
oculto = item("Oculto"); oculto.set_no_show_all(True)
menu("_Arquivo", [item("_Novo", "<Control>n"), item("_Abrir…", "<Control>o"), sub, Gtk.SeparatorMenuItem(), item("_Sair", "<Control>q")])
menu("_Editar", [item("Des_fazer", "<Control>z", ativo=False), item("_Copiar", "<Control>c"), item("C_olar", "<Control>v"), oculto])
menu("E_xibir", [check])
caixa.pack_start(barra, False, False, 0); caixa.pack_start(Gtk.TextView(), True, True, 0)
w.add(caixa); w.set_default_size(500, 300); w.connect("destroy", Gtk.main_quit); w.show_all(); w.present()
Gtk.main()
