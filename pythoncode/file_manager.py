import os
import shutil
import re
from utils import get_timestamp

def backup_save_file(save_file_path, backup_folder):
    """
    현재의 save_file_path (예: save.sav)를 백업 폴더에
    타임스탬프를 추가한 이름으로 복사합니다.
    """
    if not os.path.exists(save_file_path):
        raise FileNotFoundError(f"지정된 파일이 존재하지 않습니다: {save_file_path}")
    
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    timestamp = get_timestamp()
    file_dir, file_name = os.path.split(save_file_path)
    name, ext = os.path.splitext(file_name)
    backup_file_name = f"{name}_{timestamp}{ext}"
    backup_file_path = os.path.join(backup_folder, backup_file_name)
    
    shutil.copy2(save_file_path, backup_file_path)
    return backup_file_path

def get_original_filename(backup_file_name):
    """
    백업 파일명에서 타임스탬프 (YYMMDD_HHMM)를 제거하여 원본 파일명을 반환합니다.
    예: "save_250401_1526.sav" -> "save.sav"
    """
    # 타임스탬프 패턴: _YYMMDD_HHMM
    return re.sub(r'_\d{6}_\d{4}', '', backup_file_name)

def restore_save_file(backup_file_path, original_folder, original_file_name=None):
    """
    백업 파일을 원래의 save 파일 이름으로 복원합니다.
    기존 파일이 있다면 덮어씁니다.
    
    Parameters:
    backup_file_path (str): 백업 파일 경로
    original_folder (str): 원본 폴더 경로
    original_file_name (str, optional): 원본 파일명. 지정하지 않으면 백업 파일명에서 추출
    
    Returns:
    str: 복원된 파일 경로
    """
    if not os.path.exists(backup_file_path):
        raise FileNotFoundError(f"백업 파일이 존재하지 않습니다: {backup_file_path}")
    
    if not os.path.exists(original_folder):
        os.makedirs(original_folder)
    
    # 원본 파일명이 제공되지 않은 경우 백업 파일명에서 추출
    if original_file_name is None:
        backup_file_name = os.path.basename(backup_file_path)
        original_file_name = get_original_filename(backup_file_name)
    
    destination_path = os.path.join(original_folder, original_file_name)
    shutil.copy(backup_file_path, destination_path)
    return destination_path