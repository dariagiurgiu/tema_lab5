import os
import sys

import posix_ipc
import sysv_ipc
from PySide6.QtCore import QFile
from PySide6.QtUiTools import QUiLoader
from PySide6.QtWidgets import QApplication, QPushButton, QLineEdit, QFileDialog, QTextEdit, QMessageBox

def text_to_html(text: str) -> str:
    lines = [ln.rstrip() for ln in text.splitlines()]

    title = ""
    i = 0
    while i < len(lines) and lines[i] == "":
        i += 1
    if i < len(lines):
        title = lines[i]
        i += 1

    body_lines = []
    para = []
    for ln in lines[i:]:
        if ln == "":
            if para:
                body_lines.append("<p>{}</p>".format(" ".join(para)))
                para = []
        else:
            para.append(ln)
    if para:
        body_lines.append("<p>{}</p>".format(" ".join(para)))
    body = "\n".join(body_lines)
    html = f"""<!doctype html>
<html>
<head>
  <meta charset="utf-8">
  <title>{title}</title>
</head>
<body>
  <h1>{title}</h1>
{body}
</body>
</html>"""
    return html

def main():
    loader = QUiLoader()
    app = QApplication(sys.argv)

    ui_file = QFile("html_converter.ui")
    ui_file.open(QFile.ReadOnly)
    window = loader.load(ui_file)
    ui_file.close()

    def browseButton_clicked():
        path, _ = QFileDialog.getOpenFileName(window,"Select text file", "", "Text Files (*.txt);;All Files (*)")
        if path:
            path_line_edit.setText(path)

    button = window.findChild(QPushButton,"browse_btn")
    button.clicked.connect(browseButton_clicked)

    path_line_edit=QLineEdit()
    path_edit = window.findChild(QLineEdit, "path_line_edit")
    browse_btn = window.findChild(QPushButton, "browse_btn")
    text_edit = window.findChild(QTextEdit, "textEdit")
    convert_btn = window.findChild(QPushButton, "pushButton")  # Convert to HTML
    send_btn = window.findChild(QPushButton, "pushButton_2")

    def on_browse():
        path, _ = QFileDialog.getOpenFileName(window, "Select text file", "", "Text Files (*.txt);;All Files (*)")
        if path:
            path_edit.setText(path)

    def on_convert():
        path = path_edit.text().strip()
        if not path:
            QMessageBox.warning(window, "Warning", "Introduceți calea către fișier.")
            return
        if not os.path.isfile(path):
            QMessageBox.critical(window, "Error", "Fișierul nu există.")
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                txt = f.read()
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Nu se poate citi fișierul: {e}")
            return
        html = text_to_html(txt)
        text_edit.setPlainText(html)

    FTOK_PATH = "coada_msg"
    FTOK_PROJ_ID = ord('B')
    MSG_TYPE = 1

    def on_send():
        html = text_edit.toPlainText()
        if not html.strip():
            QMessageBox.warning(window, "Warning", "Zona HTML este goală. Convertește un fișier sau introdu HTML.")
            return
        try:
            if not os.path.exists(FTOK_PATH):
                QMessageBox.critical(window, "Error", f"Fișierul pentru ftok nu există: {FTOK_PATH}. Creează-l.")
                return
            key = sysv_ipc.ftok(FTOK_PATH, FTOK_PROJ_ID)
            mq = sysv_ipc.MessageQueue(key, sysv_ipc.IPC_CREAT)
            mq.send(html.encode('utf-8'), block=True, type=MSG_TYPE)
            QMessageBox.information(window, "Success", "HTML trimis către programul C (System V).")
        except Exception as e:
            QMessageBox.critical(window, "Error", f"Eroare la trimitere: {e}")


    browse_btn.clicked.connect(on_browse)
    convert_btn.clicked.connect(on_convert)
    send_btn.clicked.connect(on_send)

    window.show()
    app.exec()

if __name__ == "__main__":
    main()
