import os
import allure
import requests


@allure.step("Отправить GET-запрос на {url}")
def get_response(url):
    return requests.get(url)


@allure.title("API-эндпоинт возвращает успешный статус")
def test_api_returns_success_status():
    url = os.environ.get("TEST_API_URL", "https://jsonplaceholder.typicode.com/posts/1")
    response = get_response(url)
    try:
        with allure.step("Проверить, что статус ответа — 200"):
            assert response.status_code == 200
    except AssertionError:
        allure.attach(
            response.text,
            name="response_body",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise


@allure.title("Ответ API является корректным JSON")
@allure.description("Проверяем, что тело ответа парсится как JSON и не пустое")
def test_api_response_is_valid_json():
    url = os.environ.get("TEST_API_URL", "https://jsonplaceholder.typicode.com/posts/1")
    response = get_response(url)
    try:
        with allure.step("Проверить, что ответ парсится как JSON"):
            data = response.json()
        with allure.step("Проверить, что ответ не пустой"):
            assert data
    except (ValueError, AssertionError):
        allure.attach(
            response.text,
            name="response_body",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise


@allure.title("Время ответа API не превышает 3 секунды")
def test_api_response_time_is_acceptable():
    url = os.environ.get("TEST_API_URL", "https://jsonplaceholder.typicode.com/posts/1")
    response = get_response(url)
    with allure.step("Проверить время ответа"):
        assert response.elapsed.total_seconds() < 3