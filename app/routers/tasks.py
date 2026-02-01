from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app import models, schemas, auth
from app.database import get_db

router = APIRouter(
    prefix="/tasks",
    tags=["Tasks"]
)

# ========== CREATE TASK ==========

@router.post("/", response_model=schemas.TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(
    task: schemas.TaskCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Create new task for current user"""
    
    new_task = models.Task(
        title=task.title,
        description=task.description,
        status=task.status,
        user_id=current_user.id  # ← Automatic user_id!
    )
    
    db.add(new_task)
    db.commit()
    db.refresh(new_task)
    
    return new_task

# ========== GET ALL TASKS (with filters) ==========

@router.get("/", response_model=List[schemas.TaskResponse])
def get_tasks(
    status: Optional[models.TaskStatus] = None,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get all tasks for current user (with optional status filter)"""
    
    query = db.query(models.Task).filter(models.Task.user_id == current_user.id)
    
    # Filter by status if provided
    if status:
        query = query.filter(models.Task.status == status)
    
    tasks = query.offset(skip).limit(limit).all()
    return tasks

# ========== GET SINGLE TASK ==========

@router.get("/{task_id}", response_model=schemas.TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Get single task by ID"""
    
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id  # ← Security: faqat o'z taski
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    return task

# ========== UPDATE TASK ==========

@router.put("/{task_id}", response_model=schemas.TaskResponse)
def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Update task (title, description, status)"""
    
    # Find task
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id  # ← Security
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    # Update only provided fields
    update_data = task_update.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(task, key, value)
    
    db.commit()
    db.refresh(task)
    
    return task

# ========== DELETE TASK ==========

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(auth.get_current_user)
):
    """Delete task"""
    
    task = db.query(models.Task).filter(
        models.Task.id == task_id,
        models.Task.user_id == current_user.id  # ← Security
    ).first()
    
    if not task:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Task not found"
        )
    
    db.delete(task)
    db.commit()
    
    return None  # 204 No Content