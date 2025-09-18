import uvicorn
# 确保所有模型都被导入，避免关系解析问题
from app.models import *
from app.main import app

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8007, reload=False)