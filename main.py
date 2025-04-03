from fastapi import FastAPI, HTTPException, UploadFile, File, Depends
from pydantic import BaseModel, Field
from typing import List, Dict
import pandas as pd
import io
import uuid

app = FastAPI()

# In-memory storage for users
users_db: Dict[str, Dict] = {}

class User(BaseModel): #BaseModel自動處理驗證、轉換與文件產生
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    name: str
    age: int

class UserCreate(BaseModel):
    name: str
    age: int

@app.post("/users", response_model=User, status_code=201)
async def create_user(user_in: UserCreate):
    """
    Create a new user.
    """
    new_user = User(**user_in.model_dump()) #使用model_dump()將user_in轉成字典型態
    if any(u['name'] == new_user.name for u in users_db.values()):
         raise HTTPException(status_code=400, detail=f"User with name '{new_user.name}' already exists")
    users_db[new_user.id] = new_user.model_dump()
    return new_user

@app.get("/users", response_model=List[User])
async def get_users():
    """
    Get a list of all users.
    """
    return list(users_db.values())

@app.delete("/users/{user_id}", status_code=204)
async def delete_user(user_id: str):
    """
    Delete a user by ID.
    """
    if user_id not in users_db:
        raise HTTPException(status_code=404, detail="User not found")
    del users_db[user_id]
    return None

@app.post("/users/upload_csv", status_code=201)
async def upload_users_csv(file: UploadFile = File(...)):
    """
    Add multiple users from an uploaded CSV file.
    The CSV file must have 'name' and 'age' columns.
    """
    if file.content_type != 'text/csv':
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV file.")

    contents = await file.read()
    try:
        # Use StringIO to treat the byte string as a file
        df = pd.read_csv(io.StringIO(contents.decode('utf-8')))
    except Exception as e:
         raise HTTPException(status_code=400, detail=f"Error processing CSV file: {e}")

    # Expect 'Name' and 'Age' columns (case-sensitive)
    if not {'Name', 'Age'}.issubset(df.columns):
        raise HTTPException(status_code=400, detail="CSV must contain 'Name' and 'Age' columns.")

    added_count = 0
    skipped_count = 0
    skipped_names = []

    for _, row in df.iterrows():
        try:
            # Use 'Name' and 'Age' from the CSV row
            user_data = UserCreate(name=row['Name'], age=int(row['Age']))
            # Check if user already exists by name before adding
            if any(u['name'] == user_data.name for u in users_db.values()):
                skipped_count += 1
                skipped_names.append(user_data.name)
                continue

            new_user = User(**user_data.model_dump())
            users_db[new_user.id] = new_user.model_dump()
            added_count += 1
        except Exception as e:
            # Handle potential data validation errors or other issues per row
            print(f"Skipping row due to error: {row} - {e}") # Log error for debugging
            skipped_count += 1
            # Use 'Name' for skipped names if available
            skipped_names.append(str(row.get('Name', 'N/A')))


    return {
        "message": f"Processed CSV file.",
        "added_users": added_count,
        "skipped_users": skipped_count,
        "skipped_names": skipped_names
    }


@app.get("/users/average_age")
async def get_average_age_by_group():
    """
    Calculate the average age of users grouped by the first letter of their name.
    """
    if not users_db:
        return {"message": "No users available to calculate average age."}

    users_list = list(users_db.values())
    df = pd.DataFrame(users_list)

    # Ensure 'name' is string and handle potential errors
    df['name'] = df['name'].astype(str)
    df['group'] = df['name'].str[0].str.upper() # Group by first letter, uppercase

    # Ensure 'age' is numeric, coercing errors to NaN which will be ignored by mean()
    df['age'] = pd.to_numeric(df['age'], errors='coerce')

    # Calculate average age, dropping groups where age might be NaN after coercion
    average_ages = df.dropna(subset=['age']).groupby('group')['age'].mean().round(2).to_dict()

    return average_ages

# To run the app (save this as main.py and run uvicorn main:app --reload)
# Example: uvicorn fastapi_user_app.main:app --reload
