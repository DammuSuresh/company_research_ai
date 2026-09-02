from app.validators import is_researchable_company_name


def test_accepts_normal_company_names():
    assert is_researchable_company_name("Acme Corp")
    assert is_researchable_company_name("Salesforce")
    assert is_researchable_company_name("3M")
    assert is_researchable_company_name("AT&T")


def test_rejects_blank_or_too_short():
    assert not is_researchable_company_name("")
    assert not is_researchable_company_name("   ")
    assert not is_researchable_company_name("a")


def test_rejects_no_letters():
    assert not is_researchable_company_name("12345")
    assert not is_researchable_company_name("!!!???")
    assert not is_researchable_company_name("----")


def test_rejects_mostly_punctuation_noise():
    assert not is_researchable_company_name("###$$%^&*()")
