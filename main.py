import uvicorn

if __name__ == "__main__":
    print("Starting Vault server... ")
    print("STARTED! port 9876 ")

    uvicorn.run(app="presentation:app", host="127.0.0.1", port=9876, reload=True)
