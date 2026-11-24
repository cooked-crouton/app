from pathlib import Path

from streamlit.testing.v1 import AppTest

from contracts import Macros
from services.mocks import MockVisionService

APP = str(Path(__file__).resolve().parent.parent / "app.py")


def _dashboard(analysis=None, portions=None) -> AppTest:
    at = AppTest.from_file(APP, default_timeout=30)
    if analysis is not None:
        at.session_state["analysis"] = analysis
    if portions is not None:
        at.session_state["portions"] = portions
    return at.run()


def _metrics(at: AppTest) -> dict[str, str]:
    return {m.label: m.value for m in at.tabs[1].metric}


def test_without_analysis_the_dashboard_explains_what_to_do():
    at = _dashboard()
    assert not at.exception
    assert any("Analyze a photo" in i.value for i in at.tabs[1].info)
    assert not at.tabs[1].metric


def test_dashboard_shows_per_portion_macros_by_default():
    analysis = MockVisionService().analyze_image(b"x")
    at = _dashboard(analysis, portions=2)
    assert not at.exception
    total = analysis.total_macros
    assert _metrics(at)["Proteins"] == f"{total.protein_g / 2:.1f} g"
    assert any("2 portions" in c.value for c in at.tabs[1].caption)


def test_whole_dish_scope_shows_the_totals():
    analysis = MockVisionService().analyze_image(b"x")
    at = _dashboard(analysis, portions=2)
    at.radio(key="dashboard_scope").set_value("Whole dish").run()
    assert not at.exception
    assert _metrics(at)["Fats"] == f"{analysis.total_macros.fat_g:.1f} g"


def test_all_zero_macros_do_not_crash():
    analysis = MockVisionService().analyze_image(b"x")
    zero = Macros(protein_g=0, carbs_g=0, fat_g=0, calories_kcal=0)
    analysis = analysis.model_copy(update={"total_macros": zero, "macros_per_portion": zero})
    at = _dashboard(analysis)
    assert not at.exception
    assert any("all values are 0" in i.value for i in at.tabs[1].info)


def _generate(at: AppTest) -> AppTest:
    return next(b for b in at.tabs[1].button if b.label == "Generate recipe").click().run()


def test_generate_shows_title_ingredients_and_numbered_steps():
    analysis = MockVisionService().analyze_image(b"x")
    at = _generate(_dashboard(analysis))
    assert not at.exception
    recipe = at.session_state["recipe"]
    assert recipe.title.startswith("Stir-fry of chicken")
    texts = [m.value for m in at.tabs[1].markdown]
    assert "- Chicken : 150 g\n- Rice : 180 g\n- Broccoli : 100 g" in texts
    assert [f"{n}. {s}" for n, s in enumerate(recipe.steps, start=1)] == [
        t for t in texts if t[:2] in {f"{n}." for n in range(1, 10)}
    ]
    assert any(b.label == "Regenerate recipe" for b in at.tabs[1].button)


def test_recipe_survives_a_rerun():
    analysis = MockVisionService().analyze_image(b"x")
    at = _generate(_dashboard(analysis)).run()
    assert not at.exception
    assert any(s.value.startswith("Stir-fry") for s in at.tabs[1].subheader)


def test_generation_failure_shows_a_message_not_a_traceback(monkeypatch):
    import ui.recipe_dashboard as panel
    from services.factory import Services
    from services.mocks import MockChatService, MockRecipeService

    class Broken(MockRecipeService):
        def generate(self, request):
            raise ConnectionError("refused")

    services = Services(vision=MockVisionService(), recipe=Broken(), chat=MockChatService())
    monkeypatch.setattr(panel, "get_services", lambda _settings: services)
    at = _generate(_dashboard(MockVisionService().analyze_image(b"x")))
    assert not at.exception
    assert any("could not be generated" in e.value for e in at.error)
    assert "recipe" not in at.session_state
