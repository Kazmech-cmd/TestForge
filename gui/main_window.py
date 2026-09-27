import re
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget
)


class TestRunnerThread(QThread):
    finished_signal = pyqtSignal(str)

    def run(self):
        result = subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--headed",
             "--alluredir=allure-results", "--clean-alluredir"],
            capture_output=True,
            text=True,
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
        self.setFixedSize(360, 320)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(16)
        central_widget.setLayout(layout)

        title = QLabel("TestForge")
        title.setObjectName("title")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        run_button = QPushButton("Запустить тесты")
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
        self.status_label.setText("Тесты выполняются...")
        self.thread = TestRunnerThread()
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