from pathlib import Path

import numpy as np
from pydantic import BaseModel, ConfigDict

from models.wind_grid_response import WindGridResponse
from models.wind_request import WindRequest

R = 6378137.0


class WindGrid(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    min_lon: float
    max_lon: float

    min_lat: float
    max_lat: float

    dx: float
    dy: float

    nx: int
    ny: int

    u: np.ndarray
    v: np.ndarray

    cycle: str = "00"
    cycle_date: str = "1972"
    
    @staticmethod
    def load(path: Path):
        data = np.load(path, mmap_mode="r")

        return WindGrid(
            min_lon=float(data["min_lon"]),
            max_lon=float(data["max_lon"]),
            min_lat=float(data["min_lat"]),
            max_lat=float(data["max_lat"]),
            dx=float(data["dx"]),
            dy=float(data["dy"]),
            nx=int(data["nx"]),
            ny=int(data["ny"]),
            u=data["u"],
            v=data["v"],
            cycle=data["cycle"].item(),
            cycle_date=data["cycle_date"].item()
        )    

    def _mercator_to_lon(self, x: np.ndarray) -> np.ndarray:
        return np.degrees(x / R)


    def _mercator_to_lat(self, y: np.ndarray) -> np.ndarray:
        return np.degrees(
            2.0 * np.arctan(np.exp(y / R)) - np.pi / 2.0
        )
    
    def _interpolate(self, field: np.ndarray, fx: np.ndarray, fy: np.ndarray) -> np.ndarray:
        ix0 = np.floor(fx).astype(np.int32)
        iy0 = np.floor(fy).astype(np.int32)

        ix1 = ix0 + 1
        iy1 = iy0 + 1

        ix0 = np.clip(ix0, 0, self.nx - 1)
        iy0 = np.clip(iy0, 0, self.ny - 1)

        ix1 = np.clip(ix1, 0, self.nx - 1)
        iy1 = np.clip(iy1, 0, self.ny - 1)

        tx = fx - ix0
        ty = fy - iy0

        f00 = field[iy0, ix0]
        f10 = field[iy0, ix1]
        f01 = field[iy1, ix0]
        f11 = field[iy1, ix1]

        return (
            f00 * (1.0 - tx) * (1.0 - ty)
            + f10 * tx * (1.0 - ty)
            + f01 * (1.0 - tx) * ty
            + f11 * tx * ty
        ).astype(np.float32)

    def resample(
        self,
        wind_request: WindRequest
    ) -> WindGridResponse:
        min_x = wind_request.min_x
        max_x = wind_request.max_x
        min_y = wind_request.min_y
        max_y = wind_request.max_y
        nx = wind_request.nx
        ny = wind_request.ny

        # Строим регулярную сетку в Web Mercator
        x = np.linspace(min_x, max_x, nx, dtype=np.float32)
        y = np.linspace(min_y, max_y, ny, dtype=np.float32)

        mx, my = np.meshgrid(x, y)

        # Переводим координаты обратно в WGS84
        lon = self._mercator_to_lon(mx)
        lat = self._mercator_to_lat(my)

        # Координаты -> дробные индексы исходной сетки GFS
        fx = (lon - self.min_lon) / self.dx
        fy = (lat - self.min_lat) / self.dy

        u = self._interpolate(self.u, fx, fy)
        v = self._interpolate(self.v, fx, fy)

        

        return WindGridResponse(
            min_x=min_x,
            max_x=max_x,
            min_y=min_y,
            max_y=max_y,
            nx=nx,
            ny=ny,
            u=u.ravel().tolist(),
            v=v.ravel().tolist(),
        )