import zipfile
import pathlib
import json
import logging
import mmzip.mmdir as mmdir
import mmzip.mm_const as mm_const

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)

def zip_to_mmdir(file_path: str, extract_to: str):
    logger.info("Extracting %s to %s", file_path, extract_to)
    file_path_p = pathlib.Path(file_path)
    try:
        with zipfile.ZipFile(file_path) as zf:
            mmdir_obj = mmdir.MMDir(extract_to)
            mmdir_obj.create()
            entry_list = _extract_and_create_entry_list(zf, mmdir_obj.base_dir_path)
            _make_entry_set(file_path_p.name, zf.comment, entry_list, mmdir_obj.base_dir_path)
    except zipfile.BadZipFile as e:
        logger.error("Failed to extract ZIP file: %s", e)
        raise
    except zipfile.LargeZipFile as e:
        logger.error("Failed to extract ZIP file: %s", e)
        raise

def _extract_and_create_entry_list(zf :zipfile.ZipFile, mm_dir_path: pathlib.Path) -> list:
    i = 1
    entry_list = []
    for info in zf.infolist():
        if not info.is_dir():
            entry_name = mm_const.FILE_PATH_FORMAT_DATA.format(i)
            data_path = mm_dir_path / entry_name
            try:
                with zf.open(info.filename) as f:
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

def _info_to_entry_dict(info: zipfile.ZipInfo, entry_name: str) -> dict:
    logger.debug("filename        : %s", info.filename)
    logger.debug("orig_filename   : %s", info.orig_filename)
    logger.debug("date_time       : %s", info.date_time)
    logger.debug("isdir           : %s", info.is_dir())
    logger.debug("file_size       : %s", info.file_size)
    logger.debug("extract_version : %s", info.extract_version)
    logger.debug("compress_type   : %s", info.compress_type)
    logger.debug("volume          : %s", info.volume)
    logger.debug("comment         : %s", info.comment)
    logger.debug("CRC             : %s", info.CRC)
    logger.debug("internal_attr   : %s", info.internal_attr)
    logger.debug("flag_bits       : %s", info.flag_bits)
    return {
        mm_const.ENTRY_FILE_NAME: info.filename,
        mm_const.ENTRY_DATE_TIME: info.date_time,
        mm_const.ENTRY_IS_DIR: info.is_dir(),
        mm_const.ENTRY_COMMENT: str(info.comment, "utf-8"),
        mm_const.ENTRY_ENTRY_NAME: entry_name
    }

def _make_entry_set(file_name: str, comment: str, entry_list: list, mm_dir_path: pathlib.Path):
    entry_set = {
        mm_const.ENTRY_SET_FILE_NAME: file_name,
        mm_const.ENTRY_SET_ENTRY_LIST: entry_list,
        mm_const.ENTRY_SET_COMMENT: str(comment, "utf-8")
    }
    entry_set_file_path = mm_dir_path / mm_const.FILE_PATH_FORMAT_ENTRY_SET.format(0)
    try:
        with entry_set_file_path.open("w") as f:
            json.dump(entry_set, f)
    except IOError as e:
        logger.error("Failed to write entry set file: %s", e)
        raise

