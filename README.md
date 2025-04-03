# FastAPI User Management API

This is a simple FastAPI application for managing users. It provides the following RESTful APIs:

*   **POST /users:** Create a new user with "name" and "age" fields.
*   **GET /users:** Get a list of all users.
*   **DELETE /users/{user\_id}:** Delete a specific user by ID.
*   **POST /users/upload\_csv:** Add multiple users from a CSV file. The CSV file should have "Name" and "Age" columns.
*   **GET /users/average\_age:** Calculate the average age of users, grouped by the first character of their usernames.

## Requirements

*   Python 3.7+
*   FastAPI
*   Uvicorn
*   Pandas
*   python-multipart
*   httpx
*   coverage

## Installation

1.  Clone the repository:

    ```bash
    git clone [repository_url]
    ```
2.  Navigate to the project directory:

    ```bash
    cd fastapi_user_app
    ```
3.  Create a virtual environment:

    ```bash
    python3 -m venv venv
    ```
4.  Activate the virtual environment:

    ```bash
    source venv/bin/activate
    ```
5.  Install the dependencies:

    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  Run the application:

    ```bash
    uvicorn main:app --reload --port 8000
    ```

2.  Open your browser and go to `http://127.0.0.1:8000/docs` to access the interactive API documentation (Swagger UI).

## Testing

To run the unit tests:

```bash
python -m unittest test_main.py
```

To calculate test coverage, you can use the `coverage` package:

```bash
coverage run -m unittest test_main.py
coverage report -m
```

## CSV File Format

The CSV file uploaded to the `/users/upload_csv` endpoint should have the following format:

```
Name,Age
John,30
Jane,25
```

## Notes

*   The application uses an in-memory database for storing users. Data will be lost when the application restarts.
*   Error handling is implemented for duplicate user names and invalid CSV file formats.

## Code Structure

The project is structured as follows:

*   `main.py`: This file contains the main FastAPI application logic, including:
    *   API endpoints for creating, retrieving, updating, and deleting users.
    *   CSV upload functionality using Pandas.
    *   Average age calculation grouped by the first letter of the username.
    *   Pydantic models for data validation.
*   `test_main.py`: This file contains the unit tests for the API endpoints, written using Python's built-in `unittest` module.
*   `requirements.txt`: This file lists the project dependencies.
