# Running the Project

Follow the steps below to run the application.

## 1. Navigate to the Project Directory

```bash
cd <project-folder>
```

## 2. Create a Virtual Environment

```bash
python -m venv venv
```

## 3. Activate the Virtual Environment

### Windows

```bash
venv\Scripts\activate
```

### Mac / Linux

```bash
source venv/bin/activate
```

## 4. Install Required Dependencies

```bash
pip install fastapi uvicorn mysql-connector-python pydantic
```

## 5. Run the Application

```bash
uvicorn main:app --reload
```

## 6. Open API Documentation

Open a browser and navigate to:

```text
http://127.0.0.1:8000/docs
```
