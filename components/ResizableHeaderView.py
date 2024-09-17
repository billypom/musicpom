from PyQt5.QtWidgets import QHeaderView
from PyQt5.QtCore import Qt
import configparser


class ResizableHeaderView(QHeaderView):
    def __init__(self, orientation, parent=None):
        super().__init__(orientation, parent)
        self.config = configparser.ConfigParser()
        self.config.read("config.ini")
        # FIXME: last column needs to not leave the screen when other columns become big...
        # howwww
        table_view_column_widths = str(self.config["table"]["column_widths"]).split(",")
        for i in range(parent.model.columnCount() - 1):
            self.setColumnWidth(i, int(table_view_column_widths[i]))
        self.setSectionsMovable(True)
        self.setSectionResizeMode(QHeaderView.Interactive)
        self.setStretchLastSection(True)
        self.min_section_size = 50
        self.default_column_proportions = [1, 1, 1, 1, 1, 1, 1, 1]

    def set_default_column_proportions(self, proportions):
        self.default_column_proportions = proportions

    def resizeEvent(self, e):
        super().resizeEvent(e)
        self.adjust_section_sizes()

    def sectionResized(self, logicalIndex, oldSize, newSize):
        super().sectionResized(logicalIndex, oldSize, newSize)
        self.adjust_section_sizes()

    def adjust_section_sizes(self):
        total_width = self.width()
        column_count = self.count()
        if not self.default_column_proportions:
            self.default_column_proportions = [1] * column_count

        # Calculate the total proportion
        total_proportion = sum(self.default_column_proportions)

        # Calculate sizes based on proportions
        sizes = [
            max(self.min_section_size, int(total_width * prop / total_proportion))
            for prop in self.default_column_proportions
        ]

        # Adjust sizes to fit exactly
        extra = total_width - sum(sizes)
        for i in range(abs(extra)):
            sizes[i % column_count] += 1 if extra > 0 else -1

        # Apply sizes
        for i in range(column_count):
            self.resizeSection(i, sizes[i])
