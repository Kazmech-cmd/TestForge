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
import logging
from datetime import datetime
import time



os.makedirs("logs", exist_ok=True)
logging.basicConfig(
    filename="logs/testforge.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    encoding="utf-8",
)

LOG_MAX_AGE_DAYS = 30


def clean_old_logs():
    if not os.path.exists("logs/testforge.log"):
        return
    file_age_days = (time.time() - os.path.getmtime("logs/testforge.log")) / 86400
    if file_age_days > LOG_MAX_AGE_DAYS:
        os.remove("logs/testforge.log")


clean_old_logs()

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
        self.setFixedSize(360, 500)
        self.setWindowIcon(QIcon("assets/testforge_logo.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(10)
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
        clear_logs_button = QPushButton("Очистить логи")
        clear_logs_button.setObjectName("reportButton")
        clear_logs_button.clicked.connect(self.clear_logs)
        layout.addWidget(clear_logs_button)
        report_button.setObjectName("reportButton")
        report_button.clicked.connect(self.open_report)
        layout.addWidget(report_button)

        self.status_label = QLabel("Готов к запуску")
        self.status_label.setObjectName("status")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.status_label)

        self.apply_styles()

    def update_input_field(self):
        self.target_input.clear()
        if self.web_radio.isChecked():
            self.target_input.setPlaceholderText("https://example.com")
        elif self.api_radio.isChecked():
            self.target_input.setPlaceholderText("https://jsonplaceholder.typicode.com/posts/1")

    def clear_logs(self):
        for handler in logging.root.handlers[:]:
            handler.close()
            logging.root.removeHandler(handler)

        if os.path.exists("logs/testforge.log"):
            archive_name = f"logs/testforge_archive_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            os.rename("logs/testforge.log", archive_name)
        else:
            archive_name = "не найден"

        logging.basicConfig(
            filename="logs/testforge.log",
            level=logging.INFO,
            format="%(asctime)s - %(levelname)s - %(message)s",
            encoding="utf-8",
        )
        logging.info(f"Логи очищены пользователем, старый файл сохранён как {archive_name}")

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
            logging.info(f"Запуск веб-теста для {value}")
            self.thread = TestRunnerThread(target="web", value=value)
        elif self.api_radio.isChecked():
            value = value or "https://jsonplaceholder.typicode.com/posts/1"
            self.status_label.setText(f"Проверяем {value}...")
            logging.info(f"Запуск API-теста для {value}")
            self.thread = TestRunnerThread(target="api", value=value)
        else:
            return

        self.thread.finished_signal.connect(self.on_tests_finished)
        self.thread.start()

    def on_tests_finished(self, summary):
        self.status_label.setText(summary)
        logging.info(f"Прогон завершён: {summary}")

    def open_report(self):
        subprocess.Popen(["allure", "serve", "allure-results"], shell=True)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()