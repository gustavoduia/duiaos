import QtQuick

Item {
    width: parent ? parent.width : 100
    height: 9
    Rectangle { anchors { left: parent.left; right: parent.right; verticalCenter: parent.verticalCenter; leftMargin: 8; rightMargin: 8 } height: 1; color: Tema.borda }
}
