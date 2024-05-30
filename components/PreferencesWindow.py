from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton
from PyQt5.QtGui import QFont


class PreferencesWindow(QDialog):
    def __init__(self, config):
        super(PreferencesWindow, self).__init__()
        self.setWindowTitle("Preferences")
        self.config = config
        layout = QVBoxLayout()

        label = QLabel("Preferences Window")
        layout.addWidget(label)

        # Labels & input fields
        self.input_fields = {}
        for category in self.config.sections():
            category_label = QLabel(f"{category}")
            category_label.setFont(QFont("", weight=QFont.Bold))  # bold category
            category_label.setStyleSheet(
                "text-transform:uppercase;"
            )  # uppercase category
            layout.addWidget(category_label)
            for key in self.config[category]:
                label = QLabel(key)
                input_field = QLineEdit(self.config[category][key])
                layout.addWidget(label)
                layout.addWidget(input_field)
                self.input_fields[key] = input_field

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_preferences)
        layout.addWidget(save_button)
        self.setLayout(layout)

    def save_preferences(self):
        # Upcate the config fields
        for key in self.input_fields:
            for category in self.config.sections():
                if key in self.config[category]:
                    self.config[category][key] = self.input_fields[key].text()

        # Write the config file
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)

        self.close()
