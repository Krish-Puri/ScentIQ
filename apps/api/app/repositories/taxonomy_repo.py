"""SCENTIQ Taxonomy Repository (Notes and Accords).
"""
import uuid
from typing import List, Optional
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.models.taxonomy import Note, Accord, FragranceNote, FragranceAccord


class TaxonomyRepository:
    def __init__(self, db: Session):
        self.db = db

    # Notes
    def get_note_by_id(self, note_id: uuid.UUID) -> Optional[Note]:
        return self.db.execute(select(Note).where(Note.id == note_id)).scalar_one_or_none()

    def get_note_by_slug(self, slug: str) -> Optional[Note]:
        return self.db.execute(select(Note).where(Note.slug == slug.lower())).scalar_one_or_none()

    def get_note_by_name(self, name: str) -> Optional[Note]:
        return self.db.execute(select(Note).where(Note.canonical_name.ilike(name))).scalar_one_or_none()

    def list_notes(self, limit: int = 100, offset: int = 0) -> List[Note]:
        return list(self.db.execute(select(Note).order_by(Note.canonical_name).limit(limit).offset(offset)).scalars().all())

    def create_note(self, note: Note) -> Note:
        self.db.add(note)
        self.db.commit()
        self.db.refresh(note)
        return note

    # Accords
    def get_accord_by_id(self, accord_id: uuid.UUID) -> Optional[Accord]:
        return self.db.execute(select(Accord).where(Accord.id == accord_id)).scalar_one_or_none()

    def get_accord_by_slug(self, slug: str) -> Optional[Accord]:
        return self.db.execute(select(Accord).where(Accord.slug == slug.lower())).scalar_one_or_none()

    def get_accord_by_name(self, name: str) -> Optional[Accord]:
        return self.db.execute(select(Accord).where(Accord.canonical_name.ilike(name))).scalar_one_or_none()

    def list_accords(self, limit: int = 100, offset: int = 0) -> List[Accord]:
        return list(self.db.execute(select(Accord).order_by(Accord.canonical_name).limit(limit).offset(offset)).scalars().all())

    def create_accord(self, accord: Accord) -> Accord:
        self.db.add(accord)
        self.db.commit()
        self.db.refresh(accord)
        return accord

    # Junctions
    def add_fragrance_note(self, fn: FragranceNote) -> FragranceNote:
        self.db.add(fn)
        self.db.commit()
        self.db.refresh(fn)
        return fn

    def add_fragrance_accord(self, fa: FragranceAccord) -> FragranceAccord:
        self.db.add(fa)
        self.db.commit()
        self.db.refresh(fa)
        return fa
