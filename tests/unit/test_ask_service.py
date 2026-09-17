import pytest

from munipal.services.ask_service import is_judgment, lexical_score, question_terms


@pytest.mark.parametrize(
    "question",
    [
        "is the bond call material",
        "should we file",
        "does this apply",
        "which clause controls",
        "are we compliant",
        "calculate the deadline",
        "when must we file",
        "are we late",
        "what date is 180 days after year end",
        "is this a reportable event",
        "recommend a course",
        "Are we in compliance?",
        "is this required",
        "does this satisfy the covenant",
        "What is our filing deadline?",
        "What is our due date?",
        "When do we file the annual report?",
        "Have we met the reporting obligation?",
        "Can we skip this notice?",
        "Is this legally sufficient?",
        "Is this legal?",
        "Has the issuer defaulted?",
        "Does my municipal advisor approve?",
        "What is our municipal adviser's opinion?",
        "Has a default occurred?",
        "Does this constitute a default?",
        "Would this cause a default?",
        "Do we comply with the covenant?",
        "Is this lawful?",
        "Does our municipal advisor support this?",
        "Has our municipal advisor signed off?",
        "Would this trigger an event of default?",
        "Would this violate the covenant?",
        "Was this approved by our municipal advisor?",
        "What does the legal opinion conclude?",
        "Are we violating the covenant?",
        "Have we complied with the covenant?",
        "Could this result in an event of default?",
        "Did counsel determine legality?",
        "Is this permissible under the covenant?",
        "Is this illegal?",
        "Is this noncompliant?",
        "Is this prohibited under the covenant?",
        "May we do this under the bond documents?",
        "Is this authorized under the indenture?",
        "What did bond counsel conclude?",
        "Did bond counsel approve this?",
        "Should bond counsel approve this?",
        "Determine whether this is allowed.",
        "Where is the default provision and are we in default?",
        "Where is the legal opinion? Is this legal?",
        "Find the municipal advisor agreement and did they approve this?",
        "Determine permissibility under the covenant.",
        "Assess municipal-advisor approval.",
        "Evaluate whether the issuer can proceed.",
        "Please confirm this course of action.",
    ],
)
def test_refuses_judgment(question):
    assert is_judgment(question)


@pytest.mark.parametrize(
    "question",
    [
        "annual report due",
        "listed events",
        "dissemination agent",
        "where is the deadline clause",
        "where is the legal opinion",
        "where is the default provision",
        "where is the municipal advisor agreement",
        "where is the annual report",
        "find the annual report",
        "show me listed events",
        "bond counsel opinion",
    ],
)
def test_accepts_record_lookup(question):
    assert not is_judgment(question)


def test_lexical_rules():
    assert question_terms("Where is the annual report?") == ["annual", "report"]
    assert lexical_score(["annual"], "Annual", "annual annual") > lexical_score(
        ["annual"], "", "annual"
    )
    assert lexical_score(["rebate"], "", "nothing relevant") == 0
