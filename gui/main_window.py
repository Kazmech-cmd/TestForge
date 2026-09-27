import os
import re
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QLineEdit, QRadioButton, QButtonGroup
)


class TestRunnerThread(QThread):
    finished_signal = pyqtSignal(str)

    def __init__(self, target, value=None):
        super().__init__()
        self.target = target
        self.value = value

    def run(self):
        env = os.environ.copy()

        if self.target == "web":
            env["TEST_URL"] = self.value
            test_path = "tests/test_web.py"
        elif self.target == "api":
            env["TEST_API_URL"] = self.value
            test_path = "tests/test_api.py"
        else:
            test_path = "tests/"

        result = subprocess.run(
            ["python", "-m", "pytest", test_path, "-v", "--headed",
             "--alluredir=allure-results", "--clean-alluredir"],
            capture_output=True,
            text=True,
            env=env,
        )
        summary = self.parse_summary(result.stdout)
        self.finished_signal.emit(summary)

    def parse_summary(self, output):
        match = re.search(r"=+ (.+?) in [\d.]+s =+", output)
        if match:
            return match.group(1)
        return "Не удалось разобрать результат"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TestForge")
        self.setFixedSize(360, 440)
        self.setWindowIcon(QIcon("assets/testforge_logo.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(14)
        central_widget.setLayout(layout)

        title = QLabel("TestForge")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        self.web_radio = QRadioButton("Веб-сайт")
        self.web_radio.setChecked(True)
        self.api_radio = QRadioButton("API")
        self.desktop_radio = QRadioButton("Десктоп-приложение (скоро)")
        self.desktop_radio.setEnabled(False)

        self.mode_group = QButtonGroup()
        self.mode_group.addButton(self.web_radio)
        self.mode_group.addButton(self.api_radio)
        self.mode_group.addButton(self.desktop_radio)

        self.web_radio.toggled.connect(self.update_input_field)
        self.api_radio.toggled.connect(self.update_input_field)

        layout.addWidget(self.web_radio)
        layout.addWidget(self.api_radio)
        layout.addWidget(self.desktop_radio)

        self.target_input = QLineEdit()
        self.target_input.setObjectName("urlInput")
        layout.addWidget(self.target_input)
        self.update_input_field()

        run_button = QPushButton("Запустить")
        run_button.setObjectName("runButton")
        run_button.clicked.connect(self.run_tests)
        layout.addWidget(run_button)

        report_button = QPushButton("Открыть отчёт")
        report_button.setObjectName("reportButton")
        report_button.clicked.connect(self.open_report)
        layout.addWidget(report_button)

        self.status_label = QLabel("Готов к запуску")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.apply_styles()

    def update_input_field(self):
        if self.web_radio.isChecked():
            self.target_input.setPlaceholderText("https://example.com")
        elif self.api_radio.isChecked():
            self.target_input.setPlaceholderText("https://jsonplaceholder.typicode.com/posts/1")

    def apply_styles(self):
        self.setStyleSheet("""
            QMainWindow {
                background-color: #1e1e2e;
            }
            #title {
                color: #cdd6f4;
                font-size: 22px;
                font-weight: bold;
                margin-bottom: 10px;
            }
            QRadioButton {
                color: #cdd6f4;
                font-size: 13px;
            }
            QRadioButton:disabled {
                color: #6c7086;
            }
            #urlInput {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 10px;
                font-size: 13px;
            }
            #urlInput:focus {
                border: 1px solid #89b4fa;
            }
            QPushButton {
                background-color: #313244;
                color: #cdd6f4;
                border: none;
                border-radius: 8px;
                padding: 12px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: #45475a;
            }
            QPushButton:pressed {
                background-color: #585b70;
            }
            #runButton {
                background-color: #89b4fa;
                color: #1e1e2e;
                font-weight: bold;
            }
            #runButton:hover {
                background-color: #74a8f9;
            }
            #status {
                color: #a6adc8;
                font-size: 13px;
                margin-top: 10px;
            }
        """)

    def run_tests(self):
        value = self.target_input.text().strip()

        if self.web_radio.isChecked():
            value = value or "https://example.com"
            self.status_label.setText(f"Проверяем {value}...")
            self.thread = TestRunnerThread(target="web", value=value)
        elif self.api_radio.isChecked():
            value = value or "https://jsonplaceholder.typicode.com/posts/1"
            self.status_label.setText(f"Проверяем {value}...")
            self.thread = TestRunnerThread(target="api", value=value)
        else:
            return

        self.thread.finished_signal.connect(self.on_tests_finished)
        self.thread.start()

    def on_tests_finished(self, summary):
        self.status_label.setText(summary)

    def open_report(self):
        subprocess.Popen(["allure", "serve", "allure-results"], shell=True)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()