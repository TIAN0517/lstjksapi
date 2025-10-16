import uvicorn
uvicorn.run('services.main.main:app', host='0.0.0.0', port=18001)