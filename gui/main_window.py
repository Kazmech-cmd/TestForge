import subprocess
import sys
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("TestForge")
        self.setGeometry(100, 100, 400, 300)

        run_button = QPushButton("Запустить тесты", self)
        run_button.setGeometry(125, 100, 150, 40)
        run_button.clicked.connect(self.run_tests)

        report_button = QPushButton("Открыть отчёт", self)
        report_button.setGeometry(125, 160, 150, 40)
        report_button.clicked.connect(self.open_report)

    def run_tests(self):
        subprocess.run(
            ["python", "-m", "pytest", "tests/", "-v", "--headed",
             "--alluredir=allure-results", "--clean-alluredir"]
        )

    def open_report(self):
        subprocess.Popen(["allure", "serve", "allure-results"], shell=True)


app = QApplication(sys.argv)
window = MainWindow()
window.show()
app.exec()