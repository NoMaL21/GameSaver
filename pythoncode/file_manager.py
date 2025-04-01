import os
import shutil
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

def restore_save_file(backup_file_path, original_folder, original_file_name):
    """
    백업 파일을 원래의 save 파일 이름으로 복원합니다.
    기존 파일이 있다면 덮어씁니다.
    """
    destination_path = os.path.join(original_folder, original_file_name)
    shutil.copy2(backup_file_path, destination_path)
    return destination_path
