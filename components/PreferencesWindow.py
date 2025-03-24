from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QHBoxLayout,
    QListWidget,
    QWidget,
    QDial,
)
from PyQt5.QtGui import QFont


class PreferencesWindow(QDialog):
    def __init__(self, config):
        super(PreferencesWindow, self).__init__()
        # Config
        self.setWindowTitle("Preferences")
        self.setMinimumSize(800, 800)
        self.config = config
        self.current_category = ""

        # Widgets
        self.content_area = QWidget()
        nav_pane = QListWidget()

        # Layouts
        central_widget = QWidget()
        main_layout = QHBoxLayout()
        self.content_layout = QVBoxLayout()
        self.content_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        central_widget.setLayout(main_layout)
        self.content_area.setLayout(self.content_layout)

        # Navigation pane
        for category in self.config.sections():
            nav_pane.addItem(category)
        nav_pane.itemClicked.connect(self.on_nav_item_clicked)
        nav_pane.setCurrentRow(0)
        first_category = self.config.sections()[0]
        self.on_nav_item_clicked(first_category)

        # # Labels & input fields
        self.input_fields = {}

        # Add widgets to the layout
        main_layout.addWidget(nav_pane)
        main_layout.addWidget(self.content_area)

        # Set the layout
        self.setLayout(main_layout)

    def on_nav_item_clicked(self, item):
        self.clear_layout(self.content_layout)
        self.input_fields = {}
        if isinstance(item, str):
            self.current_category = item
        else:
            self.current_category = item.text()
        category_label = QLabel(f"{self.current_category}")
        category_label.setFont(QFont("Sans", weight=QFont.Bold))
        category_label.setStyleSheet("text-transform:uppercase;")
        self.content_layout.addWidget(category_label)
        for key in self.config[self.current_category]:
            label = QLabel(key)
            input_field = QLineEdit(self.config[self.current_category][key])
            self.content_layout.addWidget(label)
            self.content_layout.addWidget(input_field)
            self.input_fields[key] = input_field

        # Save button
        save_button = QPushButton("Save")
        save_button.clicked.connect(self.save_preferences)
        self.content_layout.addWidget(save_button)

    def clear_layout(self, layout):
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

    def save_preferences(self):
        print('im saving')
        # Upcate the config fields
        for key in self.input_fields:
            for category in self.config.sections():
                if key in self.config[category]:
                    self.config[self.current_category][key] = self.input_fields[
                        key
                    ].text()

        # Write the config file
        with open("config.ini", "w") as configfile:
            self.config.write(configfile)
        # self.close()
