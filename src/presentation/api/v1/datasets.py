"""Dataset management routes."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from fastapi import APIRouter, HTTPException, Query, status
from pydantic import BaseModel, Field

from src.application.use_cases.evaluations import (
    AddDatasetItemsUseCase,
    CreateDatasetDTO,
    CreateDatasetUseCase,
    DatasetItemInput,
    DatasetNotFoundError,
    DeleteDatasetUseCase,
    GetDatasetUseCase,
    ListDatasetItemsUseCase,
    ListDatasetsUseCase,
)
from src.infrastructure.database.repositories import (
    PostgresDatasetItemRepository,
    PostgresDatasetRepository,
    PostgresOrganizationRepository,
)
from src.presentation.api.auth_dependencies import (
    CurrentUser, OrgAdminDep, OrgMemberDep, SessionDep,
)

router = APIRouter(prefix="/organizations/{org_slug}/datasets", tags=["datasets"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class CreateDatasetRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    dataset_type: str = Field(default="golden", pattern="^(golden|benchmark|regression)$")


class DatasetResponse(BaseModel):
    id: str
    org_id: str
    name: str
    description: str | None
    dataset_type: str
    created_by: str
    created_at: datetime
    updated_at: datetime


class DatasetListResponse(BaseModel):
    items: list[DatasetResponse]
    total: int
    limit: int
    offset: int


class DatasetItemRequest(BaseModel):
    input: dict[str, Any]
    expected_output: dict[str, Any] | None = None
    context: list[str] = Field(default_factory=list)
    metadata: dict[str, Any] = Field(default_factory=dict)


class AddItemsRequest(BaseModel):
    items: list[DatasetItemRequest] = Field(..., min_length=1)


class DatasetItemResponse(BaseModel):
    id: str
    dataset_id: str
    input: dict[str, Any]
    expected_output: dict[str, Any] | None
    context: list[str]
    created_at: datetime


class DatasetItemListResponse(BaseModel):
    items: list[DatasetItemResponse]
    total: int
    limit: int
    offset: int


# ── Helper ────────────────────────────────────────────────────────────────────

async def _org_id(org_slug: str, session) -> str:
    org = await PostgresOrganizationRepository(session).get_by_slug(org_slug)
    if not org:
        raise HTTPException(status_code=404, detail=f"Organization '{org_slug}' not found")
    return org.id


def _ds_response(d) -> DatasetResponse:
    return DatasetResponse(
        id=d.id, org_id=d.org_id, name=d.name, description=d.description,
        dataset_type=d.dataset_type, created_by=d.created_by,
        created_at=d.created_at, updated_at=d.updated_at,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.post("", response_model=DatasetResponse, status_code=status.HTTP_201_CREATED)
async def create_dataset(
    org_slug: str,
    body: CreateDatasetRequest,
    current_user: CurrentUser,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> DatasetResponse:
    org_id = await _org_id(org_slug, session)
    uc = CreateDatasetUseCase(PostgresDatasetRepository(session))
    dataset = await uc.execute(CreateDatasetDTO(
        org_id=org_id, name=body.name, created_by=current_user.id,
        dataset_type=body.dataset_type, description=body.description,
    ))
    return _ds_response(dataset)


@router.get("", response_model=DatasetListResponse)
async def list_datasets(
    org_slug: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
) -> DatasetListResponse:
    org_id = await _org_id(org_slug, session)
    uc = ListDatasetsUseCase(PostgresDatasetRepository(session))
    datasets, total = await uc.execute(org_id, limit, offset)
    return DatasetListResponse(
        items=[_ds_response(d) for d in datasets], total=total, limit=limit, offset=offset,
    )


@router.get("/{dataset_id}", response_model=DatasetResponse)
async def get_dataset(
    org_slug: str,
    dataset_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> DatasetResponse:
    org_id = await _org_id(org_slug, session)
    uc = GetDatasetUseCase(PostgresDatasetRepository(session))
    try:
        dataset = await uc.execute(dataset_id, org_id)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return _ds_response(dataset)


@router.delete("/{dataset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_dataset(
    org_slug: str,
    dataset_id: str,
    org_admin: OrgAdminDep,
    session: SessionDep,
) -> None:
    org_id = await _org_id(org_slug, session)
    uc = DeleteDatasetUseCase(PostgresDatasetRepository(session))
    try:
        await uc.execute(dataset_id, org_id)
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)


@router.post("/{dataset_id}/items", response_model=list[DatasetItemResponse], status_code=status.HTTP_201_CREATED)
async def add_items(
    org_slug: str,
    dataset_id: str,
    body: AddItemsRequest,
    org_member: OrgMemberDep,
    session: SessionDep,
) -> list[DatasetItemResponse]:
    org_id = await _org_id(org_slug, session)
    uc = AddDatasetItemsUseCase(
        PostgresDatasetRepository(session),
        PostgresDatasetItemRepository(session),
    )
    try:
        items = await uc.execute(
            dataset_id, org_id,
            [DatasetItemInput(
                input=i.input, expected_output=i.expected_output,
                context=i.context, metadata=i.metadata,
            ) for i in body.items],
        )
    except DatasetNotFoundError as e:
        raise HTTPException(status_code=404, detail=e.message)
    return [
        DatasetItemResponse(
            id=i.id, dataset_id=i.dataset_id, input=i.input,
            expected_output=i.expected_output, context=i.context, created_at=i.created_at,
        )
        for i in items
    ]


@router.get("/{dataset_id}/items", response_model=DatasetItemListResponse)
async def list_items(
    org_slug: str,
    dataset_id: str,
    org_member: OrgMemberDep,
    session: SessionDep,
    limit: int = Query(default=100, ge=1, le=500),
    offset: int = Query(default=0, ge=0),
) -> DatasetItemListResponse:
    uc = ListDatasetItemsUseCase(PostgresDatasetItemRepository(session))
    items, total = await uc.execute(dataset_id, limit, offset)
    return DatasetItemListResponse(
        items=[
            DatasetItemResponse(
                id=i.id, dataset_id=i.dataset_id, input=i.input,
                expected_output=i.expected_output, context=i.context, created_at=i.created_at,
            )
            for i in items
        ],
        total=total, limit=limit, offset=offset,
    )
