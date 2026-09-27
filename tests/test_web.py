import allure


@allure.title("Заголовок страницы example.com соответствует ожидаемому")
def test_example_page_title(page):
    page.goto("https://example.com")
    try:
        assert page.title() == "Example Domain"
    except AssertionError:
        allure.attach(
            page.screenshot(),
            name="screenshot_on_failure",
            attachment_type=allure.attachment_type.PNG,
        )
        raise