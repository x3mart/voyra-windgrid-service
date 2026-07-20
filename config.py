from pathlib import Path

HOME = Path.home()
SOURCE_FOLDER = HOME / "voyra-wind-service" /"wind-data-service" / "data"
NPZ_FILE_NAME = "windgrid.npz"
CURRENT_CYCLE_JSON_PATH = SOURCE_FOLDER / "current_cycle.json"
NPZ_PATH = SOURCE_FOLDER / NPZ_FILE_NAME