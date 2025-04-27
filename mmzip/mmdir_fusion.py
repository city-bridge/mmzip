from mmzip.mmdir import MMDir
import json
import shutil
import mmzip.mm_const as mm_const
from mmzip.mmdir_remove_same_file import mmdir_remove_same_file

def mmdir_fusion(mm_dir_path1: str, mm_dir_path2: str, mm_dir_path_dest: str) -> None:
    mm_dir1 = MMDir(mm_dir_path1)
    mm_dir2 = MMDir(mm_dir_path2)
    mm_dir_dest = MMDir(mm_dir_path_dest)

    if not mm_dir1.have_info() or not mm_dir2.have_info():
        raise Exception("One of the directories does not have an info file")

    mm_dir_dest.create()

    data_conv_maps = _copy_data_files(mm_dir1, mm_dir2, mm_dir_dest)
    entry_set_list_1 = _conv_entry_set(mm_dir1, data_conv_maps["dir1_conv_map"])
    entry_set_list_2 = _conv_entry_set(mm_dir2, data_conv_maps["dir2_conv_map"])
    entry_set_list_1.extend(entry_set_list_2)
    _save_entry_set(mm_dir_dest, entry_set_list_1)
    mmdir_remove_same_file(mm_dir_dest.base_dir_path)

def _copy_data_files(mm_dir1: MMDir, mm_dir2: MMDir, mm_dir_dest: MMDir) -> dict:
    i = 0
    dir1_conv_map = []
    for file in mm_dir1.get_data_files():
        src_file = file["path"]
        src_entry_name = file["entry_name"]
        dest_entry_name = mm_const.FILE_PATH_FORMAT_DATA.format(i)
        dest_file_path = mm_dir_dest.base_dir_path / dest_entry_name
        shutil.copy(src=src_file, dst=dest_file_path)
        dir1_conv_map.append({
            "src_entry_name": src_entry_name,
            "dest_entry_name": dest_entry_name
        })
        i += 1
    dir2_conv_map = []
    for file in mm_dir2.get_data_files():
        src_file = file["path"]
        src_entry_name = file["entry_name"]
        dest_entry_name = mm_const.FILE_PATH_FORMAT_DATA.format(i)
        dest_file_path = mm_dir_dest.base_dir_path / dest_entry_name
        shutil.copy(src=src_file, dst=dest_file_path)
        dir2_conv_map.append({
            "src_entry_name": src_entry_name,
            "dest_entry_name": dest_entry_name
        })
        i += 1
    return {
        "dir1_conv_map": dir1_conv_map,
        "dir2_conv_map": dir2_conv_map
    }


def _conv_entry_set(mm_dir: MMDir, conv_map: list) -> list:
    entry_set_list = mm_dir.get_entry_set_list()
    for entry_set in entry_set_list:
        for entry in entry_set[mm_const.ENTRY_SET_ENTRY_LIST]:
            for conv in conv_map:
                if entry[mm_const.ENTRY_ENTRY_NAME] == conv["src_entry_name"]:
                    entry[mm_const.ENTRY_ENTRY_NAME] = conv["dest_entry_name"]
                    break
    return entry_set_list

def _save_entry_set(mm_dir_dest: MMDir, entry_set_list: list) -> None:
    i = 0
    for entry_set in entry_set_list:
        entry_set_file = mm_dir_dest.base_dir_path / mm_const.FILE_PATH_FORMAT_ENTRY_SET.format(i)
        with open(entry_set_file, "w", encoding="utf-8") as f:
            json.dump(entry_set, f)
        i += 1
