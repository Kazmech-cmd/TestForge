import re
import subprocess
import sys
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLabel


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
        self.setGeometry(100, 100, 400, 300)

        run_button = QPushButton("Запустить тесты", self)
        run_button.setGeometry(125, 80, 150, 40)
        run_button.clicked.connect(self.run_tests)

        report_button = QPushButton("Открыть отчёт", self)
        report_button.setGeometry(125, 140, 150, 40)
        report_button.clicked.connect(self.open_report)

        self.status_label = QLabel("Готов к запуску", self)
        self.status_label.setGeometry(50, 200, 300, 30)

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