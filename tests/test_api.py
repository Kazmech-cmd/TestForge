import json
import os
import allure
import requests


@allure.step("Отправить {method} запрос на {url}")
def send_request(method, url, body=None, headers=None):
    try:
        kwargs = {"timeout": 5}
        if body:
            kwargs["json"] = json.loads(body)
        if headers:
            kwargs["headers"] = json.loads(headers)
        return requests.request(method, url, **kwargs)
    except requests.exceptions.RequestException as error:
        allure.attach(
            str(error),
            name="connection_error",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise AssertionError(f"Не удалось подключиться к {url}: {error}")
    except json.JSONDecodeError as error:
        raise AssertionError(f"Тело запроса или заголовки — невалидный JSON: {error}")


def get_request_params():
    url = os.environ.get("TEST_API_URL", "https://jsonplaceholder.typicode.com/posts/1")
    method = os.environ.get("TEST_API_METHOD", "GET")
    body = os.environ.get("TEST_API_BODY", "")
    headers = os.environ.get("TEST_API_HEADERS", "")
    required_fields = os.environ.get("TEST_API_REQUIRED_FIELDS", "")
    return method, url, body, headers, required_fields


@allure.title("API-эндпоинт возвращает успешный статус")
def test_api_returns_success_status():
    method, url, body, headers, _ = get_request_params()
    response = send_request(method, url, body, headers)
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
    method, url, body, headers, _ = get_request_params()
    response = send_request(method, url, body, headers)
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
    method, url, body, headers, _ = get_request_params()
    response = send_request(method, url, body, headers)
    with allure.step("Проверить время ответа"):
        assert response.elapsed.total_seconds() < 3


@allure.title("Content-Type ответа указывает на JSON")
def test_api_content_type_is_json():
    method, url, body, headers, _ = get_request_params()
    response = send_request(method, url, body, headers)
    with allure.step("Проверить заголовок Content-Type"):
        content_type = response.headers.get("Content-Type", "")
        assert "json" in content_type.lower()


@allure.title("Ответ содержит все обязательные поля")
@allure.description("Проверяем наличие полей, заданных пользователем через запятую")
def test_api_response_has_required_fields():
    method, url, body, headers, required_fields = get_request_params()
    if not required_fields:
        allure.attach(
            "Список обязательных полей не задан — проверка пропущена",
            name="skip_reason",
            attachment_type=allure.attachment_type.TEXT,
        )
        return

    response = send_request(method, url, body, headers)
    try:
        data = response.json()
        fields = [f.strip() for f in required_fields.split(",") if f.strip()]
        for field in fields:
            with allure.step(f"Проверить, что поле '{field}' присутствует в ответе"):
                assert field in data, f"Поле '{field}' отсутствует в ответе"
    except (ValueError, AssertionError):
        allure.attach(
            response.text,
            name="response_body",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise