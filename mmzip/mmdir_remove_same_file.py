import pathlib
import json
import logging
import mmzip.mm_const as mm_const
import zlib
import mmzip.mmdir as mmdir

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def mmdir_remove_same_file(mm_dir_path: str):
    mm_dir = mmdir.MMDir(mm_dir_path)   
    data_list = _create_data_list(mm_dir.data_dir_path)
    _search_same_file(data_list)
    _remove_same_file(data_list)
    _remove_same_entry_from_entry_set(mm_dir, data_list)

def _create_data_list(data_dir: pathlib.Path) -> list:
    data_list = []
    for entry in data_dir.iterdir():
        file_data = {
            "path":entry,
            "entry_name": mm_const.DIR_PATH_DATA + entry.name,
            "size": entry.stat().st_size,
            "same_entry_name" : None,
            "crc":None
        }
        logger.debug("file_data: %s", file_data)
        data_list.append(file_data)
    return data_list

def _search_same_file(data_list: list):
    for i in range(len(data_list)):
        now_data = data_list[i]
        now_data_bytes = now_data["path"].read_bytes()

        if now_data["crc"] is None:
            now_data["crc"] = zlib.crc32(now_data_bytes)
        
        # already found same file
        if now_data["same_entry_name"] is not None:
            continue

        for j in range(i+1, len(data_list)):
            next_data = data_list[j]

            if now_data["size"] != next_data["size"]:
                continue

            next_data_bytes = None
            if next_data["crc"] is None:
                next_data_bytes = next_data["path"].read_bytes()
                next_data["crc"] = zlib.crc32(next_data_bytes)
            
            if now_data["crc"] != next_data["crc"]:
                continue
            
            if next_data_bytes is None:
                next_data_bytes = next_data["path"].read_bytes()
            
            if now_data_bytes == next_data_bytes:
                logger.info("Found same file: %s, %s", now_data["entry_name"], next_data["entry_name"])
                next_data["same_entry_name"] = now_data["entry_name"]

def _remove_same_file(data_list: list):
    for data in data_list:
        if data["same_entry_name"] is not None:
            data["path"].unlink()

def _remove_same_entry_from_entry_set(mm_dir: mmdir.MMDir ,data_list: list):
    for entry_set_path in mm_dir.get_entry_set_path_list():
        with entry_set_path.open("r") as f:
            entry_set = json.load(f)
        
        entry_list = entry_set[mm_const.ENTRY_SET_ENTRY_LIST]
        for entry in entry_list:
            for data in data_list:
                if entry[mm_const.ENTRY_ENTRY_NAME] == data["entry_name"]:
                    if data["same_entry_name"] is not None:
                        entry[mm_const.ENTRY_ENTRY_NAME] = data["same_entry_name"]
                    break
        
        with entry_set_path.open("w") as f:
            json.dump(entry_set, f)