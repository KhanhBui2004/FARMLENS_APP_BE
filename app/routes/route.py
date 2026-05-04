from http.client import HTTPException

from fastapi import APIRouter
from app.models.todos import Todo
from app.config.database import collection_name
from app.schema.schemas import list_serial
from bson import ObjectId

router = APIRouter()

#GET Request Method
@router.get("/")
async def get_todos():
    todos = list_serial(collection_name.find())
    return todos

#POST Request Method
@router.post("/")
async def post_todo(todo: Todo):
    todo_dict = todo.dict()
    result = collection_name.insert_one(todo_dict)
    return {"id": str(result.inserted_id)} 

#PUT Request Method
@router.put("/{id}")
async def update_todo(id: str, todo: Todo):
    todo_dict = todo.dict()
    result = collection_name.update_one({"_id": ObjectId(id)}, {"$set": todo_dict})
    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="Todo not found")
    return {"id": id}