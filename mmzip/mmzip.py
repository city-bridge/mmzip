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

class MMZip:
    path: set
    zip_obj: zipfile.ZipFile

    def __init__(self, path: str):
        self.path = path
        self.zip_obj = zipfile.ZipFile(self.path,"r")    
    
    def have_info(self) -> bool:
        return mm_const.FILE_PATH_INFO_JSON in self.zip_obj.NameToInfo.keys()
    
    def _get_entry_set_zipinfo_list(self) -> list:
        entry_set_list = []
        pt = re.compile(mm_const.FILE_PATH_REGEX_ENTRY_SET)
        for file in self.zip_obj.filelist:
            if pt.match(file.filename):
                entry_set_list.append(file)
        pt = re.compile(mm_const.FILE_PATH_REGEX_ENTORY_SET)
        for file in self.zip_obj.filelist:
            if pt.match(file.filename):
                entry_set_list.append(file)
        return entry_set_list

    def get_entry_set_list(self):
        entry_set_list = []
        for file in self._get_entry_set_zipinfo_list():
            data = self.zip_obj.open(file,"r").read()
            entry_set_list.append(json.loads(data))
        return entry_set_list
    
    def get_entry_set(self, entry_set_num: int) -> dict:
        entry_set_list = self.get_entry_set_list()
        if entry_set_num < 0:
            raise Exception("entry not found")
        if entry_set_num >= len(entry_set_list):
            raise Exception("entry not found")

        return entry_set_list[entry_set_num]

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
                zip_info = self.zip_obj.NameToInfo[entry[mm_const.ENTRY_ENTRY_NAME]]
                with self.zip_obj.open(zip_info,"r") as zf:
                    with output_path.open("wb") as of:
                        of.write(zf.read())
                os.utime(path=str(output_path), times=(atime.timestamp(), atime.timestamp()))
        logger.info("Extraction of entry set %d completed successfully to %s", entry_set_num, extract_to)

    def to_mmdir(self, output_path: str) -> None:
        # Placeholder for conversion logic to MMDir format
        logger.info("Converting to MMDir format at %s", output_path)
        out_dir_path = pathlib.Path(output_path)
        out_dir_path.mkdir(parents=True, exist_ok=True)
        for entry in self.zip_obj.filelist:
            data_path = out_dir_path / entry.filename
            data_path.parent.mkdir(parents=True, exist_ok=True)
            with self.zip_obj.open(entry,"r") as zf:
               with data_path.open("wb") as of:
                    of.write(zf.read())
