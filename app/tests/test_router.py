from app.agent.router import router

SHORTLIST = [{"project_name": "Azure Bay"}]


def make_state(**overrides):
    state = {
        "user_query": "",
        "shortlisted_projects": [],
        "budget": None,
    }
    state.update(overrides)
    return state


def test_greeting_routes_to_not_relevant():
    assert router(make_state(user_query="Hello there")) == "not_relevant"


def test_greeting_word_inside_other_words_is_not_a_greeting():
    # "hi" inside "this" must not be treated as a greeting
    state = make_state(user_query="book this one", shortlisted_projects=SHORTLIST)
    assert router(state) == "book_project"


def test_budget_number_routes_to_extract_budget():
    assert router(make_state(user_query="my budget is 800000")) == "extract_budget"


def test_booking_intent_with_shortlist_routes_to_booking():
    state = make_state(user_query="I want to book Azure Bay", shortlisted_projects=SHORTLIST)
    assert router(state) == "book_project"


def test_booking_intent_without_shortlist_is_refused():
    assert router(make_state(user_query="I want to book a visit")) == "not_relevant"


def test_qa_intent_with_shortlist_routes_to_project_qa():
    state = make_state(user_query="what amenities does it have", shortlisted_projects=SHORTLIST)
    assert router(state) == "project_qa"


def test_no_budget_routes_to_ask_budget():
    assert router(make_state(user_query="show me flats in dubai")) == "ask_budget"


def test_existing_budget_routes_to_sql_search():
    state = make_state(user_query="show me flats in dubai", budget=800000)
    assert router(state) == "sql_search"


def test_awaiting_email_routes_back_to_booking():
    state = make_state(user_query="mehul@example.com", awaiting_email=True)
    assert router(state) == "book_project"


def test_awaiting_project_choice_routes_back_to_booking():
    state = make_state(user_query="Azure Bay", awaiting_project_choice=True,
                       shortlisted_projects=SHORTLIST, budget=800000)
    assert router(state) == "book_project"
