from fastapi import Request

def get_qdrant(request: Request):
    return request.app.state.qdrant