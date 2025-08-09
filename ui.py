from __future__ import annotations
import sys
from typing import Dict
from PyQt5 import QtCore, QtWidgets, QtGui

from twin_core import DigitalAITwin
from models import MemoryItem


def app_stylesheet() -> str:
    return """
    /* Minimal Black & White Futuristic Theme */
    QWidget { font-family: 'Segoe UI', 'Arial'; font-size: 11pt; color: #E6E6E6; background: #0E0E10; }
    QMainWindow { background: #0E0E10; }

    /* Survey Wizard */
    QWizard { background: #0E0E10; color: #E6E6E6; }
    QWizardPage { background: #0E0E10; color: #E6E6E6; }

    /* Header bar */
    QFrame#HeaderBar { background: #0E0E10; border-bottom: 1px solid #1F1F21; }
    QLabel#AppTitle { font-size: 13pt; font-weight: 600; color: #FFFFFF; letter-spacing: 0.5px; }

    /* Tabs */
    QTabWidget::pane { border: none; background: #0E0E10; }
    QTabBar::tab { background: transparent; padding: 10px 16px; margin: 6px 10px; color: #9A9A9A; border-bottom: 2px solid transparent; }
    QTabBar::tab:selected { color: #FFFFFF; border-bottom: 2px solid #FFFFFF; }
    QTabBar::tab:hover { color: #FFFFFF; }

    /* Buttons */
    QPushButton { background: transparent; color: #E6E6E6; border: 1px solid #2A2A2A; border-radius: 10px; padding: 10px 16px; }
    QPushButton:hover { background: #E6E6E6; color: #0E0E10; }
    QPushButton:pressed { background: #CFCFCF; color: #0E0E10; }
    QPushButton:disabled { color: #6A6A6A; border-color: #2A2A2A; }

    /* Inputs */
    QLineEdit, QTextEdit { background: #111214; border: 1px solid #2A2A2A; border-radius: 12px; padding: 10px 14px; color: #E6E6E6; }
    QLineEdit::placeholder, QTextEdit::placeholder { color: #6E6E6E; }
    QLineEdit#SearchInput { border-radius: 24px; padding: 14px 18px; font-size: 12pt; }

    /* Form controls */
    QSpinBox { background: #111214; border: 1px solid #2A2A2A; border-radius: 8px; padding: 8px; color: #E6E6E6; }
    QComboBox { background: #111214; border: 1px solid #2A2A2A; border-radius: 8px; padding: 8px; color: #E6E6E6; }
    QComboBox::drop-down { border: none; }
    QComboBox::down-arrow { border: none; }
    QComboBox QAbstractItemView { background: #111214; color: #E6E6E6; selection-background-color: #2A2A2A; }

    /* Sliders */
    QSlider::groove:horizontal { background: #2A2A2A; height: 6px; border-radius: 3px; }
    QSlider::handle:horizontal { background: #E6E6E6; border: 1px solid #2A2A2A; width: 18px; margin: -6px 0; border-radius: 9px; }
    QSlider::handle:horizontal:hover { background: #FFFFFF; }

    /* Tables */
    QHeaderView::section { background: #0E0E10; color: #AFAFAF; padding: 8px; border: none; border-bottom: 1px solid #1F1F21; }
    QTableWidget { background: #111214; border: 1px solid #1F1F21; border-radius: 12px; gridline-color: #242428; color: #E6E6E6; }
    QTableWidget QTableCornerButton::section { background: #0E0E10; border: none; }

    /* Card */
    QFrame#Card { background: #121315; border: 1px solid #1F1F21; border-radius: 16px; }
    """


class Likert(QtWidgets.QWidget):
    def __init__(self, label: str, key: str, min_label: str = "1", max_label: str = "5"):
        super().__init__()
        self.key = key
        layout = QtWidgets.QHBoxLayout(self)
        layout.addWidget(QtWidgets.QLabel(label))
        self.slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.slider.setMinimum(1); self.slider.setMaximum(5); self.slider.setValue(3)
        layout.addWidget(QtWidgets.QLabel(min_label))
        layout.addWidget(self.slider)
        layout.addWidget(QtWidgets.QLabel(max_label))

    def value(self) -> int:
        return int(self.slider.value())


class SurveyWizard(QtWidgets.QWizard):
    survey_submitted = QtCore.pyqtSignal(dict)

    def __init__(self):
        super().__init__()
        self.setWindowTitle("Onboarding Survey")
        self.pages: Dict[int, QtWidgets.QWizardPage] = {}
        self.controls: Dict[str, object] = {}

        self.addPage(self._build_tone_page())
        self.addPage(self._build_values_page())
        self.addPage(self._build_personality_page())
        self.addPage(self._build_decision_page())
        self.addPage(self._build_mbti_page())
        self.addPage(self._build_examples_page())

        self.button(QtWidgets.QWizard.FinishButton).clicked.connect(self.emit_results)

    def _build_tone_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("Tone & Style")
        layout = QtWidgets.QVBoxLayout(page)
        fields = [
            Likert("Directness", "tone_directness", "Indirect", "Very direct"),
            Likert("Formality", "tone_formality", "Casual", "Very formal"),
            Likert("Empathy", "tone_empathy", "Low", "High"),
            Likert("Preferred message length", "msg_length", "Short", "Long"),
        ]
        for w in fields:
            layout.addWidget(w)
            self.controls[w.key] = w
        humor_row = QtWidgets.QHBoxLayout()
        humor_row.addWidget(QtWidgets.QLabel("Humor style"))
        humor = QtWidgets.QComboBox(); humor.addItems(["light", "dry", "sarcastic", "playful", "none"]) 
        self.controls["humor_style"] = humor
        humor_row.addWidget(humor)
        layout.addLayout(humor_row)
        layout.addWidget(QtWidgets.QLabel("How often do you use humor?"))
        hf = Likert("Frequency", "humor_frequency", "Rarely", "Often")
        layout.addWidget(hf); self.controls["humor_frequency"] = hf
        return page

    def _build_values_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("Core Values")
        layout = QtWidgets.QFormLayout(page)
        def spin():
            s = QtWidgets.QSpinBox(); s.setRange(1, 5); s.setValue(3); return s
        vals = {
            "val_honesty": spin(),
            "val_efficiency": spin(),
            "val_loyalty": spin(),
            "val_creativity": spin(),
            "val_frugality": spin(),
        }
        for k, w in vals.items():
            layout.addRow(k.replace("_", " ").title(), w)
            self.controls[k] = w
        catch = QtWidgets.QLineEdit()
        layout.addRow("Catchphrase(s)", catch)
        self.controls["catchphrase"] = catch
        return page

    def _build_personality_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("Personality Traits")
        layout = QtWidgets.QFormLayout(page)
        def likert_row(label, key):
            w = Likert(label, key, "Low", "High"); self.controls[key] = w; return w
        for label, key in [
            ("Agreeableness", "agreeableness"),
            ("Conscientiousness", "conscientiousness"),
            ("Openness", "openness"),
            ("Extraversion", "extraversion"),
        ]:
            layout.addRow(likert_row(label, key))
        return page

    def _build_decision_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("Decision Making")
        layout = QtWidgets.QVBoxLayout(page)
        widgets = [
            Likert("Data vs. Intuition", "decision_data_vs_intuition", "Intuition", "Data"),
            Likert("Risk tolerance", "risk_tolerance", "Low", "High"),
            Likert("Speed vs. Thoroughness", "speed_vs_thoroughness", "Thorough", "Fast"),
        ]
        for w in widgets:
            layout.addWidget(w); self.controls[w.key] = w
        return page

    def _build_mbti_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("MBTI Tendencies")
        layout = QtWidgets.QFormLayout(page)
        def likert_row(label, key, left, right):
            w = Likert(label, key, left, right); self.controls[key] = w; return w
        layout.addRow(likert_row("Extraversion vs Introversion", "mbti_ei", "Introvert", "Extravert"))
        layout.addRow(likert_row("Sensing vs Intuition", "mbti_sn", "Sensing", "Intuition"))
        layout.addRow(likert_row("Thinking vs Feeling", "mbti_tf", "Thinking", "Feeling"))
        layout.addRow(likert_row("Judging vs Perceiving", "mbti_jp", "Judging", "Perceiving"))
        return page

    def _build_examples_page(self) -> QtWidgets.QWizardPage:
        page = QtWidgets.QWizardPage(); page.setTitle("Examples")
        layout = QtWidgets.QFormLayout(page)
        ex1 = QtWidgets.QLineEdit(); ex2 = QtWidgets.QLineEdit(); ex3 = QtWidgets.QLineEdit()
        layout.addRow("Past decision example 1", ex1)
        layout.addRow("Past decision example 2", ex2)
        layout.addRow("Past decision example 3", ex3)
        self.controls["example_decision1"] = ex1
        self.controls["example_decision2"] = ex2
        self.controls["example_decision3"] = ex3
        return page

    def emit_results(self):
        data: Dict[str, object] = {}
        for key, w in self.controls.items():
            if isinstance(w, Likert):
                data[key] = w.value()
            elif isinstance(w, QtWidgets.QSpinBox):
                data[key] = int(w.value())
            elif isinstance(w, QtWidgets.QComboBox):
                data[key] = w.currentText()
            elif isinstance(w, QtWidgets.QLineEdit):
                data[key] = w.text().strip()
        self.survey_submitted.emit(data)


class ChatPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame(); card.setObjectName("Card")
        card_layout = QtWidgets.QVBoxLayout(card)
        card_layout.setContentsMargins(24, 24, 24, 24)
        card_layout.setSpacing(12)

        self.history = QtWidgets.QTextEdit(); self.history.setReadOnly(True)
        self.history.setPlaceholderText("Your conversation will appear here…")

        input_row = QtWidgets.QHBoxLayout()
        self.input = QtWidgets.QLineEdit(); self.input.setObjectName("SearchInput"); self.input.setPlaceholderText("Ask or say anything…")
        self.send_btn = QtWidgets.QPushButton("Send")
        self.send_btn.clicked.connect(self.on_send)
        input_row.addWidget(self.input)
        input_row.addWidget(self.send_btn)

        card_layout.addWidget(self.history)
        card_layout.addLayout(input_row)

        root.addWidget(card)

    def on_send(self):
        msg = self.input.text().strip()
        if not msg:
            return
        self.history.append(f"You: {msg}")
        reply = self.twin.chat(msg)
        self.history.append(f"Twin: {reply}")
        self.input.clear()


class WhatWouldIDoPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame(); card.setObjectName("Card")
        layout = QtWidgets.QVBoxLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(12)

        self.situation = QtWidgets.QTextEdit(); self.situation.setPlaceholderText("Describe a situation…")
        self.sim_btn = QtWidgets.QPushButton("Simulate Decision")
        self.sim_btn.clicked.connect(self.on_sim)
        self.output = QtWidgets.QTextEdit(); self.output.setReadOnly(True)

        layout.addWidget(self.situation)
        layout.addWidget(self.sim_btn)
        layout.addWidget(self.output)
        root.addWidget(card)

    def on_sim(self):
        text = self.situation.toPlainText().strip()
        if not text:
            return
        reply = self.twin.simulate_decision(text)
        self.output.setPlainText(reply)


class MemoryViewerPage(QtWidgets.QWidget):
    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame(); card.setObjectName("Card")
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

    def refresh(self):
        mems = self.twin.memories.list()
        self.table.setRowCount(len(mems))
        for i, m in enumerate(mems):
            self.table.setItem(i, 0, QtWidgets.QTableWidgetItem(m.type))
            self.table.setItem(i, 1, QtWidgets.QTableWidgetItem(m.text[:200]))
            self.table.setItem(i, 2, QtWidgets.QTableWidgetItem(m.timestamp.isoformat()))
            self.table.setItem(i, 3, QtWidgets.QTableWidgetItem("Yes" if m.permanent else "No"))
        self.table.resizeColumnsToContents()

    def delete_selected(self):
        rows = sorted({idx.row() for idx in self.table.selectedIndexes()}, reverse=True)
        for r in rows:
            self.twin.memories.delete(r)
        self.refresh()


class SettingsPage(QtWidgets.QWidget):
    key_applied = QtCore.pyqtSignal(bool)
    def __init__(self, twin: DigitalAITwin):
        super().__init__()
        self.twin = twin
        root = QtWidgets.QVBoxLayout(self)
        root.setContentsMargins(24, 24, 24, 24)
        root.setSpacing(18)

        card = QtWidgets.QFrame(); card.setObjectName("Card")
        layout = QtWidgets.QFormLayout(card)
        layout.setContentsMargins(24, 24, 24, 24)

        self.name_input = QtWidgets.QLineEdit(self.twin.persona.user_name)
        self.api_key_input = QtWidgets.QLineEdit(); self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
        layout.addRow("User Name", self.name_input)
        layout.addRow("Gemini API Key", self.api_key_input)
        save = QtWidgets.QPushButton("Apply")
        save.clicked.connect(self.apply)
        layout.addRow(save)

        root.addWidget(card)

    def apply(self):
        self.twin.persona.user_name = self.name_input.text().strip() or "You"
        key = self.api_key_input.text().strip()
        ok = False
        if key:
            self.twin.set_gemini_key(key)
            # best-effort check
            ok = bool(getattr(self.twin.gemini, "_have_sdk", False) and getattr(self.twin.gemini, "_configured", False))
        self.key_applied.emit(ok)


class HeaderBar(QtWidgets.QFrame):
    def __init__(self):
        super().__init__()
        self.setObjectName("HeaderBar")
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(16, 8, 16, 8)
        layout.setSpacing(12)
        self.title = QtWidgets.QLabel("Digital AI Twin")
        self.title.setObjectName("AppTitle")
        layout.addWidget(self.title)
        layout.addStretch(1)


class MainWindow(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Digital AI Twin")
        self.setMinimumSize(1024, 720)
        self.twin = DigitalAITwin()

        main = QtWidgets.QWidget()
        self.setCentralWidget(main)
        v = QtWidgets.QVBoxLayout(main)
        v.setContentsMargins(0, 0, 0, 0)
        v.setSpacing(0)

        self.header = HeaderBar()
        v.addWidget(self.header)

        tabs_container = QtWidgets.QWidget()
        tabs_layout = QtWidgets.QVBoxLayout(tabs_container)
        tabs_layout.setContentsMargins(16, 16, 16, 16)
        tabs_layout.setSpacing(0)

        tabs = QtWidgets.QTabWidget()
        tabs_layout.addWidget(tabs)
        v.addWidget(tabs_container)

        self.survey = SurveyWizard()
        self.survey.survey_submitted.connect(self.on_survey)
        self.chat = ChatPage(self.twin)
        self.wwid = WhatWouldIDoPage(self.twin)
        self.memview = MemoryViewerPage(self.twin)
        self.settings = SettingsPage(self.twin)

        tabs.addTab(self.survey, "Survey")
        tabs.addTab(self.chat, "Chat")
        tabs.addTab(self.wwid, "What Would I Do?")
        tabs.addTab(self.memview, "Memories")
        tabs.addTab(self.settings, "Settings")

    def on_survey(self, data: Dict[str, object]):
        self.twin.process_survey(data)
        self.memview.refresh()

    # Gemini status indicator removed for a cleaner minimal UI


def main():
    app = QtWidgets.QApplication(sys.argv)
    app.setStyleSheet(app_stylesheet())
    w = MainWindow(); w.show()
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
