from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt
import configparser


class ResizableHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        self.parent = parent
        # FIXME: last column needs to not leave the screen when other columns become big...
        # howwww
        table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        for i in range(parent.model.columnCount() - 1):
            self.setColumnWidth(i, int(table_view_column_widths[i]))
        self.setStretchLastSection(True)
        self.setSectionResizeMode(QHeaderView.Interactive)

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_section_sizes()

    def sectionResized(self, logicalIndex, oldSize, newSize):
        super().sectionResized(logicalIndex, oldSize, newSize)
        self.adjust_section_sizes()

    def adjust_section_sizes(self):
        column_count = self.count()
        total_width = 0

        for i in range(self.parent.model.columnCount()):
            total_width += self.parent.model.columnWidth(i)
        print(f"total_width = {total_width}")

        if not self.default_column_proportions:
            self.default_column_proportions = [1] * column_count
