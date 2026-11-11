import math

from contracts import CookingState
from services.mocks import MockVisionService
from utils.ingredients import GRAMS, NAME, STATE, to_request, to_rows


def test_to_rows_lists_every_ingredient():
    rows = to_rows(MockVisionService().analyze_image(b"x"))
    assert rows[0] == {NAME: "poulet", STATE: "grilled", GRAMS: 150.0}
    assert len(rows) == 3


def test_to_request_cleans_the_rows():
    rows = [
        {NAME: "  Poulet ", STATE: "grilled", GRAMS: 200},
        {NAME: "riz", STATE: None, GRAMS: math.nan},  # new row: no state, no weight
        {NAME: "", STATE: "raw", GRAMS: 50},  # blank name is skipped
        {NAME: None, STATE: None, GRAMS: None},
    ]
    request = to_request(rows, portions=2)
    assert [i.name for i in request.ingredients] == ["poulet", "riz"]
    assert request.ingredients[0].grams == 200
    assert request.ingredients[1].grams is None
    assert request.ingredients[1].cooking_state is CookingState.UNKNOWN
    assert request.portions == 2


def test_to_request_returns_none_without_ingredient():
    assert to_request([{NAME: "", STATE: None, GRAMS: None}], portions=1) is None
