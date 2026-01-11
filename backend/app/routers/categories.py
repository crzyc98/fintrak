from fastapi import APIRouter, HTTPException

from app.models.category import CategoryCreate, CategoryUpdate, CategoryResponse, CategoryTree
from app.services.category_service import category_service

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
async def get_categories():
    return category_service.get_all()


@router.get("/tree", response_model=list[CategoryTree])
async def get_category_tree():
    return category_service.get_tree()


@router.post("", response_model=CategoryResponse, status_code=201)
async def create_category(data: CategoryCreate):
    try:
        return category_service.create(data)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/{category_id}", response_model=CategoryResponse)
async def get_category(category_id: str):
    category = category_service.get_by_id(category_id)
    if not category:
        raise HTTPException(status_code=404, detail="Category not found")
    return category


@router.put("/{category_id}", response_model=CategoryResponse)
async def update_category(category_id: str, data: CategoryUpdate):
    try:
        category = category_service.update(category_id, data)
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
        return category
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{category_id}", status_code=204)
async def delete_category(category_id: str):
    success, error = category_service.delete(category_id)
    if not success:
        if error == "Category not found":
            raise HTTPException(status_code=404, detail=error)
        raise HTTPException(status_code=400, detail=error)
