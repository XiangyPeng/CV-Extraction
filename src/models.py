import re
from typing import List, Optional
from pydantic import BaseModel, EmailStr, Field, field_validator

PHONE_CLEAN = re.compile(r"[^\d+]+")


class Resume(BaseModel):
    name: str
    email: EmailStr
    phone: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    education: List[str] = Field(default_factory=list)
    experience: List[str] = Field(default_factory=list)
    raw_text: Optional[str] = None
    confidence: float = 0.0

    model_config = {"extra": "forbid"}

    @field_validator("name")
    def validate_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("Name must not be empty")
        return value

    @field_validator("phone")
    def normalize_phone(cls, value: Optional[str]) -> Optional[str]:
        if value is None or not str(value).strip():
            return None
        cleaned = PHONE_CLEAN.sub("", str(value))
        if len(cleaned) < 7:
            raise ValueError("Phone number is too short or may be invalid")
        return cleaned

    @field_validator("skills", "education", "experience", mode="before")
    def normalize_list_fields(cls, value):
        if value is None:
            return []
        if isinstance(value, str):
            parts = re.split(r"[\n,;•●*]+", value)
            return [item.strip() for item in parts if item.strip()]
        if isinstance(value, list):
            return [str(item).strip() for item in value if str(item).strip()]
        raise ValueError("Field must be a string or a list of strings")


class ExtractionResult(BaseModel):
    source_file: str
    resume: Optional[Resume] = None
    confidence: float = 0.0
    warnings: List[str] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)

    model_config = {"extra": "forbid"}
