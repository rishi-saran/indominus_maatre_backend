## Maathre setup

### 1. Create and Activate Virtual Environment

**-> Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```
**-> macOS / Linux:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Run the Application
```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Note:** Once running, access the API at `http://localhost:8000` and auto-generated docs at `http://localhost:8000/docs`.

## Running Scripts

### 1. seed_pages.py
```bash
python -m scripts.pages.seed_pages
or
python3 -m scripts.pages.seed_pages
```
