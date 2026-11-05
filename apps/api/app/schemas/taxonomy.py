"""SCENTIQ Taxonomy Schemas: Notes, Accords, and Fragrance Associations.
"""
import uuid
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, Field
from app.models.enums import PyramidPosition


class NoteBase(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=150)
    aliases: List[str] = Field(default_factory=list)
    note_family: Optional[str] = None
    description: Optional[str] = None


class NoteCreate(NoteBase):
    slug: Optional[str] = None


class NoteResponse(NoteBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str


class AccordBase(BaseModel):
    canonical_name: str = Field(..., min_length=1, max_length=150)
    family: Optional[str] = None
    description: Optional[str] = None


class AccordCreate(AccordBase):
    slug: Optional[str] = None


class AccordResponse(AccordBase):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str


class FragranceNoteCreate(BaseModel):
    note_id: uuid.UUID
    pyramid_position: PyramidPosition = PyramidPosition.UNSPECIFIED
    source_id: Optional[uuid.UUID] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class FragranceNoteResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    note_id: uuid.UUID
    note_name: Optional[str] = None
    pyramid_position: PyramidPosition
    confidence: float


class FragranceAccordCreate(BaseModel):
    accord_id: uuid.UUID
    intensity_rank: int = Field(1, ge=1, le=10)
    source_id: Optional[uuid.UUID] = None
    confidence: float = Field(1.0, ge=0.0, le=1.0)


class FragranceAccordResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    accord_id: uuid.UUID
    accord_name: Optional[str] = None
    intensity_rank: int
    confidence: float

