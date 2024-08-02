from PyQt5.QtWidgets import QInputDialog


class CreatePlaylistWindow(QInputDialog):
    def __init__(self, list_options: dict):
        super(CreatePlaylistWindow, self).__init__()
        self.setWindowTitle("Choose")
        self.setLabelText("Enter playlist name:")
        self.exec()

    def done(self, result: int) -> None:
        value = self.textValue()
        if result:
            print(value)
        else:
            print("NOPE")
        # FIXME: dialog box doesn't close on OK or Cancel buttons pressed...
        # do i have to manually implement the accept and reject when i override the done() func?
        self.close()
