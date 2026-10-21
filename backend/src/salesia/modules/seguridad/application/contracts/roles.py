from pydantic import BaseModel, Field


class RoleCreateModel(BaseModel):
    role_key: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    permissions: list[str]


class RoleUpdateModel(BaseModel):
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    permissions: list[str]
    affected_users: int = Field(ge=0)
    expected_role_hash: str = Field(min_length=64, max_length=64)
    reason: str = Field(min_length=5, max_length=2000)


class RoleCloneModel(BaseModel):
    role_key: str = Field(pattern=r"^[a-z][a-z0-9_]{2,63}$")
    title: str = Field(min_length=1, max_length=128)
    description: str = Field(default="", max_length=2000)
    additional_permissions: list[str] = Field(default_factory=list)
