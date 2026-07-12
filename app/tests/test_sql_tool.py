from app.tools.sql_tool import SQLSearchTool


async def run_search(session_factory, query: str, budget):
    state = {"user_query": query, "budget": budget}
    async with session_factory() as session:
        return await SQLSearchTool(session).run(state)


async def test_no_budget_returns_empty(test_db):
    state = await run_search(test_db, "3 bhk in Dubai", None)
    assert state["projects"] == []


async def test_budget_filter_allows_30_percent_slack(test_db):
    state = await run_search(test_db, "apartments anywhere", 500000)
    prices = [p["price_usd"] for p in state["projects"]]
    assert prices, "expected some projects"
    assert all(p <= 500000 * 1.3 for p in prices)


async def test_city_match_is_case_insensitive_and_scalar(test_db):
    state = await run_search(test_db, "I want a 3 bhk in Dubai under budget", 800000)
    assert state["city"] == "Dubai"  # scalar, not a list
    assert all(p["city"] == "Dubai" for p in state["projects"])


async def test_bhk_exact_match(test_db):
    state = await run_search(test_db, "2 bhk in phuket", 500000)
    assert state["bhk"] == 2
    assert all(p["bedrooms"] == 2 for p in state["projects"])


async def test_bhk_fallback_to_lower_available(test_db):
    # Dubai has no 5 BHK under this budget — falls back to the best lower option (4)
    state = await run_search(test_db, "5 bhk in dubai", 800000)
    assert state["bhk"] == 4
    assert state["projects"]
    assert all(p["bedrooms"] == 4 for p in state["projects"])


async def test_feature_filter(test_db):
    state = await run_search(test_db, "3 bhk with pool in dubai", 800000)
    assert state["projects"]
    for p in state["projects"]:
        blob = " ".join(filter(None, [p["features"], p["facilities"], p["description"]])).lower()
        assert "pool" in blob
