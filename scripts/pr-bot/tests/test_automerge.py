from pr_bot.automerge import closes_issue_number


def test_closes_issue_number():
    body = "Implements #13: Fix README\n\nCloses #13"
    assert closes_issue_number(body) == 13


def test_closes_issue_number_missing():
    assert closes_issue_number("No link here") is None
