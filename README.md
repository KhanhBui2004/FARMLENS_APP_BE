# FarmLens Backend (FastAPI + MongoDB)

FastAPI backend for FarmLens providing user authentication, Sentinel-2 analysis and change-detection features backed by MongoDB.

## Requirements

- Python 3.10+
- MongoDB (local or Atlas)
- Optional: Google Earth Engine account (only required for Sentinel image retrieval)

## Quick Start

1. Clone the repository and create a virtual environment

```bash
git clone <repo-url>
cd farmlens_be
python -m venv venv
```

2. Activate the virtual environment

Windows PowerShell:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
./venv/Scripts/Activate.ps1
```

macOS / Linux:

```bash
source venv/bin/activate
```

3. Install dependencies

```bash
pip install -r requirements.txt
```

4. Create a `.env` file in the project root. Example:

```env
MONGO_URL=mongodb://localhost:27017
JWT_SECRET=change_me
JWT_ALGORITHM=HS256
# Optional overrides
ACCESS_TOKEN_EXPIRE_MINUTES=30
REFRESH_TOKEN_EXPIRE_DAYS=7
GEE_SERVICE_ACCOUNT=your-service-account@your-project.iam.gserviceaccount.com
```

## Training AI Model

The training notebook is available at:

```text
model/unet_model.ipynb
```

This notebook is used to prepare the DeepGlobe dataset, train the U-Net model on Kaggle, and export the final checkpoint for backend inference.

### Dataset Split (70/20/10)

The DeepGlobe dataset should be split into:

- **70%** training set
- **20%** validation set
- **10%** test set

Recommended directory structure:

```text
dataset/
  train/
    img/
    ann/
  val/
    img/
    ann/
  test/
    img/
    ann/
```

Make sure each image file matches its corresponding mask file.

### Training on Kaggle

1. Upload the project folder or notebook to Kaggle.
2. Upload the DeepGlobe dataset to Kaggle as a Dataset, or mount it from Kaggle input storage.
3. In the notebook, update dataset paths so they point to the Kaggle input directory.

Example:

```python
DATASET_DIR = "/kaggle/input/deepglobe-split/dataset"
TRAIN_IMG_DIR = f"{DATASET_DIR}/train/img"
TRAIN_MASK_DIR = f"{DATASET_DIR}/train/ann"
VAL_IMG_DIR = f"{DATASET_DIR}/val/img"
VAL_MASK_DIR = f"{DATASET_DIR}/val/ann"
TEST_IMG_DIR = f"{DATASET_DIR}/test/img"
TEST_MASK_DIR = f"{DATASET_DIR}/test/ann"
```

4. Enable **GPU** in Kaggle Notebook before training.
5. Run all cells in `model/unet_model.ipynb`.

### Model Output

After training, save the final model checkpoint with the following name:

```text
unet_efficientnet_b5.pth
```

Example save path in Kaggle working directory:

```python
torch.save(model.state_dict(), "/kaggle/working/unet_efficientnet_b5.pth")
```

### Copy Model Back to Project

After training finishes, download the exported checkpoint from Kaggle and place it in the project folder:

```text
model/unet_efficientnet_b5.pth
```

This file will be used by the backend for inference.

### Notes

- The notebook already contains the main training pipeline.
- Only the dataset path and output checkpoint path need to be adjusted for Kaggle.
- Ensure the backend model path matches the exported checkpoint name before running the API.

## Google Earth Engine (GEE) - Optional

To enable Sentinel-2 imagery retrieval via Earth Engine:

1. Enable Earth Engine API in Google Cloud and create a Service Account.
2. Grant the Service Account the required permissions and download its JSON key.
3. Place the key file in the project root as `gee_key.json` and set `GEE_SERVICE_ACCOUNT` in `.env`.
4. Alternatively, run `earthengine authenticate` for interactive authentication.

If you don't need GEE locally or for tests, you can skip this — tests use lightweight shims so you can run them without a working GEE setup.

## Running the server

Start the app using either the repository entrypoint or Uvicorn:

```bash
# Simple entrypoint
python main.py

# Development server with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open the interactive API docs at `http://127.0.0.1:8000/docs`.

## API Overview

- Auth
  - `POST /auth/register` — register a new user
  - `POST /auth/login` — login and receive access/refresh tokens
  - `POST /auth/refresh` — refresh access token

- Analysis
  - `GET /analysis/segmentation` — list segmentation history
  - `POST /analysis/segmentation` — request segmentation (uses GEE)
  - `DELETE /analysis/segmentation/{id}` — delete a segmentation
  - `POST /analysis/statistics` — compute segmentation statistics
  - `GET /analysis/statistics` — get statistics by analysis id

- Change Detection
  - `GET /analysis/change-detection` — list change detection history
  - `POST /analysis/change-detection` — run change detection for two dates

For full request/response schemas see the OpenAPI docs at `/docs`.

## Testing

Tests use `pytest` and live in the `tests/` directory. The test suite includes lightweight shims (in `tests/conftest.py`) so it can run without heavy native dependencies (Earth Engine, segmentation model, bcrypt, etc.).

Run tests from the project root (PowerShell example):

```powershell
$env:PYTHONPATH='.'; pytest -q
```

If you prefer to run tests against a full dependency install, first run:

```bash
pip install -r requirements.txt
pytest -q
```

## Production notes

- Use a strong `JWT_SECRET` in production and keep it secret.
- Ensure `MONGO_URL` points to a secure, backed-up MongoDB instance.
- Consider running the app behind a reverse proxy (nginx) and enabling HTTPS.

If you want, I can also add a brief `Makefile` or `scripts/` with common commands (`start`, `test`, `lint`).
