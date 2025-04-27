import rarfile
import pathlib
import json
import logging
import mmzip.mmdir as mmdir
import mmzip.mm_const as mm_const

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

def rar_to_mmdir(file_path: str, extract_to: str):
    logger.info("Extracting %s to %s", file_path, extract_to)
    file_path_p = pathlib.Path(file_path)
    try:
        with rarfile.RarFile(file_path) as rf:
            mmdir_obj = mmdir.MMDir(extract_to)
            mmdir_obj.create()
            entry_list = _extract_and_create_entry_list(rf, mmdir_obj.base_dir_path)
            _make_entry_set(file_path_p.name, rf.comment, entry_list, mmdir_obj.base_dir_path)
    except rarfile.Error as e:
        logger.error("Failed to extract RAR file: %s", e)
        raise

def _extract_and_create_entry_list(rf: rarfile.RarFile, mm_dir_path: pathlib.Path) -> list:
    i = 1
    entry_list = []
    for info in rf.infolist():
        if not info.is_dir():
            entry_name = mm_const.FILE_PATH_FORMAT_DATA.format(i)
            data_path = mm_dir_path / entry_name
            try:
                with rf.open(info.filename) as f:
                    with data_path.open("wb") as f2:
                        f2.write(f.read())
                i += 1
            except IOError as e:
                logger.error("Failed to extract file %s: %s", info.filename, e)
                raise
        else:
            entry_name = None
        entry = _info_to_entry_dict(info, entry_name)
        entry_list.append(entry)
    return entry_list

def _info_to_entry_dict(info: rarfile.RarInfo, entry_name: str) -> dict:
    logger.debug("filename        : %s", info.filename)
    logger.debug("orig_filename   : %s", info.orig_filename)
    logger.debug("arctime         : %s", info.arctime)
    logger.debug("atime           : %s", info.atime)
    logger.debug("date_time       : %s", info.date_time)
    logger.debug("ctime           : %s", info.ctime)
    logger.debug("mtime           : %s", info.mtime)
    logger.debug("isdir           : %s", info.is_dir())
    logger.debug("file_size       : %s", info.file_size)
    logger.debug("extract_version : %s", info.extract_version)
    logger.debug("flags           : %s", info.flags)
    logger.debug("compress_type   : %s", info.compress_type)
    logger.debug("mode            : %s", info.mode)
    logger.debug("type            : %s", info.type)
    logger.debug("volume          : %s", info.volume)
    logger.debug("comment         : %s", info.comment)
    return {
        mm_const.ENTRY_FILE_NAME: info.filename,
        mm_const.ENTRY_DATE_TIME: info.date_time,
        mm_const.ENTRY_IS_DIR: info.is_dir(),
        mm_const.ENTRY_COMMENT: info.comment,
        mm_const.ENTRY_ENTRY_NAME: entry_name
    }

def _make_entry_set(file_name: str, comment: str, entry_list: list, mm_dir_path: pathlib.Path):
    entry_set = {
        mm_const.ENTRY_SET_FILE_NAME: file_name,
        mm_const.ENTRY_SET_ENTRY_LIST: entry_list,
        mm_const.ENTRY_SET_COMMENT: comment
    }
    entry_set_file_path = mm_dir_path / mm_const.FILE_PATH_FORMAT_ENTRY_SET.format(0)
    try:
        with entry_set_file_path.open("w") as f:
            json.dump(entry_set, f)
    except IOError as e:
        logger.error("Failed to write entry set file: %s", e)
        raise

