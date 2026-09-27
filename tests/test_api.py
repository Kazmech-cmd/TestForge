import allure
import pytest
import requests


@allure.step("Отправить GET-запрос на пост {post_id}")
def get_post(post_id):
    return requests.get(f"https://jsonplaceholder.typicode.com/posts/{post_id}")


@allure.title("Пост {post_id} должен возвращать статус 200")
@pytest.mark.parametrize("post_id", [1, 2, 3])
def test_multiple_posts_return_200(post_id):
    response = get_post(post_id)
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


@allure.title("Ответ должен содержать поле title")
@allure.description("Проверяем, что структура ответа API соответствует ожидаемой схеме")
def test_post_has_title_field():
    response = get_post(1)
    try:
        with allure.step("Проверить, что в ответе есть поле title"):
            data = response.json()
            assert "title" in data
    except AssertionError:
        allure.attach(
            response.text,
            name="response_body",
            attachment_type=allure.attachment_type.TEXT,
        )
        raise