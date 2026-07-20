import asyncio
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends #type: ignore
from datetime import datetime

import logger_config
import logging

from config import NPZ_PATH
from models.wind_grid import WindGrid
from models.wind_grid_response import WindGridResponse
from models.wind_request import WindRequest
from services import get_wind_grid, is_update_needed


logger = logging.getLogger(__name__)


async def wind_grid_updater(app: FastAPI, initial_grid: WindGrid | None):
    app.state.wind_grid = initial_grid
        
    while True:
        await asyncio.sleep(300)
        
        try:
            if is_update_needed(app.state.wind_grid):
                new_windgrid = WindGrid.load(NPZ_PATH)
                if new_windgrid is not None:
                    app.state.wind_grid = new_windgrid
                    logger.info(f"[Memory Worker] Сетка ветра в app.state успешно обновлена! {app.state.wind_grid.cycle}, {app.state.wind_grid.cycle_date}")
        except Exception as e:
            logger.exception(f"[Memory Worker] Ошибка при обновлении сетки в памяти")
       
@asynccontextmanager
async def lifespan(app: FastAPI):
    start_grid = None
    
    if NPZ_PATH.exists():
        try:
            logger.info(f"[Lifespan] Найдена сохраненная модель. Загружаем при старте...")
            start_grid = WindGrid.load(NPZ_PATH)
        except Exception as e:
            logger.exception(f"[Lifespan] Не удалось прочитать существующий файл")
    else:
        logger.warning(f"[Lifespam] не найден файл NPZ {NPZ_PATH}")
    
    memory_task = asyncio.create_task(wind_grid_updater(app, start_grid))
        
    yield # FastAPI запущен и принимает запросы
    
    # При остановке сервера отменяем задачи
    memory_task.cancel()
    

app = FastAPI(lifespan=lifespan)



@app.get("/f-api/v2/wind-grid")
async def get_wind(
    request: WindRequest = Depends(),
) -> WindGridResponse:
    wind_grid = get_wind_grid(app)

    return wind_grid.resample(
        request,
    )