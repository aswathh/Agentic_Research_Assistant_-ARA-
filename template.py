import os 
import logging
from pathlib import Path

logging.basicConfig(format='[%(asctime)s]:%(message)s',level=logging.INFO)

list_of_files=[
    "src/__init__.py",
    "src/agents/__init__.py",
    "src/rag/__init__.py",
    "src/mcp/__init__.py",
    "src/api/__init__.py",
    "src/api/routes/__init__.py",
    "src/observability/__init__.py",
    "src/core/__init__.py"
    "src/core/config.py"
    "src/core/llm.py"

]

for filepath in list_of_files:
    filepath = Path(filepath)
    filedir,filename=os.path.split(filepath)

    if filedir !="":
        os.makedirs(filedir,exist_ok=True)
        logging.info(f"Creating a file {filedir} with the filename {filename}")
    if not os.path.exists(filepath) or os.path.getsize(filepath):
        with open(filepath,"w") as f:
            pass
        logging.info(f"creating an empty folder{filepath}")
    else:
        logging.info(f"the file directory is already exist")