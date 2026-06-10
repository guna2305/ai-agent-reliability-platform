"""Unit tests for RegisterUserUseCase using in-memory repos."""
import pytest

from src.application.interfaces.repositories import (
    OrganizationRepository,
    OrgMemberRepository,
    UserRepository,
)
from src.application.use_cases.auth import (
    EmailAlreadyRegisteredError,
    RegisterUserDTO,
    RegisterUserUseCase,
)
from src.domain.entities import Organization, OrgMember, User

# ── In-memory fakes ───────────────────────────────────────────────────────────

class FakeUserRepo(UserRepository):
    def __init__(self):
        self._store: dict[str, User] = {}

    async def save(self, user: User) -> User:
        self._store[user.id] = user
        return user

    async def get_by_id(self, user_id: str) -> User | None:
        return self._store.get(user_id)

    async def get_by_email(self, email: str) -> User | None:
        return next((u for u in self._store.values() if u.email == email.lower()), None)

    async def update(self, user: User) -> User:
        self._store[user.id] = user
        return user


class FakeOrgRepo(OrganizationRepository):
    def __init__(self):
        self._store: dict[str, Organization] = {}

    async def save(self, org: Organization) -> Organization:
        self._store[org.id] = org
        return org

    async def get_by_id(self, org_id: str) -> Organization | None:
        return self._store.get(org_id)

    async def get_by_slug(self, slug: str) -> Organization | None:
        return next((o for o in self._store.values() if o.slug == slug), None)

    async def list_for_user(self, user_id: str) -> list[Organization]:
        return list(self._store.values())

    async def update(self, org: Organization) -> Organization:
        self._store[org.id] = org
        return org


class FakeMemberRepo(OrgMemberRepository):
    def __init__(self):
        self._store: list[OrgMember] = []

    async def save(self, member: OrgMember) -> OrgMember:
        self._store.append(member)
        return member

    async def get(self, org_id: str, user_id: str) -> OrgMember | None:
        return next((m for m in self._store if m.org_id == org_id and m.user_id == user_id), None)

    async def list_by_org(self, org_id: str) -> list[OrgMember]:
        return [m for m in self._store if m.org_id == org_id]

    async def update_role(self, org_id: str, user_id: str, role: str) -> OrgMember | None:
        for m in self._store:
            if m.org_id == org_id and m.user_id == user_id:
                m.role = role
                return m
        return None

    async def delete(self, org_id: str, user_id: str) -> bool:
        before = len(self._store)
        self._store = [m for m in self._store if not (m.org_id == org_id and m.user_id == user_id)]
        return len(self._store) < before


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.fixture
def uc():
    return RegisterUserUseCase(
        user_repo=FakeUserRepo(),
        org_repo=FakeOrgRepo(),
        member_repo=FakeMemberRepo(),
    )


@pytest.mark.asyncio
async def test_register_user_returns_tokens(uc):
    result = await uc.execute(RegisterUserDTO(
        email="alice@example.com",
        password="securepass123",
        full_name="Alice Smith",
    ))
    assert result.email == "alice@example.com"
    assert result.access_token
    assert result.refresh_token
    assert result.token_type == "bearer"


@pytest.mark.asyncio
async def test_register_user_duplicate_raises(uc):
    dto = RegisterUserDTO(email="bob@example.com", password="pass1234!", full_name="Bob")
    await uc.execute(dto)
    with pytest.raises(EmailAlreadyRegisteredError):
        await uc.execute(dto)


@pytest.mark.asyncio
async def test_register_creates_org_with_owner_membership():
    user_repo = FakeUserRepo()
    org_repo = FakeOrgRepo()
    member_repo = FakeMemberRepo()
    uc = RegisterUserUseCase(user_repo=user_repo, org_repo=org_repo, member_repo=member_repo)

    await uc.execute(RegisterUserDTO(
        email="charlie@example.com",
        password="mypassword99",
        full_name="Charlie",
        org_name="Charlie's Company",
    ))

    user = await user_repo.get_by_email("charlie@example.com")
    assert user is not None
    orgs = list(org_repo._store.values())
    assert len(orgs) == 1
    assert orgs[0].name == "Charlie's Company"

    members = member_repo._store
    assert len(members) == 1
    assert members[0].role == "owner"
    assert members[0].user_id == user.id
