
# FarmLens Backend (FastAPI + MongoDB)

This project provides a FastAPI backend with MongoDB for todo and user authentication.

## Requirements

- Python 3.10+
- MongoDB (local or Atlas)

## Setup (clone from GitHub)

1) Create a virtual environment

```bash
python -m venv venv
```

2) Activate the environment

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
./venv/Scripts/Activate.ps1
```

macOS/Linux:

```bash
source venv/bin/activate
```

3) Install dependencies

```bash
pip install -r requirements.txt
```

4) Create a .env file in the project root

```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
```

## Run the server

```bash
python main.py
```

The API will start at http://127.0.0.1:8000

## API overview

- Auth:
	- POST /auth/register
	- POST /auth/login
	- POST /auth/refresh

## Notes

- Change JWT_SECRET in production.
- MONGO_URL should point to your MongoDB instance.
