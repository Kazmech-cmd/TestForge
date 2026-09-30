import json
import os
import allure
import requests


@allure.step("Отправить {method} запрос на {url}")
def send_request(method, url, body=None):
    try:
        kwargs = {"timeout": 5}
        if body:
            kwargs["json"] = json.loads(body)
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as error:
        allure.attach(
            str(error),
            name="connection_error",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise AssertionError(f"Не удалось подключиться к {url}: {error}")
    except json.JSONDecodeError as error:
        raise AssertionError(f"Тело запроса — невалидный JSON: {error}")


def get_request_params():
    url = os.environ.get("TEST_API_URL", "https://jsonplaceholder.typicode.com/posts/1")
    method = os.environ.get("TEST_API_METHOD", "GET")
    body = os.environ.get("TEST_API_BODY", "")
    return method, url, body


@allure.title("API-эндпоинт возвращает успешный статус")
def test_api_returns_success_status():
    method, url, body = get_request_params()
    response = send_request(method, url, body)
    try:
        with allure.step("Проверить, что статус ответа в диапазоне 200-299"):
            assert 200 <= response.status_code < 300
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
    method, url, body = get_request_params()
    response = send_request(method, url, body)
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
    method, url, body = get_request_params()
    response = send_request(method, url, body)
    with allure.step("Проверить время ответа"):
        assert response.elapsed.total_seconds() < 3