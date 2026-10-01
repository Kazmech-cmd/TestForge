import os
import time
import allure


@allure.title("Страница открывается и содержит непустой заголовок")
def test_page_loads_successfully(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    page.goto(url)
    try:
        with allure.step("Проверить, что заголовок страницы не пустой"):
            assert page.title() != ""
    except AssertionError:
        allure.attach(
            page.screenshot(),
            name="screenshot_on_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise


@allure.title("Указанный текст присутствует на странице")
def test_page_contains_text(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    expected_text = os.environ.get("TEST_EXPECTED_TEXT", "")
    scenario = os.environ.get("TEST_SCENARIO", "")
    if not expected_text or scenario:
        allure.attach(
            "Текст для поиска не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    page.goto(url)
    page.wait_for_load_state("networkidle")
    try:
        with allure.step(f"Проверить, что на странице есть текст '{expected_text}'"):
            page_text = page.locator("body").inner_text()
            assert expected_text.lower() in page_text.lower()
    except AssertionError:
        allure.attach(
            page.screenshot(),
            name="screenshot_on_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise


@allure.title("Указанный элемент виден на странице")
def test_element_is_visible(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    selector = os.environ.get("TEST_SELECTOR", "")
    if not selector:
        allure.attach(
            "Селектор не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    page.goto(url)
    try:
        with allure.step(f"Проверить, что элемент '{selector}' виден"):
            page.wait_for_selector(selector, state="visible", timeout=5000)
    except Exception:
        allure.attach(
            page.screenshot(),
            name="screenshot_on_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise AssertionError(f"Элемент '{selector}' не найден или не виден")


@allure.title("Страница загружается быстрее заданного времени")
def test_page_load_time_is_acceptable(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    max_seconds = float(os.environ.get("TEST_MAX_LOAD_TIME", "5"))

    start = time.time()
    page.goto(url)
    load_time = time.time() - start

    with allure.step(f"Проверить, что страница загрузилась быстрее {max_seconds} сек"):
        assert load_time < max_seconds, f"Страница загружалась {load_time:.2f} сек"


@allure.title("На странице нет ошибок в консоли браузера")
def test_no_console_errors(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    console_errors = []

    def handle_console(msg):
        if msg.type == "error" and "Failed to load resource" not in msg.text:
            console_errors.append(msg.text)

    page.on("console", handle_console)
    page.on("pageerror", lambda error: console_errors.append(str(error)))

    page.goto(url)
    page.wait_for_load_state("networkidle")

    if console_errors:
        allure.attach(
            "\n".join(console_errors),
            name="console_errors",
            attachment_type=allure.attachment_type.TEXT,
        )

    with allure.step("Проверить отсутствие ошибок в консоли"):
        assert not console_errors, f"Найдено ошибок в консоли: {len(console_errors)}"


@allure.title("Сценарий действий выполняется без ошибок")
@allure.description("Выполняет последовательность действий (fill/click) и проверяет, что каждое сработало")
def test_custom_scenario(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    scenario = os.environ.get("TEST_SCENARIO", "")
    if not scenario:
        allure.attach(
            "Сценарий не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    page.goto(url)

    for line_number, line in enumerate(scenario.strip().split("\n"), start=1):
        line = line.strip()
        if not line:
            continue

        try:
            if line.startswith("fill:"):
                rest = line[len("fill:"):].strip()
                selector, value = [part.strip() for part in rest.split("|", 1)]
                with allure.step(f"Шаг {line_number}: заполнить '{selector}' значением '{value}'"):
                    page.fill(selector, value)

            elif line.startswith("click:"):
                selector = line[len("click:"):].strip()
                with allure.step(f"Шаг {line_number}: кликнуть по '{selector}'"):
                    page.click(selector)

            else:
                raise AssertionError(f"Неизвестная команда в строке {line_number}: '{line}'")

        except Exception as error:
            allure.attach(
                page.screenshot(),
                name=f"screenshot_step_{line_number}",
                attachment_type=allure.attachment_type.PNG,
            )
            raise AssertionError(f"Ошибка на шаге {line_number} ('{line}'): {error}")

    expected_text = os.environ.get("TEST_EXPECTED_TEXT", "")
    if expected_text:
        try:
            with allure.step(f"Проверить, что после сценария на странице есть текст '{expected_text}'"):
                page_text = page.locator("body").inner_text()
                assert expected_text.lower() in page_text.lower()
        except AssertionError:
            allure.attach(
                page.screenshot(),
                name="screenshot_after_scenario",
                attachment_type=allure.attachment_type.PNG,
            )
            raise