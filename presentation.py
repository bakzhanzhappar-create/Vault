"""FastAPI"""
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from postgres import VaultRepository

app = FastAPI(title="Vault - testing FastAPI")
db = VaultRepository()
db.create_table()
db.create_config_table()  # Создаем таблицу конфигов для Zero-Knowledge

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/static", StaticFiles(directory="."), name="static")

@app.get("/")
async def serve_index():
    return FileResponse("index.html")

@app.get("/auth")
async def serve_auth():
    return FileResponse("auth.html")

# --- Конфигурация хранилища (Zero-Knowledge) ---

@app.get("/api/config/get")
async def get_config():
    cfg = db.get_config()
    if not cfg:
        raise HTTPException(status_code=404, detail="Config not initialized")
    salt, nonce, encrypted_dek = cfg
    return {"salt": salt, "nonce": nonce, "encrypted_dek": encrypted_dek}

@app.post("/api/config/set")
async def set_config(request: Request):
    try:
        body = await request.json()
        salt = body.get("salt")
        nonce = body.get("nonce")
        encrypted_dek = body.get("encrypted_dek")

        if not salt or not nonce or not encrypted_dek:
            raise HTTPException(status_code=400, detail="Missing configuration fields")

        db.set_config(salt, nonce, encrypted_dek)
        return {"status": "success"}
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))

# --- Записи в хранилище (с клиентским шифрованием) ---

@app.post("/api/write", status_code=201)
async def write(request: Request):
    try:
        body = await request.json()
        session_id = body.get("session_id")
        title_data = body.get("title")  # {nonce, ciphertext}
        secret_data = body.get("secret") # {nonce, ciphertext}

        if not session_id or not title_data or not secret_data:
            raise HTTPException(status_code=400, detail="session_id, title and secret are required")

        parsed_uuid = db.check_uuid(session_id)
        if not parsed_uuid:
            raise HTTPException(status_code=400, detail="Invalid UUID")

        secret_dict = {
            "title": title_data,
            "secret": secret_data
        }

        db.insert_table(session_id=parsed_uuid, dict_secret=secret_dict)
        return {"status": "encrypted write success", "id": str(parsed_uuid)}

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