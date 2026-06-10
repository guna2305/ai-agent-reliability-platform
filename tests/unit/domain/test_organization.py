from src.domain.entities import Organization, OrgMember


def test_create_org_generates_slug():
    org = Organization.create(name="Acme Corp")
    assert org.slug == "acme-corp"
    assert org.plan == "free"
    assert org.id is not None


def test_org_slug_strips_special_chars():
    org = Organization.create(name="Hello, World! 2024")
    assert " " not in org.slug
    assert "!" not in org.slug
    assert "," not in org.slug


def test_create_org_member():
    member = OrgMember.create(org_id="org-1", user_id="user-1", role="owner")
    assert member.role == "owner"
    assert member.org_id == "org-1"


def test_upgrade_org_plan():
    org = Organization.create(name="Startup Inc")
    org.upgrade_plan("pro")
    assert org.plan == "pro"
