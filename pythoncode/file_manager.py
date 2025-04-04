import os
import shutil
import re
import json
from datetime import datetime
from utils import get_timestamp

def backup_save_file(save_file_path, backup_folder, backup_set_id=None):
    """
    현재의 save_file_path (예: save.sav)를 백업 폴더에
    타임스탬프를 추가한 이름으로 복사합니다.
    """
    if not os.path.exists(save_file_path):
        raise FileNotFoundError(f"지정된 파일이 존재하지 않습니다: {save_file_path}")
    
    if not os.path.exists(backup_folder):
        os.makedirs(backup_folder)
    
    timestamp = backup_set_id or get_timestamp()
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

def save_backup_set(backup_folder, set_id, file_paths, description=None):
    """
    백업 세트 정보를 저장합니다.
    
    Parameters:
    backup_folder (str): 백업 폴더 경로
    set_id (str): 백업 세트 ID (타임스탬프)
    file_paths (list): 백업된 파일 경로 목록
    description (str, optional): 백업 세트 설명
    """
    backup_sets_file = os.path.join(backup_folder, "backup_sets.json")
    
    # 기존 백업 세트 정보 로드
    backup_sets = {}
    if os.path.exists(backup_sets_file):
        with open(backup_sets_file, 'r', encoding='utf-8') as f:
            backup_sets = json.load(f)
    
    # 형식화된 날짜 생성
    formatted_date = datetime.strptime(set_id, "%y%m%d_%H%M").strftime("%Y-%m-%d %H:%M")
    
    # 새 백업 세트 정보 추가
    backup_sets[set_id] = {
        "id": set_id,
        "date": formatted_date,
        "description": description or f"백업 ({formatted_date})",
        "files": [os.path.basename(file) for file in file_paths]
    }
    
    # 백업 세트 정보 저장
    with open(backup_sets_file, 'w', encoding='utf-8') as f:
        json.dump(backup_sets, f, ensure_ascii=False, indent=4)
    
    return set_id

def get_backup_sets(backup_folder):
    """
    백업 폴더에서 모든 백업 세트 정보를 가져옵니다.
    
    Parameters:
    backup_folder (str): 백업 폴더 경로
    
    Returns:
    dict: 백업 세트 정보 사전
    """
    backup_sets_file = os.path.join(backup_folder, "backup_sets.json")
    
    if not os.path.exists(backup_sets_file):
        return {}
    
    with open(backup_sets_file, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_backup_set_files(backup_folder, set_id):
    """
    특정 백업 세트에 포함된 모든 파일의 전체 경로를 가져옵니다.
    
    Parameters:
    backup_folder (str): 백업 폴더 경로
    set_id (str): 백업 세트 ID
    
    Returns:
    list: 백업 파일 경로 목록
    """
    backup_sets = get_backup_sets(backup_folder)
    
    if set_id not in backup_sets:
        return []
    
    backup_set = backup_sets[set_id]
    return [os.path.join(backup_folder, file) for file in backup_set["files"]]