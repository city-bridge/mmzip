import datetime
import os
import pathlib
import json
import re
import logging
import zipfile
import mmzip.mm_const as mm_const

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

class MMDir:
    base_dir_path: pathlib.Path
    data_dir_path: pathlib.Path
    info_dir_path: pathlib.Path
    info_file_path: pathlib.Path

    def __init__(self, path: str):
        self.base_dir_path = pathlib.Path(path)
        self.data_dir_path = self.base_dir_path / mm_const.DIR_PATH_DATA
        self.info_dir_path = self.base_dir_path / mm_const.DIR_PATH_MM_INFO
        self.info_file_path = self.base_dir_path / mm_const.FILE_PATH_INFO_JSON
    
    def create(self) -> None:
        if self.base_dir_path.exists():
            raise Exception("Destination directory already exists")
        
        try:
            self.base_dir_path.mkdir()
            self.data_dir_path.mkdir()
            self.info_dir_path.mkdir()
            self._create_info()
            logger.info("Directory structure created successfully at %s", self.base_dir_path)
        except Exception as e:
            logger.error("An unexpected error occurred while creating directories: %s", e)
            raise
    
    def _create_info(self) -> None:
        info = {
            mm_const.INFO_DICT_TYPE: mm_const.INFO_DICT_TYPE_MMZIP
        }
        try:
            with self.info_file_path.open("w") as f:
                json.dump(info, f)
        except IOError as e:
            logger.error("Failed to write info file: %s", e)
            raise
    
    def have_info(self) -> bool:
        return self.info_file_path.exists()
    
    def get_entry_set_path_list(self) -> list:
        entry_set_list = []
        for file in self.info_dir_path.glob(mm_const.FILE_PATH_GLOB_FORMAT_ENTRY_SET):
            entry_set_list.append(file)
        for file in self.info_dir_path.glob(mm_const.FILE_PATH_GLOB_FORMAT_ENTORY_SET):
            entry_set_list.append(file)
        return entry_set_list

    def get_entry_set_list(self):
        entry_set_list = []
        for file in self.get_entry_set_path_list():
            data = file.read_text()
            entry_set_list.append(json.loads(data))
        return entry_set_list
    
    def get_entry_set(self, entry_set_num: int) -> dict:
        entry_set_list = self.get_entry_set_list()
        if entry_set_num < 0:
            raise Exception("entry not found")
        if entry_set_num >= len(entry_set_list):
            raise Exception("entry not found")

        return entry_set_list[entry_set_num]

    def get_data_files(self) -> list:
        data_files = []
        for file in self.data_dir_path.iterdir():
            data_files.append({
                "path": file,
                "entry_name": mm_const.DIR_PATH_DATA + file.name,
            })
        return data_files

    def extract(self, entry_set_num: int, extract_to: str) -> None:
        logger.info("Extracting entry set %d to %s", entry_set_num, extract_to)
        entry_set = self.get_entry_set(entry_set_num)
        extract_path = pathlib.Path(extract_to)
        if extract_path.exists():
            raise Exception("Destination directory already exists")
        extract_path.mkdir()
        for entry in entry_set[mm_const.ENTRY_SET_ENTRY_LIST]:
            output_path: pathlib.Path = extract_path / entry[mm_const.ENTRY_FILE_NAME]
            date_time = entry[mm_const.ENTRY_DATE_TIME]
            atime = datetime.datetime(year=date_time[0], month=date_time[1], day=date_time[2], hour=date_time[3], minute=date_time[4], second=date_time[5], microsecond=0, tzinfo=datetime.timezone.utc)

            if entry[mm_const.ENTRY_IS_DIR]:
                output_path.mkdir(parents=True, exist_ok=True)
                os.utime(path=str(output_path), times=(atime.timestamp(), atime.timestamp()))
            else:
                output_path.parent.mkdir(parents=True, exist_ok=True)
                entry_path: pathlib.Path = self.base_dir_path / entry[mm_const.ENTRY_ENTRY_NAME]
                logger.debug("Extracting %s to %s", entry_path, output_path)
                output_path.write_bytes(entry_path.read_bytes())
                os.utime(path=str(output_path), times=(atime.timestamp(), atime.timestamp()))
        logger.info("Extraction of entry set %d completed successfully to %s", entry_set_num, extract_to)

    def to_mmzip(self, output_path: str) -> None:
        # Placeholder for conversion logic to MMZip format
        logger.info("Converting to MMZip format at %s", output_path)
        zip_file_path = pathlib.Path(output_path)
        with zipfile.ZipFile(zip_file_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
            for root, _, files in os.walk(self.base_dir_path):
                for file in files:
                    file_path = pathlib.Path(root) / file
                    arcname = file_path.relative_to(self.base_dir_path)
                    zipf.write(file_path, arcname)
