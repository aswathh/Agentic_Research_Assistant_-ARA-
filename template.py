import os 
import logging
from pathlib import Path

logging.basicConfig(format='[%(asctime)s]:%(message)s',level=logging.INFO)

list_of_files=[

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
        logiing.info(f"the file directory is already exist")