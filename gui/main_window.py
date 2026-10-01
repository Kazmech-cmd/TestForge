import os
import re
import subprocess
import sys
import logging
import time
from datetime import datetime
from PyQt6.QtCore import QThread, pyqtSignal, Qt
from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QPushButton, QLabel,
    QVBoxLayout, QWidget, QLineEdit, QRadioButton, QButtonGroup,
    QComboBox, QTextEdit, QMessageBox
)


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

    def __init__(self, target, value=None, method="GET", body="", headers="",
                 required_fields="", expected_text="", selector="", scenario=""):
        super().__init__()
        self.target = target
        self.value = value
        self.method = method
        self.body = body
        self.headers = headers
        self.required_fields = required_fields
        self.expected_text = expected_text
        self.selector = selector
        self.scenario = scenario

    def run(self):
        env = os.environ.copy()

        if self.target == "web":
            env["TEST_URL"] = self.value
            env["TEST_EXPECTED_TEXT"] = self.expected_text
            env["TEST_SELECTOR"] = self.selector
            env["TEST_SCENARIO"] = self.scenario
            test_path = "tests/test_web.py"
        elif self.target == "api":
            env["TEST_API_URL"] = self.value
            env["TEST_API_METHOD"] = self.method
            env["TEST_API_BODY"] = self.body
            env["TEST_API_HEADERS"] = self.headers
            env["TEST_API_REQUIRED_FIELDS"] = self.required_fields
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
        self.setFixedSize(380, 870)
        self.setWindowIcon(QIcon("assets/testforge_logo.png"))

        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        layout = QVBoxLayout()
        layout.setContentsMargins(40, 30, 40, 30)
        layout.setSpacing(8)
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

        self.method_combo = QComboBox()
        self.method_combo.setObjectName("methodCombo")
        self.method_combo.addItems(["GET", "POST", "PUT", "DELETE"])
        self.method_combo.setVisible(False)
        self.method_combo.currentTextChanged.connect(self.update_body_visibility)
        layout.addWidget(self.method_combo)

        self.target_input = QLineEdit()
        self.target_input.setObjectName("urlInput")
        layout.addWidget(self.target_input)

        # --- Поля для веб-тестов ---
        self.web_text_label = QLabel("Ожидаемый текст на странице (необязательно):")
        self.web_text_label.setObjectName("fieldLabel")
        layout.addWidget(self.web_text_label)

        self.web_text_input = QLineEdit()
        self.web_text_input.setObjectName("urlInput")
        self.web_text_input.setPlaceholderText("например, Добро пожаловать")
        layout.addWidget(self.web_text_input)

        self.web_selector_label = QLabel("CSS-селектор элемента (необязательно):")
        self.web_selector_label.setObjectName("fieldLabel")
        layout.addWidget(self.web_selector_label)

        self.web_selector_input = QLineEdit()
        self.web_selector_input.setObjectName("urlInput")
        self.web_selector_input.setPlaceholderText("например, button.submit")
        layout.addWidget(self.web_selector_input)

        self.web_scenario_label = QLabel("Сценарий действий (необязательно):")
        self.web_scenario_label.setObjectName("fieldLabel")
        layout.addWidget(self.web_scenario_label)

        self.web_scenario_input = QTextEdit()
        self.web_scenario_input.setObjectName("bodyInput")
        self.web_scenario_input.setPlaceholderText('fill: input[name="email"] | test@mail.com\nclick: button[type="submit"]')
        self.web_scenario_input.setFixedHeight(70)
        layout.addWidget(self.web_scenario_input)

        # --- Поля для API-тестов ---
        self.headers_label = QLabel("Заголовки (JSON, необязательно):")
        self.headers_label.setObjectName("fieldLabel")
        layout.addWidget(self.headers_label)

        self.headers_input = QTextEdit()
        self.headers_input.setObjectName("bodyInput")
        self.headers_input.setPlaceholderText('{"Authorization": "Bearer токен"}')
        self.headers_input.setFixedHeight(55)
        layout.addWidget(self.headers_input)

        self.body_label = QLabel("Тело запроса (JSON):")
        self.body_label.setObjectName("fieldLabel")
        layout.addWidget(self.body_label)

        self.body_input = QTextEdit()
        self.body_input.setObjectName("bodyInput")
        self.body_input.setPlaceholderText('{"key": "value"}')
        self.body_input.setFixedHeight(55)
        layout.addWidget(self.body_input)

        self.fields_label = QLabel("Обязательные поля в ответе (через запятую):")
        self.fields_label.setObjectName("fieldLabel")
        layout.addWidget(self.fields_label)

        self.fields_input = QLineEdit()
        self.fields_input.setObjectName("urlInput")
        self.fields_input.setPlaceholderText("id, title, userId")
        layout.addWidget(self.fields_input)

        self.update_input_field()

        run_button = QPushButton("Запустить")
        run_button.setObjectName("runButton")
        run_button.clicked.connect(self.run_tests)
        layout.addWidget(run_button)

        clear_logs_button = QPushButton("Очистить логи")
        clear_logs_button.setObjectName("reportButton")
        clear_logs_button.clicked.connect(self.clear_logs)
        layout.addWidget(clear_logs_button)

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
        self.target_input.clear()
        is_api = self.api_radio.isChecked()
        is_web = self.web_radio.isChecked()

        self.method_combo.setVisible(is_api)
        self.headers_label.setVisible(is_api)
        self.headers_input.setVisible(is_api)
        self.fields_label.setVisible(is_api)
        self.fields_input.setVisible(is_api)

        self.web_text_label.setVisible(is_web)
        self.web_text_input.setVisible(is_web)
        self.web_selector_label.setVisible(is_web)
        self.web_selector_input.setVisible(is_web)
        self.web_scenario_label.setVisible(is_web)
        self.web_scenario_input.setVisible(is_web)

        if is_web:
            self.target_input.setPlaceholderText("https://example.com")
        elif is_api:
            self.target_input.setPlaceholderText("https://jsonplaceholder.typicode.com/posts/1")

        self.update_body_visibility(self.method_combo.currentText())

    def update_body_visibility(self, method):
        show_body = self.api_radio.isChecked() and method in ("POST", "PUT")
        self.body_label.setVisible(show_body)
        self.body_input.setVisible(show_body)

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
                margin-bottom: 6px;
            }
            #fieldLabel {
                color: #a6adc8;
                font-size: 11px;
                margin-top: 4px;
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
            #methodCombo {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px;
                font-size: 13px;
            }
            #bodyInput {
                background-color: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 8px;
                padding: 8px;
                font-size: 12px;
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

        if not value:
            QMessageBox.warning(self, "Не заполнено поле", "Введите URL для проверки.")
            return

        if self.web_radio.isChecked():
            expected_text = self.web_text_input.text().strip()
            selector = self.web_selector_input.text().strip()
            scenario = self.web_scenario_input.toPlainText().strip()
            self.status_label.setText(f"Проверяем {value}...")
            logging.info(f"Запуск веб-теста для {value}")
            self.thread = TestRunnerThread(
                target="web", value=value,
                expected_text=expected_text, selector=selector,
                scenario=scenario
            )
        elif self.api_radio.isChecked():
            method = self.method_combo.currentText()
            body = self.body_input.toPlainText().strip()
            headers = self.headers_input.toPlainText().strip()
            required_fields = self.fields_input.text().strip()

            if method in ("POST", "PUT") and not body:
                QMessageBox.warning(self, "Не заполнено поле", f"Для метода {method} нужно указать тело запроса.")
                return

            self.status_label.setText(f"Проверяем {method} {value}...")
            logging.info(f"Запуск API-теста: {method} {value}")
            self.thread = TestRunnerThread(
                target="api", value=value, method=method,
                body=body, headers=headers, required_fields=required_fields
            )
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