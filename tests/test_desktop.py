import os
import time
import allure
from pywinauto.application import Application


def launch_app():
    app_path = os.environ.get("TEST_APP_PATH", "mspaint.exe")

    try:
        app = Application(backend="win32").start(app_path)
    except Exception as error:
        raise AssertionError(f"Не удалось запустить '{app_path}': {error}")

    time.sleep(1)
    window = app.top_window()
    window.wait("visible", timeout=10)
    return app, window


def collect_all_text(window):
    texts = [window.window_text()]
    try:
        for ctrl in window.descendants():
            try:
                text = ctrl.window_text()
                if text:
                    texts.append(text)
            except Exception:
                pass
    except Exception:
        pass
    return " ".join(texts)


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


@allure.title("Приложение запускается быстрее заданного времени")
def test_app_launch_time_is_acceptable():
    max_seconds = float(os.environ.get("TEST_MAX_LAUNCH_TIME", "10"))
    app = None
    try:
        start = time.time()
        with allure.step("Запустить приложение и замерить время"):
            app, window = launch_app()
        launch_time = time.time() - start
        with allure.step(f"Проверить, что запуск занял меньше {max_seconds} сек"):
            assert launch_time < max_seconds, f"Запуск занял {launch_time:.2f} сек"
    finally:
        if app:
            try:
                app.kill()
            except Exception:
                pass


@allure.title("Указанный текст присутствует в окне приложения")
def test_window_contains_text():
    expected_text = os.environ.get("TEST_DESKTOP_TEXT", "")
    if not expected_text:
        allure.attach(
            "Текст для поиска не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    app = None
    try:
        with allure.step("Запустить приложение"):
            app, window = launch_app()
        with allure.step(f"Проверить, что в окне есть текст '{expected_text}'"):
            all_text = collect_all_text(window)
            assert expected_text.lower() in all_text.lower(), f"Текст не найден. Найдено: {all_text[:300]}"
    finally:
        if app:
            try:
                app.kill()
            except Exception:
                pass


@allure.title("Указанный элемент присутствует в окне")
def test_element_exists():
    element_name = os.environ.get("TEST_DESKTOP_ELEMENT", "")
    if not element_name:
        allure.attach(
            "Имя элемента не задано — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    app = None
    try:
        with allure.step("Запустить приложение"):
            app, window = launch_app()
        with allure.step(f"Проверить, что элемент '{element_name}' существует"):
            try:
                control = window[element_name]
                assert control.exists(), f"Элемент '{element_name}' не найден"
            except Exception as error:
                raise AssertionError(f"Элемент '{element_name}' не найден: {error}")
    finally:
        if app:
            try:
                app.kill()
            except Exception:
                pass


@allure.title("Сценарий действий выполняется без ошибок")
@allure.description("Выполняет последовательность действий (click/type) по именам элементов")
def test_custom_scenario():
    scenario = os.environ.get("TEST_DESKTOP_SCENARIO", "")
    if not scenario:
        allure.attach(
            "Сценарий не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    app = None
    try:
        with allure.step("Запустить приложение"):
            app, window = launch_app()

        for line_number, line in enumerate(scenario.strip().split("\n"), start=1):
            line = line.strip()
            if not line:
                continue

            try:
                if line.startswith("click:"):
                    target = line[len("click:"):].strip()
                    with allure.step(f"Шаг {line_number}: кликнуть по '{target}'"):
                        window[target].click()

                elif line.startswith("type:"):
                    rest = line[len("type:"):].strip()
                    target, value = [part.strip() for part in rest.split("|", 1)]
                    with allure.step(f"Шаг {line_number}: ввести в '{target}' текст '{value}'"):
                        window[target].type_keys(value, with_spaces=True)

                else:
                    raise AssertionError(f"Неизвестная команда в строке {line_number}: '{line}'")

            except Exception as error:
                raise AssertionError(f"Ошибка на шаге {line_number} ('{line}'): {error}")
    finally:
        if app:
            try:
                app.kill()
            except Exception:
                pass