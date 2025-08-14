from scanner import match_rules


def test_term_rule_matches():
    s = "This document is confidential and must not be shared."
    ms = match_rules(s)
    assert any(m["rule_id"] == "R1" for m in ms)


def test_regex_rule_matches():
    s = "Please share credentials after the call."
    ms = match_rules(s)
    assert any(m["rule_id"] == "R2" for m in ms)
