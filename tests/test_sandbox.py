import allure


def safe_add(a, b):
    try:
        return a + b
    except TypeError:
        return None


@allure.title("Сложение двух чисел работает корректно")
def test_safe_add_numbers():
    assert safe_add(2, 3) == 5


@allure.title("Сложение числа со строкой не вызывает падение, а возвращает None")
def test_safe_add_with_string():
    assert safe_add(2, "три") is None