from src import report, mark
from src.coingeckp_api import get_current_price
from src.epics import SuperEpic

pytestmark = [SuperEpic.story.EpicStory]


@mark.link("test")
def test_get_current_price_with_one_currency():
    """Получение курса для одной валюты

    Шаги:
    ________
    Получаем курс Bitcoin на доллары USD
    Проверяем, что курс имеется
    """
    with report.step("Получаем курс Bitcoin на доллары USD"):
        currencies = get_current_price("bitcoin", "usd").get("bitcoin", {})
    with report.step("Проверяем, что курс имеется"):
        assert currencies.get("usd") is not None
        assert len(currencies.keys()) == 1


def test_get_current_price_with_two_currency():
    """Получение курса для двух валют

    Шаги:
    ________
    Получаем курс Bitcoin на доллары USD и EUR
    Проверяем, что курс имеется
    """
    with report.step("Получаем курс Bitcoin на доллары USD и EUR"):
        currencies = get_current_price("bitcoin", "usd,eur").get("bitcoin", {})
    with report.step("Проверяем, что курс имеется"):
        assert currencies.get("usd") is not None
        assert currencies.get("eur") is not None
        assert len(currencies.keys()) == 2


def test_get_current_price_with_two_currency_failed():
    """Поломанный тест

    Шаги:
    ________
    Получаем курс Bitcoin на доллары USD и EUR
    Проверяем, что курс имеется (и падаем =))
    """
    with report.step("Получаем курс Bitcoin на доллары USD и EUR"):
        currencies = get_current_price("bitcoin", "usd,eur").get("bitcoin", {})
    with report.step("Проверяем, что курс имеется", duty="qa_duty_2"):
        assert currencies.get("usd") is not None
        assert currencies.get("eur") is not None
        assert len(currencies.keys()) == 1
