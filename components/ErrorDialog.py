from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QPushButton

class ErrorDialog(QDialog):
    def __init__(self, message, parent=None):
        super().__init__(parent)
        self.setWindowTitle("An error occurred")
        self.setGeometry(100,100,400,200)
        layout = QVBoxLayout()

        self.label = QLabel(message)
        layout.addWidget(self.label)

        self.button = QPushButton("ok")
        self.button.clicked.connect(self.accept) # press ok
        layout.addWidget(self.button)

        self.setLayout(layout)
