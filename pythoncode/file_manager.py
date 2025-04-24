import os
import shutil
import re
import json
from datetime import datetime
from utils import get_timestamp
import sys
import time

def get_backup_folder_path(profile_name):
    """
    프로필 이름을 기반으로 백업 폴더 경로를 생성합니다.
    프로그램 실행 디렉토리 아래에 'backups' 폴더를 만들고,
    그 안에 프로필별 폴더를 생성합니다.
    """
    # 프로그램 실행 디렉토리 경로 가져오기
    if getattr(sys, 'frozen', False):
        # PyInstaller로 생성된 exe 파일인 경우
        base_dir = os.path.dirname(sys.executable)
    else:
        # 일반 Python 스크립트로 실행된 경우
        base_dir = os.path.dirname(os.path.abspath(__file__))
    
    # backups 폴더 경로 생성
    backups_dir = os.path.join(base_dir, 'backups')
    
    # 프로필별 폴더 경로 생성
    profile_backup_dir = os.path.join(backups_dir, profile_name)
    
    # 폴더가 없으면 생성
    if not os.path.exists(profile_backup_dir):
        os.makedirs(profile_backup_dir)
    
    return profile_backup_dir

def backup_save_file(file_path, backup_folder, timestamp):
    """
    세이브 파일을 백업 폴더에 복사합니다.
    
    Args:
        file_path (str): 백업할 파일의 전체 경로
        backup_folder (str): 백업 폴더의 전체 경로
        timestamp (str): 백업 세트의 타임스탬프
        
    Returns:
        str: 백업된 파일의 전체 경로
    """
    try:
        # 원본 파일명과 확장자 분리
        original_filename = os.path.basename(file_path)
        name, ext = os.path.splitext(original_filename)
        
        # 백업 파일명 생성 (파일명_타임스탬프.확장자)
        backup_filename = f"{name}_{timestamp}{ext}"
        
        # 백업 파일의 전체 경로
        backup_path = os.path.join(backup_folder, backup_filename)
        
        # 파일 복사
        shutil.copy2(file_path, backup_path)
        
        # 생성 시간을 현재 시간으로 설정
        current_time = time.time()
        os.utime(backup_path, (current_time, current_time))
        
        return backup_path
        
    except Exception as e:
        raise Exception(f"파일 백업 중 오류 발생: {str(e)}")

def get_original_filename(backup_file_name):
    """
    백업 파일명에서 타임스탬프 (YYMMDD_HHMMSS)를 제거하여 원본 파일명을 반환합니다.
    예: "save_250401_152655.sav" -> "save.sav"
    """
    # 타임스탬프 패턴: _YYMMDD_HHMMSS
    return re.sub(r'_\d{6}_\d{6}', '', backup_file_name)

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
        name, ext = os.path.splitext(backup_file_name)
        # 타임스탬프 부분을 제거하여 원본 파일명 추출
        original_file_name = name.rsplit('_', 1)[0] + ext
    
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
    formatted_date = datetime.strptime(set_id, "%y%m%d_%H%M%S").strftime("%Y-%m-%d %H:%M:%S")
    
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