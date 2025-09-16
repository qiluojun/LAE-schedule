#!/usr/bin/env python3
"""
调试服务器 - 添加异常处理来查看具体错误
"""

import uvicorn
import traceback
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from app.main import app

# 添加全局异常处理器
@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    print(f"=== Exception Caught ===")
    print(f"URL: {request.url}")
    print(f"Exception Type: {type(exc).__name__}")
    print(f"Exception Message: {str(exc)}")
    print(f"Traceback:")
    traceback.print_exc()
    print("=======================")

    return JSONResponse(
        status_code=500,
        content={
            "error": str(exc),
            "type": type(exc).__name__,
            "url": str(request.url)
        }
    )

if __name__ == "__main__":
    print("Starting debug server...")
    uvicorn.run(app, host="127.0.0.1", port=8001, reload=False)