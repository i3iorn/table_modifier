from pathlib import Path
ROOT_PATH: Path = Path(__file__)
while not ROOT_PATH.joinpath("README.md").exists():
    ROOT_PATH = ROOT_PATH.parent
