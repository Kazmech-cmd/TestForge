import os
import time
import allure
from pywinauto.application import Application


def launch_app():
    app_path = os.environ.get("TEST_APP_PATH", "notepad.exe")

    try:
        app = Application(backend="win32").start(app_path)
    except Exception as error:
        raise AssertionError(f"Не удалось запустить '{app_path}': {error}")

    time.sleep(1)
    window = app.top_window()
    window.wait("visible", timeout=10)
    return app, window


@allure.title("Приложение запускается и открывает окно")
def test_app_launches_successfully():
    app = None
    try:
        with allure.step("Запустить приложение"):
            app, window = launch_app()
        with allure.step("Проверить, что заголовок окна не пустой"):
            title = window.window_text()
            assert title != "", "У окна пустой заголовок"
    finally:
        if app:
            try:
                app.kill()
            except Exception:
                pass