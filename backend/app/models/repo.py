from pydantic import BaseModel, computed_field
from typing import Optional
from uuid import UUID


class ConnectedRepo(BaseModel):
    id: UUID
    user_id: UUID
    installation_id: int
    owner: str
    repo: str
    active: bool = True

    @computed_field
    @property
    def full_name(self) -> str:
        return f"{self.owner}/{self.repo}"
