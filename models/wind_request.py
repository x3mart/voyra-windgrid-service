from pydantic import BaseModel


class WindRequest(BaseModel):
    min_x: float
    max_x: float

    min_y: float
    max_y: float

    nx: int = 128
    ny: int = 128