"""FastAPI"""
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from postgres import VaultRepository

app = FastAPI(title="Vault - testing FastAPI")
db = VaultRepository()
db.create_table()

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

#без шифрования
@app.post("/api/write", status_code=201)
async def write(title: str, secret:str):
    try:
        secret_dict = {
            "title": title,
            "secret": secret
        }

        if not secret_dict.get("title") or not secret_dict.get("secret"):
            raise HTTPException(status_code=400, detail="title and secret text are required")

        session_id = uuid.uuid4()

        db.insert_table(session_id=session_id, dict_secret=secret_dict)
        return {"status": "lol it worked", "id": str(session_id)}

    except Exception as error:
        print(f"ERROR: {error}")
        raise HTTPException(status_code=500, detail=str(error))

@app.get("/api/read", status_code=200)
async def read(session_id: str):
    try:
        return {"status": "works too", "result": db.get_secret_by_id(session_id)}
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.get("/api/show", status_code=200)
async def show():
    try:
        return {"status": "show table", "result": db.show_table()}
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.put("/api/update", status_code=200)
async def update(session_id: str, title: str, secret: str):
    try:
        secret_dict = {
            "title": title,
            "secret": secret
        }
        return {"status": "UPDATED", "result": db.update_by_id(uuid_code=session_id, dict_secret=secret_dict)}
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.delete("/api/delete", status_code=200)
async def delete(session_id: str):
    try:
        return {"status": "deleted", "result": db.delete_by_id(uuid_code=session_id)}
    except Exception as error:
        raise HTTPException(status_code=404, detail=str(error))


@app.post("/api/dump", status_code=200)
async def dump(backup_dir: str="."):
    try:
        db.backup(backup_dir=backup_dir)
        return {"status": "DUMP", "result":True}
    except FileNotFoundError:
        error_msg = "Ошибка: утилита pg_dump не найдена. Убедитесь, что PostgreSQL клиент установлен и доступен в PATH."
        print(error_msg)
        raise HTTPException(status_code=500, detail=error_msg)

@app.post("/api/restore", status_code=200)
async def restore(path: str):
    try:
        db.restore(path)
        return {"status": "RESTORED", "result": True}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))