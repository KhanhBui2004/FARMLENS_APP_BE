
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
GEE_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com
```

## Google Earth Engine (GEE)

Backend su dung GEE de lay anh Sentinel-2. Can set up Service Account va khoa JSON.

1) Dang ky tai khoan GEE (neu chua co) va enable Earth Engine API trong Google Cloud.
2) Tao Service Account trong Google Cloud, cap quyen, tai key JSON.
3) Luu key JSON vao goc du an voi ten: `gee_key.json`.
4) Cap nhat `.env` voi email Service Account:

```env
GEE_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com
```

Neu chua truy cap duoc GEE, chay lenh `earthengine authenticate` trong terminal de xac thuc tai khoan ca nhan.

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
