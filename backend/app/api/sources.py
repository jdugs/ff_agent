from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from app.database import get_db
from app.models.sources import Source
from pydantic import BaseModel

router = APIRouter()

class SourceResponse(BaseModel):
    source_id: int
    name: str
    source_type: str
    data_method: str
    specialty: Optional[str] = None
    is_active: bool
    current_reliability_score: Optional[float] = None
    
    class Config:
        from_attributes = True

@router.get("/", response_model=List[SourceResponse])
async def get_sources(
    source_type: Optional[str] = None,
    active_only: bool = True,
    db: Session = Depends(get_db)
):
    """Get all data sources"""
    query = db.query(Source)
    
    if active_only:
        query = query.filter(Source.is_active == True)
    if source_type:
        query = query.filter(Source.source_type == source_type)
    
    sources = query.all()
    return sources

@router.get("/{source_id}", response_model=SourceResponse)
async def get_source(source_id: int, db: Session = Depends(get_db)):
    """Get a specific source by ID"""
    source = db.query(Source).filter(Source.source_id == source_id).first()
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    return source