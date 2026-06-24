from __future__ import annotations

import sys
from typing import Dict

from PyQt5 import QtCore, QtWidgets

from local_model_client import LocalModelError
from twin_core import DigitalAITwin


def app_stylesheet() -> str:
    return """
    QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 11pt; color: #E6E6E6; background: #0E0E10; }
    QMainWindow { background: #0E0E10; }
    QWizard { background: #0E0E10; color: #E6E6E6; }
    QWizardPage { background: #0E0E10; color: #E6E6E6; }
    QFrame#HeaderBar { background: #0E0E10; border-bottom: 1px solid #1F1F21; }
    QLabel#AppTitle { font-size: 13pt; font-weight: 600; color: #FFFFFF; letter-spacing: 0.5px; }
    QTabWidget::pane { border: none; background: #0E0E10; }
    QTabBar::tab { background: transparent; padding: 10px 16px; margin: 6px 10px; color: #9A9A9A; border-bottom: 2px solid transparent; }
    QTabBar::tab:selected { color: #FFFFFF; border-bottom: 2px solid #FFFFFF; }
    QTabBar::tab:hover { color: #FFFFFF; }
    QPushButton { background: transparent; color: #E6E6E6; border: 1px solid #2A2A2A; border-radius: 10px; padding: 10px 16px; }
    QPushButton:hover { background: #E6E6E6; color: #0E0E10; }
    QPushButton:pressed { background: #CFCFCF; color: #0E0E10; }
    QPushButton:disabled { color: #6A6A6A; border-color: #2A2A2A; }
    QLineEdit, QTextEdit, QLabel#StatusLabel { background: #111214; border: 1px solid #2A2A2A; border-radius: 12px; padding: 10px 14px; color: #E6E6E6; }
    QLineEdit#SearchInput { border-radius: 24px; padding: 14px 18px; font-size: 12pt; }
    QSpinBox { background: #111214; border: 1px solid #2A2A2A; border-radius: 8px; padding: 8px; color: #E6E6E6; }
    QComboBox { background: #111214; border: 1px solid #2A2A2A; border-radius: 8px; padding: 8px; color: #E6E6E6; }
    QComboBox::drop-down { border: none; }
    QComboBox::down-arrow { border: none; }
    QComboBox QAbstractItemView { background: #111214; color: #E6E6E6; selection-background-color: #2A2A2A; }
    QSlider::groove:horizontal { background: #2A2A2A; height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: #E6E6E6; border: 1px solid #2A2A2A; width: 18px; margin: -6px 0; border-radius: 9px; }
    QHeaderView::section { background: #0E0E10; color: #AFAFAF; padding: 8px; border: none; border-bottom: 1px solid #1F1F21; }
    QTableWidget { background: #111214; border: 1px solid #1F1F21; border-radius: 12px; gridline-color: #242428; color: #E6E6E6; }
    QFrame#Card { background: #121315; border: 1px solid #1F1F21; border-radius: 16px; }
    """


class Likert(QtWidgets.QWidget):
    def __init__(self, label: str, key: str, min_label: str = "1", max_label: str = "5"):
        super().__init__()
        self.key = key
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(label))
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(5)
        self.slider.setValue(3)
        layout.addWidget(QtWidgets.QLabel(min_label))
        layout.addWidget(self.slider)
        layout.addWidget(QtWidgets.QLabel(max_label))

    def value(self) -> int:
        return int(self.slider.value())


class SurveyWizard(QtWidgets.QWizard):
    survey_submitted = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Chloe Persona Survey")
        self.controls: Dict[str, object] = {}

        self.addPage(self._build_tone_page())
        self.addPage(self._build_values_page())
        self.addPage(self._build_personality_page())
        self.addPage(self._build_decision_page())
        self.addPage(self._build_mbti_page())
        self.addPage(self._build_examples_page())

        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.emit_results)

    def _build_tone_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Tone & Style")
        layout = QtWidgets.QVBoxLayout(page)
        fields = [
            Likert("Directness", "tone_directness", "Indirect", "Very direct"),
            Likert("Formality", "tone_formality", "Casual", "Very formal"),
            Likert("Empathy", "tone_empathy", "Low", "High"),
            Likert("Preferred message length", "msg_length", "Short", "Long"),
        ]
        for widget in fields:
            layout.addWidget(widget)
            self.controls[widget.key] = widget
        humor_row = QtWidgets.QHBoxLayout()
        humor_row.addWidget(QtWidgets.QLabel("Humor style"))
        humor = QtWidgets.QComboBox()
        humor.addItems(["light", "dry", "sarcastic", "playful", "none"])
        self.controls["humor_style"] = humor
        humor_row.addWidget(humor)
        layout.addLayout(humor_row)
        layout.addWidget(QtWidgets.QLabel("How often do you use humor?"))
        humor_frequency = Likert("Frequency", "humor_frequency", "Rarely", "Often")
        layout.addWidget(humor_frequency)
        self.controls["humor_frequency"] = humor_frequency
        return page

    def _build_values_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Core Values")
        layout = QtWidgets.QFormLayout(page)

        def spin() -> QtWidgets.QSpinBox:
            widget = QtWidgets.QSpinBox()
            widget.setRange(1, 5)
            widget.setValue(3)
            return widget

        values = {
            "val_honesty": spin(),
            "val_efficiency": spin(),
            "val_loyalty": spin(),
            "val_creativity": spin(),
            "val_frugality": spin(),
        }
        for key, widget in values.items():
            layout.addRow(key.replace("_", " ").title(), widget)
            self.controls[key] = widget
        catchphrase = QtWidgets.QLineEdit()
        layout.addRow("Catchphrase(s)", catchphrase)
        self.controls["catchphrase"] = catchphrase
        return page

    def _build_personality_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Personality Traits")
        layout = QtWidgets.QFormLayout(page)

        def likert_row(label: str, key: str) -> Likert:
            widget = Likert(label, key, "Low", "High")
            self.controls[key] = widget
            return widget

        for label, key in [
            ("Agreeableness", "agreeableness"),
            ("Conscientiousness", "conscientiousness"),
            ("Openness", "openness"),
            ("Extraversion", "extraversion"),
        ]:
            layout.addRow(likert_row(label, key))
        return page

    def _build_decision_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Decision Making")
        layout = QtWidgets.QVBoxLayout(page)
        widgets = [
            Likert("Data vs. Intuition", "decision_data_vs_intuition", "Intuition", "Data"),
            Likert("Risk tolerance", "risk_tolerance", "Low", "High"),
            Likert("Speed vs. Thoroughness", "speed_vs_thoroughness", "Thorough", "Fast"),
        ]
        for widget in widgets:
            layout.addWidget(widget)
            self.controls[widget.key] = widget
        return page

    def _build_mbti_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("MBTI Tendencies")
        layout = QtWidgets.QFormLayout(page)

        def likert_row(label: str, key: str, left: str, right: str) -> Likert:
            widget = Likert(label, key, left, right)
            self.controls[key] = widget
            return widget

        layout.addRow(likert_row("Extraversion vs Introversion", "mbti_ei", "Introvert", "Extravert"))
        layout.addRow(likert_row("Sensing vs Intuition", "mbti_sn", "Sensing", "Intuition"))
        layout.addRow(likert_row("Thinking vs Feeling", "mbti_tf", "Thinking", "Feeling"))
        layout.addRow(likert_row("Judging vs Perceiving", "mbti_jp", "Judging", "Perceiving"))
        return page

    def _build_examples_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage()
        page.setTitle("Examples")
        layout = QtWidgets.QFormLayout(page)
        example_one = QtWidgets.QLineEdit()
        example_two = QtWidgets.QLineEdit()
        example_three = QtWidgets.QLineEdit()
        layout.addRow("Past decision example 1", example_one)
        layout.addRow("Past decision example 2", example_two)
        layout.addRow("Past decision example 3", example_three)
        self.controls["example_decision1"] = example_one
        self.controls["example_decision2"] = example_two
        self.controls["example_decision3"] = example_three
        return page

    def emit_results(self) -> None:
        data: Dict[str, object] = {}
        for key, widget in self.controls.items():
            if isinstance(widget, Likert):
                data[key] = widget.value()
            elif isinstance(widget, QtWidgets.QSpinBox):
                data[key] = int(widget.value())
            elif isinstance(widget, QtWidgets.QComboBox):
                data[key] = widget.currentText()
            elif isinstance(widget, QtWidgets.QLineEdit):
                data[key] = widget.text().strip()
        self.survey_submitted.emit(data)


class ChatPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin, notify_error):
        super().__init__()
        self.twin = twin
        self.notify_error = notify_error
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        self.history = QtWidgets.QTextEdit()
        self.history.setReadOnly(True)
        self.history.setPlaceholderText("Chloe listens here...")

        input_row = QtWidgets.QHBoxLayout()
        self.input = QtWidgets.QLineEdit()
        self.input.setObjectName("SearchInput")
        self.input.setPlaceholderText("Ask or say anything...")
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_btn)

        card_layout.addWidget(self.history)
        card_layout.addLayout(input_row)
        root.addWidget(card)

    def on_send(self) -> None:
        message = self.input.text().strip()
        if not message:
            return
        self.history.append(f"You: {message}")
        try:
            reply = self.twin.chat(message)
            self.history.append(f"Chloe: {reply}")
            self.input.clear()
        except LocalModelError as exc:
            self.notify_error(str(exc))


class WhatWouldIDoPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin, notify_error):
        super().__init__()
        self.twin = twin
        self.notify_error = notify_error
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.situation = QtWidgets.QTextEdit()
        self.situation.setPlaceholderText("Describe a situation...")
        self.sim_btn = QtWidgets.QPushButton("Simulate Decision")
        self.sim_btn.clicked.connect(self.on_sim)
        self.output = QtWidgets.QTextEdit()
        self.output.setReadOnly(True)

        layout.addWidget(self.situation)
        layout.addWidget(self.sim_btn)
        layout.addWidget(self.output)
        root.addWidget(card)

    def on_sim(self) -> None:
        text = self.situation.toPlainText().strip()
        if not text:
            return
        try:
            reply = self.twin.simulate_decision(text)
            self.output.setPlainText(reply)
        except LocalModelError as exc:
            self.notify_error(str(exc))


class MemoryViewerPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        self.table = QtWidgets.QTableWidget(0, 4)
        self.table.setHorizontalHeaderLabels(["Type", "Text", "Timestamp", "Permanent"])
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QtWidgets.QHeaderView.ResizeToContents)

        btn_row = QtWidgets.QHBoxLayout()
        self.refresh_btn = QtWidgets.QPushButton("Refresh")
        self.delete_btn = QtWidgets.QPushButton("Delete Selected")
        self.refresh_btn.clicked.connect(self.refresh)
        self.delete_btn.clicked.connect(self.delete_selected)
        btn_row.addStretch(1)
        btn_row.addWidget(self.refresh_btn)
        btn_row.addWidget(self.delete_btn)

        layout.addLayout(btn_row)
        layout.addWidget(self.table)
        root.addWidget(card)

    def refresh(self) -> None:
        memories = self.twin.memories.list()
        self.table.setRowCount(len(memories))
        for index, memory in enumerate(memories):
            self.table.setItem(index, 0, QtWidgets.QTableWidgetItem(memory.type))
            self.table.setItem(index, 1, QtWidgets.QTableWidgetItem(memory.text[:200]))
            self.table.setItem(index, 2, QtWidgets.QTableWidgetItem(memory.timestamp.isoformat()))
            self.table.setItem(index, 3, QtWidgets.QTableWidgetItem("Yes" if memory.permanent else "No"))
        self.table.resizeColumnsToContents()

    def delete_selected(self) -> None:
        rows = sorted({item.row() for item in self.table.selectedIndexes()}, reverse=True)
        for row in rows:
            self.twin.memories.delete(row)
        self.refresh()


class SettingsPage(QtWidgets.QWidget):
    status_changed = QtCore.pyqtSignal(str)

    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame()
        card.setObjectName("Card")
        layout = QtWidgets.QFormLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)

        self.name_input = QtWidgets.QLineEdit(self.twin.persona.user_name)
        self.model_input = QtWidgets.QLineEdit(self.twin.model.model_name)
        self.base_url_input = QtWidgets.QLineEdit(self.twin.model.base_url)
        self.status_label = QtWidgets.QLabel()
        self.status_label.setObjectName("StatusLabel")
        layout.addRow("User Name", self.name_input)
        layout.addRow("Local Model Name", self.model_input)
        layout.addRow("Ollama Base URL", self.base_url_input)
        layout.addRow("Status", self.status_label)
        save = QtWidgets.QPushButton("Apply")
        save.clicked.connect(self.apply)
        layout.addRow(save)

        root.addWidget(card)
        self.refresh_status()

    def refresh_status(self) -> None:
        status = self.twin.api_status()
        mode = str(status.get("mode", "offline")).upper()
        error = str(status.get("last_error", "")).strip()
        text = f"Mode: {mode}"
        if error:
            text += f"\nLast error: {error}"
        self.status_label.setText(text)
        self.status_changed.emit(text)

    def apply(self) -> None:
        self.twin.set_user_name(self.name_input.text().strip(), persist=True)
        try:
            self.twin.set_local_model(self.model_input.text().strip(), self.base_url_input.text().strip(), persist=True)
            self.refresh_status()
        except LocalModelError as exc:
            self.status_label.setText(str(exc))
            self.status_changed.emit(str(exc))


class HeaderBar(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("HeaderBar")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        self.title = QtWidgets.QLabel("CHLOE // CYBERLIFE")
        self.title.setObjectName("AppTitle")
        layout.addWidget(self.title)
        layout.addStretch(1)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CHLOE")
        self.setMinimumSize(1024, 720)
        self.twin = DigitalAITwin()

        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        root = QtWidgets.QVBoxLayout(main)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        self.header = HeaderBar()
        root.addWidget(self.header)

        self.status_banner = QtWidgets.QLabel()
        self.status_banner.setObjectName("StatusLabel")
        root.addWidget(self.status_banner)

        tabs_container = QtWidgets.QWidget()
        tabs_layout = QtWidgets.QVBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(16, 16, 16, 16)
        tabs_layout.setSpacing(0)

        tabs = QtWidgets.QTabWidget()
        tabs_layout.addWidget(tabs)
        root.addWidget(tabs_container)

        self.survey = SurveyWizard()
        self.survey.survey_submitted.connect(self.on_survey)
        self.chat = ChatPage(self.twin, self.show_error)
        self.wwid = WhatWouldIDoPage(self.twin, self.show_error)
        self.memview = MemoryViewerPage(self.twin)
        self.settings = SettingsPage(self.twin)
        self.settings.status_changed.connect(self.status_banner.setText)

        tabs.addTab(self.survey, "Survey")
        tabs.addTab(self.chat, "Chat")
        tabs.addTab(self.wwid, "What Would I Do?")
        tabs.addTab(self.memview, "Memories")
        tabs.addTab(self.settings, "Settings")

        self.settings.refresh_status()
        self.memview.refresh()

    def on_survey(self, data: Dict[str, object]) -> None:
        try:
            self.twin.process_survey(data)
            self.memview.refresh()
            self.status_banner.setText("Survey processed successfully.")
        except LocalModelError as exc:
            self.show_error(str(exc))

    def show_error(self, message: str) -> None:
        self.status_banner.setText(message)
        QtWidgets.QMessageBox.warning(self, "CHLOE Node Error", message)


def main() -> None:
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet())
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
