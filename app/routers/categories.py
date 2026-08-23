from typing import List
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.database import get_db
from app.models.content import Category, Series, series_categories
from app.schemas.series import CategoryOut

router = APIRouter(prefix="/api/categories", tags=["Kategoriler"])

@router.get("", response_model=List[CategoryOut])
def get_categories(db: Session = Depends(get_db)):
    return db.query(Category).filter(Category.is_active == True).order_by(Category.name).all()

@router.get("/with-counts")
def get_categories_with_counts(db: Session = Depends(get_db)):
    cats = db.query(
        Category.id,
        Category.name,
        Category.slug,
        Category.description,
        Category.icon,
        func.count(series_categories.c.series_id).label("series_count")
    ).outerjoin(series_categories, Category.id == series_categories.c.category_id)     .group_by(Category.id)     .filter(Category.is_active == True)     .all()

    return [
        {
            "id": c.id,
            "name": c.name,
            "slug": c.slug,
            "description": c.description,
            "icon": c.icon,
            "series_count": c.series_count
        }
        for c in cats
    ]
