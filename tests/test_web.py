import os
import allure


@allure.title("Страница открывается и содержит непустой заголовок")
def test_url_opens_successfully(page):
    url = os.environ.get("TEST_URL", "https://example.com")
    page.goto(url)
    try:
        assert page.title() != ""
    except AssertionError:
        allure.attach(
            page.screenshot(),
            name="screenshot_on_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise