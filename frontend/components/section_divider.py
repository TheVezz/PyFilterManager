from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QWidget
from qfluentwidgets import CaptionLabel


class SectionDivider(QWidget):
    def __init__(self, text: str, parent=None) -> None:
        super().__init__(parent)

        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 8, 0, 8)
        layout.setSpacing(12)

        left_line = QFrame(self)
        left_line.setFrameShape(QFrame.Shape.HLine)
        left_line.setFrameShadow(QFrame.Shadow.Plain)
        left_line.setProperty("class", "section-divider-line")

        label = CaptionLabel(text, self)
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        right_line = QFrame(self)
        right_line.setFrameShape(QFrame.Shape.HLine)
        right_line.setFrameShadow(QFrame.Shadow.Plain)
        right_line.setProperty("class", "section-divider-line")

        layout.addWidget(left_line, 1)
        layout.addWidget(label, 0)
        layout.addWidget(right_line, 1)
