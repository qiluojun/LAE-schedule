import uvicorn
# 确保所有模型都被导入，避免关系解析问题
from app.models import *
from app.main import app

if __name__ == "__main__":
    import sys
    port = 8008
    if len(sys.argv) > 1 and sys.argv[1] == "--port" and len(sys.argv) > 2:
        port = int(sys.argv[2])
    # uvicorn.run(app, host="127.0.0.1", port=port, reload=False)
    uvicorn.run(app, host="0.0.0.0", port=port, reload=False)