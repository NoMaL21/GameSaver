import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog # simpledialog 추가
import os
import json
from datetime import datetime
import re
import threading
import time

from file_manager import (
    backup_save_file, restore_save_file, get_original_filename,
    save_backup_set, get_backup_sets, get_backup_set_files,
    get_backup_folder_path
)
from utils import get_timestamp

CONFIG_FILE = "save_manager_config.json"

class SaveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("게임 세이버")
        self.root.geometry("540x900")
        self.root.resizable(True, True)

        # 스타일 설정 (기존과 동일)
        self.style = ttk.Style()
        self.style.theme_use('clam')
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a86e8"
        self.button_color = "#5c9eff"
        self.root.configure(bg=self.bg_color)
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TButton', background=self.button_color, foreground='white', font=('Arial', 10, 'bold'))
        self.style.configure('TLabel', background=self.bg_color, font=('Arial', 10))
        self.style.configure('Header.TLabel', background=self.bg_color, font=('Arial', 12, 'bold'))

        # 상태 변수
        self.save_folder = ""
        self.save_files = []
        self.backup_folder = ""
        self.backup_sets = {}
        self.config_data = {"active_profile": None, "profiles": {}} # 설정 데이터 전체 저장
        self.active_profile_name = None # 현재 활성화된 프로필 이름
        
        # 자동 새로고침 관련 변수
        self.refresh_thread = None
        self.stop_refresh = False
        self.last_refresh_time = 0
        self.refresh_interval = 20  # 20초마다 새로고침

        self.setup_ui()
        self._load_config() # UI 로드 후 설정 파일 로드

    def _load_config(self):
        """설정 파일에서 프로필 정보를 로드합니다."""
        try:
            if os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded_data = json.load(f)
                    # 기본 구조 유효성 검사
                    if isinstance(loaded_data, dict) and "profiles" in loaded_data:
                         self.config_data = loaded_data
                    else:
                         print(f"경고: '{CONFIG_FILE}' 파일 구조가 예상과 다릅니다. 기본값으로 시작합니다.")
                         self.config_data = {"active_profile": None, "profiles": {}} # 기본 구조로 리셋
            else:
                 # 파일 없으면 기본 구조 사용
                 self.config_data = {"active_profile": None, "profiles": {}}

        except json.JSONDecodeError:
            messagebox.showerror("설정 오류", f"'{CONFIG_FILE}' 파일 형식이 잘못되었습니다. 파일을 확인하거나 삭제 후 다시 시작해주세요.")
            # 오류 시 기본값으로 계속 진행하거나, 프로그램 종료를 고려할 수 있음
            self.config_data = {"active_profile": None, "profiles": {}}
        except Exception as e:
            print(f"설정 로드 중 오류 발생: {e}")
            self.config_data = {"active_profile": None, "profiles": {}}

        # 콤보박스 업데이트
        profile_names = list(self.config_data.get("profiles", {}).keys())
        self.profile_combobox['values'] = profile_names

        # 마지막 활성 프로필 선택 시도
        last_active = self.config_data.get("active_profile")
        if last_active and last_active in profile_names:
            self.profile_combobox.set(last_active)
            self._apply_profile(last_active) # 해당 프로필 경로 적용
            self.active_profile_name = last_active
        elif profile_names: # 활성 프로필이 없지만 프로필 목록이 있으면 첫번째 선택
             first_profile = profile_names[0]
             self.profile_combobox.set(first_profile)
             self._apply_profile(first_profile)
             self.active_profile_name = first_profile
             self.config_data["active_profile"] = first_profile # 활성 프로필 정보 업데이트
             self._save_config() # 변경된 활성 프로필 저장
        else: # 프로필이 아예 없으면 비움
             self._clear_paths_and_ui()

    def _save_config(self):
        """현재 설정(모든 프로필 및 활성 프로필)을 파일에 저장합니다."""
        # 저장 전에 현재 활성 프로필 이름 업데이트
        if self.active_profile_name:
             self.config_data["active_profile"] = self.active_profile_name
        else:
             self.config_data["active_profile"] = None

        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config_data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            print(f"설정 저장 중 오류 발생: {e}")
            messagebox.showwarning("저장 오류", f"설정 저장 중 오류 발생:\n{e}")

    def _apply_profile(self, profile_name):
        """선택된 프로필의 경로를 로드하고 UI에 적용합니다."""
        profile_data = self.config_data.get("profiles", {}).get(profile_name)
        if profile_data:
            loaded_save_folder = profile_data.get("save_folder", "")
            
            # 백업 폴더는 자동으로 생성
            self.backup_folder = get_backup_folder_path(profile_name)
            
            valid_save = os.path.isdir(loaded_save_folder)

            self.save_folder = loaded_save_folder if valid_save else ""

            # UI 업데이트
            self.folder_entry.delete(0, tk.END)
            if self.save_folder:
                self.folder_entry.insert(0, self.save_folder)
                # 자동 새로고침 시작
                self.start_auto_refresh()

            # 폴더 변경 시 관련 데이터 초기화
            self.save_files = []
            self.details_listbox.delete(0, tk.END)
            self.load_backup_sets()

            self.active_profile_name = profile_name
            print(f"프로필 '{profile_name}' 로드 완료.")

        else:
            print(f"오류: 프로필 '{profile_name}' 데이터를 찾을 수 없습니다.")
            self._clear_paths_and_ui()

    def _clear_paths_and_ui(self):
        """경로 변수와 관련 UI를 초기화합니다."""
        # 자동 새로고침 중지
        self.stop_auto_refresh()
        
        self.save_folder = ""
        self.backup_folder = ""
        self.save_files = []
        self.backup_sets = {}
        self.active_profile_name = None

        self.folder_entry.delete(0, tk.END)
        self.file_listbox.delete(0, tk.END)
        self.details_listbox.delete(0, tk.END)
        for item in self.sets_tree.get_children():
            self.sets_tree.delete(item)
        self.profile_combobox.set("") # 콤보박스 선택 해제
        self.status_label.config(text="준비됨")
        self.progress_bar["value"] = 0

    def _on_profile_selected(self, event):
        """콤보박스에서 프로필 선택 시 호출됩니다."""
        selected_profile = self.profile_combobox.get()
        if selected_profile:
            self._apply_profile(selected_profile)
            # 활성 프로필 변경 시 바로 저장
            self._save_config()
            # 파일 목록 새로고침
            self._refresh_file_list()

    def _create_new_profile(self):
        """새 프로필 생성 대화상자를 띄우고 프로필을 추가합니다."""
        new_name = simpledialog.askstring("새 프로필", "새 프로필 이름을 입력하세요:", parent=self.root)

        if not new_name:
            return

        new_name = new_name.strip()
        if not new_name:
            messagebox.showwarning("입력 오류", "프로필 이름은 공백일 수 없습니다.")
            return

        profiles = self.config_data.get("profiles", {})
        if new_name in profiles:
            messagebox.showerror("오류", f"이미 '{new_name}'이라는 프로필이 존재합니다.")
            return

        # 새 프로필 추가 (백업 폴더는 자동 생성되므로 저장하지 않음)
        profiles[new_name] = {"save_folder": ""}
        self.config_data["profiles"] = profiles

        # 콤보박스 업데이트 및 새 프로필 선택
        profile_names = list(profiles.keys())
        self.profile_combobox['values'] = profile_names
        self.profile_combobox.set(new_name)

        # 새 프로필 적용
        self._apply_profile(new_name)
        self._save_config()
        messagebox.showinfo("성공", f"새 프로필 '{new_name}'이(가) 생성되었습니다.\n이제 세이브 폴더를 선택하세요.")


    def _delete_profile(self):
        """현재 선택된 프로필을 삭제합니다."""
        profile_to_delete = self.profile_combobox.get()

        if not profile_to_delete:
            messagebox.showinfo("알림", "삭제할 프로필을 선택해주세요.")
            return

        if messagebox.askyesno("프로필 삭제 확인", f"'{profile_to_delete}' 프로필을 정말 삭제하시겠습니까?", parent=self.root):
            profiles = self.config_data.get("profiles", {})
            if profile_to_delete in profiles:
                del profiles[profile_to_delete] # 프로필 제거
                self.config_data["profiles"] = profiles

                # 활성 프로필이 삭제된 경우
                if self.config_data.get("active_profile") == profile_to_delete:
                     self.config_data["active_profile"] = None
                     self.active_profile_name = None

                # UI 업데이트
                profile_names = list(profiles.keys())
                self.profile_combobox['values'] = profile_names
                self._clear_paths_and_ui() # UI 및 경로 초기화

                # 변경사항 저장
                self._save_config()
                messagebox.showinfo("성공", f"프로필 '{profile_to_delete}'이(가) 삭제되었습니다.")

                # 삭제 후, 남은 프로필이 있다면 첫번째 프로필 로드
                if profile_names:
                     first_profile = profile_names[0]
                     self.profile_combobox.set(first_profile)
                     self._apply_profile(first_profile)
                     # 활성 프로필 정보 업데이트 및 저장
                     self.active_profile_name = first_profile
                     self.config_data["active_profile"] = first_profile
                     self._save_config()

    def setup_ui(self):
        # 메인 컨테이너 (스크롤 가능한 영역)
        container = ttk.Frame(self.root)
        container.pack(fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        canvas = tk.Canvas(container)
        scrollbar = ttk.Scrollbar(container, orient="vertical", command=canvas.yview)
        
        # 스크롤 가능한 프레임
        self.scrollable_frame = ttk.Frame(canvas)
        
        # 마우스 휠 스크롤 지원 - 캔버스에만 적용
        def _on_mousewheel(event):
            # 마우스가 캔버스 위에 있을 때만 스크롤
            if str(event.widget).startswith(str(canvas)):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"  # 이벤트 전파 중지
                
        # 프레임 크기 변경 시 스크롤 영역 업데이트
        def configure_scroll_region(event):
            # 프레임의 전체 높이와 캔버스의 보이는 영역 높이를 비교
            frame_height = self.scrollable_frame.winfo_reqheight()
            canvas_height = canvas.winfo_height()
            
            # 프레임이 캔버스보다 클 때만 스크롤바 표시
            if frame_height > canvas_height:
                canvas.configure(scrollregion=canvas.bbox("all"))
                scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
                # 스크롤바가 표시될 때 마우스 휠 이벤트 바인딩
                canvas.bind_all("<MouseWheel>", _on_mousewheel)
            else:
                scrollbar.pack_forget()
                # 스크롤바가 숨겨질 때 마우스 휠 이벤트 바인딩 해제
                canvas.unbind_all("<MouseWheel>")
                
        self.scrollable_frame.bind("<Configure>", configure_scroll_region)
        
        # 캔버스에 프레임 추가
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 스크롤바와 캔버스 배치
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 창 크기 변경 시 스크롤 영역 업데이트
        def on_window_resize(event):
            configure_scroll_region(None)
        self.root.bind("<Configure>", on_window_resize)
        
        # 메인 프레임
        main_frame = ttk.Frame(self.scrollable_frame, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)

        # 제목
        title_label = ttk.Label(main_frame, text="게임 세이브 파일 관리자", style='Header.TLabel')
        title_label.pack(pady=10)

        # --- 프로필 관리 프레임 ---
        profile_manage_frame = ttk.LabelFrame(main_frame, text="프로필 관리", padding=10)
        profile_manage_frame.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(profile_manage_frame, text="선택:").pack(side=tk.LEFT, padx=(0, 5))
        
        # 프로필 콤보박스
        self.profile_combobox = ttk.Combobox(profile_manage_frame, state="readonly", width=20)
        self.profile_combobox.pack(side=tk.LEFT, padx=5)
        self.profile_combobox.bind('<<ComboboxSelected>>', self._on_profile_selected)

        # 프로필 관리 버튼
        ttk.Button(profile_manage_frame, text="새 프로필", command=self._create_new_profile).pack(side=tk.LEFT, padx=5)
        ttk.Button(profile_manage_frame, text="프로필 삭제", command=self._delete_profile).pack(side=tk.LEFT, padx=5)

        # --- 세이브 폴더 선택 프레임 ---
        folder_frame = ttk.LabelFrame(main_frame, text="세이브 폴더", padding=10)
        folder_frame.pack(fill=tk.X, pady=(0, 10))

        self.folder_entry = ttk.Entry(folder_frame, width=50)
        self.folder_entry.pack(side=tk.LEFT, padx=(0, 5), fill=tk.X, expand=True)
        
        ttk.Button(folder_frame, text="폴더 선택", command=self.select_save_folder).pack(side=tk.LEFT)

        # --- 백업 영역 ---
        self.setup_backup_area(main_frame)

        # --- 복원 영역 ---
        self.setup_restore_area(main_frame)

        # --- 상태 표시줄 ---
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.status_label = ttk.Label(status_frame, text="준비됨")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(status_frame, mode='determinate')
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(10, 0))


    def select_save_folder(self):
        """사용자가 세이브 폴더를 선택하고, 활성 프로필에 저장합니다."""
        # 현재 설정된 경로 또는 사용자 홈 디렉토리에서 시작
        initial_dir = self.save_folder or os.path.expanduser("~")
        folder_selected = filedialog.askdirectory(title="세이브 폴더 선택", initialdir=initial_dir)
        if folder_selected:
            self.save_folder = folder_selected
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)

            # 세이브 폴더 변경 시, 기존 파일 선택 목록 초기화
            self.save_files = []
            self.file_listbox.delete(0, tk.END)

            # 활성 프로필이 있다면 해당 프로필 업데이트 및 저장
            if self.active_profile_name:
                 profile_data = self.config_data.get("profiles", {}).get(self.active_profile_name)
                 if profile_data:
                     profile_data["save_folder"] = self.save_folder
                     self._save_config() # 변경사항 저장
            else:
                 messagebox.showinfo("알림", "현재 선택된 프로필이 없습니다. 폴더 경로는 임시로 사용됩니다.\n프로필을 생성하거나 선택 후 다시 폴더를 선택하면 해당 프로필에 저장됩니다.")

    def deselect_all_files(self):
        """선택된 파일들의 체크박스 해제"""
        for var in self.checkbox_vars.values():
            var.set(False)

    def setup_backup_area(self, parent):
        # 백업 파일 선택 프레임
        files_frame = ttk.LabelFrame(parent, text="백업할 파일 선택", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 체크박스와 파일명을 담을 캔버스와 스크롤바
        canvas = tk.Canvas(files_frame, height=150)
        scrollbar = ttk.Scrollbar(files_frame, orient="vertical", command=canvas.yview)
        
        # 체크박스들을 담을 프레임
        self.checkbox_frame = ttk.Frame(canvas)
        
        # 캔버스 설정
        canvas.configure(yscrollcommand=scrollbar.set)
        
        # 스크롤바와 캔버스 배치
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 체크박스 프레임을 캔버스에 추가
        canvas_frame = canvas.create_window((0, 0), window=self.checkbox_frame, anchor="nw")
        
        # 체크박스 프레임 크기 변경 시 스크롤 영역 업데이트
        def configure_scroll_region(event):
            canvas.configure(scrollregion=canvas.bbox("all"))
        self.checkbox_frame.bind("<Configure>", configure_scroll_region)
        
        # 캔버스 크기 변경 시 내부 프레임 크기 조정
        def configure_canvas(event):
            canvas.itemconfig(canvas_frame, width=event.width)
        canvas.bind("<Configure>", configure_canvas)
        
        # 마우스 휠 스크롤 지원 - 캔버스에만 적용
        def _on_mousewheel(event):
            # 마우스가 캔버스 위에 있을 때만 스크롤
            if str(event.widget).startswith(str(canvas)):
                canvas.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"  # 이벤트 전파 중지
        canvas.bind("<MouseWheel>", _on_mousewheel)
        
        # 체크박스 프레임에도 마우스 휠 이벤트 바인딩
        def _on_checkbox_frame_mousewheel(event):
            canvas.yview_scroll(int(-1*(event.delta/120)), "units")
            return "break"  # 이벤트 전파 중지
        self.checkbox_frame.bind("<MouseWheel>", _on_checkbox_frame_mousewheel)

        # 체크박스 변수들을 저장할 딕셔너리
        self.checkbox_vars = {}

        # 백업 설명 입력 프레임
        desc_frame = ttk.Frame(parent)
        desc_frame.pack(fill=tk.X, pady=5)

        ttk.Label(desc_frame, text="백업 설명:").pack(side=tk.LEFT, padx=(0, 5))
        self.desc_entry = ttk.Entry(desc_frame)
        self.desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 수동 새로고침 버튼
        refresh_btn = ttk.Button(desc_frame, text="새로고침", command=self._refresh_file_list, width=8)
        refresh_btn.pack(side=tk.RIGHT, padx=5)

        # 버튼 프레임 생성
        self.button_frame = ttk.Frame(parent)
        self.button_frame.pack(side=tk.BOTTOM, pady=5)

        # 백업 버튼
        backup_btn = ttk.Button(self.button_frame, text="선택한 파일 백업하기", command=self.backup_files, width=25)
        backup_btn.pack(side=tk.LEFT, padx=5)

    def setup_restore_area(self, parent):
        # 백업 세트 선택 프레임
        sets_frame = ttk.LabelFrame(parent, text="복원할 백업 세트 선택", padding=10)
        sets_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # 백업 세트 목록을 보여줄 트리뷰
        self.sets_tree = ttk.Treeview(sets_frame, columns=("date", "description", "files"), show="headings", height=6)
        self.sets_tree.heading("date", text="날짜")
        self.sets_tree.heading("description", text="설명")
        self.sets_tree.heading("files", text="파일 수")

        # 열 너비 설정
        self.sets_tree.column("date", width=120, anchor=tk.W)
        self.sets_tree.column("description", width=200, anchor=tk.W)
        self.sets_tree.column("files", width=60, anchor=tk.CENTER)

        self.sets_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 스크롤바 추가
        sets_scrollbar = ttk.Scrollbar(sets_frame, orient="vertical", command=self.sets_tree.yview)
        sets_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sets_tree.config(yscrollcommand=sets_scrollbar.set)

        # 마우스 휠 스크롤 지원 - 트리뷰에만 적용
        def _on_tree_mousewheel(event):
            # 마우스가 트리뷰 위에 있을 때만 스크롤
            if str(event.widget).startswith(str(self.sets_tree)):
                self.sets_tree.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"  # 이벤트 전파 중지
        self.sets_tree.bind("<MouseWheel>", _on_tree_mousewheel)

        # 백업 세트 상세 정보 프레임
        details_frame = ttk.LabelFrame(parent, text="선택한 백업 세트의 파일 목록", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        self.details_listbox = tk.Listbox(details_frame, height=4)
        self.details_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # 스크롤바 추가
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_listbox.yview)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_listbox.config(yscrollcommand=details_scrollbar.set)

        # 마우스 휠 스크롤 지원 - 리스트박스에만 적용
        def _on_listbox_mousewheel(event):
            # 마우스가 리스트박스 위에 있을 때만 스크롤
            if str(event.widget).startswith(str(self.details_listbox)):
                self.details_listbox.yview_scroll(int(-1*(event.delta/120)), "units")
                return "break"  # 이벤트 전파 중지
        self.details_listbox.bind("<MouseWheel>", _on_listbox_mousewheel)

        # 이벤트 연결
        self.sets_tree.bind("<<TreeviewSelect>>", self.on_backup_set_selected)

        # 복원 버튼
        restore_btn = ttk.Button(self.button_frame, text="복원하기", command=self.restore_backup_set, width=15)
        restore_btn.pack(side=tk.LEFT, padx=5)


    def select_save_files(self):
        """사용자가 여러 개의 세이브 파일을 선택"""
        if not self.save_folder:
            messagebox.showerror("오류", "먼저 세이브 폴더를 선택해주세요.")
            return
        # 선택된 폴더가 유효한지 한번 더 확인
        if not os.path.isdir(self.save_folder):
            messagebox.showerror("오류", f"세이브 폴더 경로가 유효하지 않습니다:\n{self.save_folder}")
            return

        files_selected = filedialog.askopenfilenames(
            title="세이브 파일 선택 (여러 개 가능)",
            initialdir=self.save_folder,
            filetypes=[("모든 파일", "*.*")]
        )

        if files_selected:
            new_files = list(files_selected)
            # 기존 목록과 합치되, 중복은 제거
            existing_files_set = set(self.save_files)
            added_count = 0
            for f in new_files:
                if f not in existing_files_set:
                    # 선택한 파일이 실제로 save_folder 내에 있는지 확인 (선택사항)
                    # if os.path.dirname(f) == self.save_folder:
                    self.save_files.append(f)
                    existing_files_set.add(f)
                    added_count += 1
                    # else:
                    #    print(f"경고: 선택한 파일 '{os.path.basename(f)}'은(는) 현재 세이브 폴더 밖에 있어 제외됩니다.")

            if added_count > 0:
                # 리스트박스 갱신 (전체 목록으로 다시 그림)
                self.file_listbox.delete(0, tk.END)
                for file in self.save_files:
                     # 파일이 실제로 존재하는지 한번 더 확인하고 추가 (선택사항)
                     # if os.path.exists(file):
                     self.file_listbox.insert(tk.END, os.path.basename(file))


    def load_backup_sets(self):
        """백업 폴더에서 백업 세트 정보 로드"""
        # 트리뷰 초기화 (먼저 수행)
        for item in self.sets_tree.get_children():
            self.sets_tree.delete(item)
        self.backup_sets = {} # 내부 데이터도 초기화
        self.details_listbox.delete(0, tk.END) # 상세 목록도 초기화

        # 백업 폴더 경로 유효성 검사
        if not self.backup_folder or not os.path.isdir(self.backup_folder):
            self.status_label.config(text="백업 폴더가 유효하지 않습니다.")
            return

        # 백업 세트 정보 로드
        try:
            self.backup_sets = get_backup_sets(self.backup_folder)
        except Exception as e: # JSON 로딩 오류 등 처리
            messagebox.showerror("로드 오류", f"백업 세트 정보를 불러오는 중 오류 발생:\n{e}\n'{os.path.join(self.backup_folder, 'backup_sets.json')}' 파일을 확인하세요.")
            self.backup_sets = {}
            self.status_label.config(text="백업 세트 로드 오류")
            return # 오류 발생 시 더 이상 진행하지 않음

        # 트리뷰에 백업 세트 정보 추가 (최신순 정렬)
        if isinstance(self.backup_sets, dict):
            set_ids_sorted = sorted(self.backup_sets.keys(), reverse=True)
            if not set_ids_sorted:
                 self.status_label.config(text="백업 세트가 없습니다.")

            loaded_count = 0
            for set_id in set_ids_sorted:
                backup_set = self.backup_sets[set_id]
                # backup_set 데이터 유효성 검사 강화
                if isinstance(backup_set, dict) and all(k in backup_set for k in ["id", "date", "description", "files"]) and isinstance(backup_set["files"], list):
                    try:
                        file_count = len(backup_set["files"])
                        self.sets_tree.insert(
                            "", "end",
                            iid=set_id, # iid는 고유해야 함 (set_id 사용)
                            values=(
                                backup_set["date"],
                                backup_set["description"],
                                file_count # 파일 개수 표시
                            )
                        )
                        loaded_count += 1
                    except Exception as insert_error:
                         print(f"Treeview 삽입 오류 (set_id: {set_id}): {insert_error}")
                else:
                    print(f"경고: 잘못된 백업 세트 데이터 (set_id: {set_id}) - 건너뜀: {backup_set}")
            if loaded_count > 0:
                 self.status_label.config(text=f"{loaded_count}개의 백업 세트 로드됨")

        else:
             messagebox.showerror("로드 오류", f"백업 세트 데이터 형식이 잘못되었습니다 (딕셔너리가 아님). '{os.path.join(self.backup_folder, 'backup_sets.json')}' 파일을 확인하세요.")
             self.backup_sets = {}
             self.status_label.config(text="백업 세트 데이터 형식 오류")


    def on_backup_set_selected(self, event):
        """백업 세트 선택 시 상세 정보 표시"""
        selected_items = self.sets_tree.selection()
        # 상세 정보 리스트박스 초기화 (선택/해제 시 항상)
        self.details_listbox.delete(0, tk.END)

        if not selected_items:
            return # 선택된 항목 없으면 여기서 종료

        set_id = selected_items[0] # 첫 번째 선택된 항목 ID 가져오기

        # 선택된 백업 세트의 파일 목록 표시
        if isinstance(self.backup_sets, dict) and set_id in self.backup_sets:
            backup_set_data = self.backup_sets[set_id]
            if isinstance(backup_set_data, dict) and "files" in backup_set_data and isinstance(backup_set_data["files"], list):
                # 파일 목록이 비어있지 않은 경우에만 표시
                if backup_set_data["files"]:
                    for file in backup_set_data["files"]:
                         self.details_listbox.insert(tk.END, file)
                # else: # 비어있는 경우 메시지 표시 (선택사항)
                #    self.details_listbox.insert(tk.END, "(이 세트에는 파일이 없습니다)")
            else:
                 print(f"경고: 선택된 백업 세트의 파일 목록 형식이 잘못되었습니다 (set_id: {set_id})")
                 self.details_listbox.insert(tk.END, "(파일 목록 로드 오류)")


    def update_progress(self, current, total):
        """진행 상태 업데이트"""
        if total > 0: # 0으로 나누기 방지
             progress = int((current / total) * 100)
             self.progress_bar["value"] = progress
             self.status_label.config(text=f"진행 중... {progress}% ({current}/{total})")
        else:
             self.progress_bar["value"] = 0
             self.status_label.config(text="대기 중...")
        self.root.update_idletasks()


    def backup_files(self):
        """선택한 세이브 파일들을 백업"""
        # 활성 프로필 & 폴더 유효성 검사
        if not self.active_profile_name:
             messagebox.showwarning("프로필 필요", "백업을 진행하려면 먼저 프로필을 선택하거나 생성해주세요.")
             return
        if not self.save_folder or not os.path.isdir(self.save_folder):
             messagebox.showerror("오류", "세이브 폴더 경로가 유효하지 않습니다.")
             return
        if not self.backup_folder or not os.path.isdir(self.backup_folder):
            messagebox.showerror("오류", "백업 폴더 경로가 유효하지 않습니다.")
            return

        # 선택된 파일들 가져오기
        selected_files = []
        for filename, var in self.checkbox_vars.items():
            if var.get():
                file_path = os.path.join(self.save_folder, filename)
                if os.path.isfile(file_path):
                    selected_files.append(file_path)

        if not selected_files:
            messagebox.showwarning("파일 선택 필요", "백업할 파일을 선택해주세요.")
            return

        try:
            self.progress_bar["value"] = 0
            self.status_label.config(text="백업 준비 중...")
            self.root.update_idletasks()

            # 새 백업 세트를 위한 타임스탬프 생성
            timestamp = get_timestamp()
            backup_paths = []  # 실제 백업된 파일의 전체 경로 저장
            error_files = []

            total_files = len(selected_files)
            for idx, file_path in enumerate(selected_files, 1):
                self.update_progress(idx, total_files)
                try:
                    # 모든 파일에 동일한 타임스탬프 적용
                    backup_path = backup_save_file(file_path, self.backup_folder, timestamp)
                    backup_paths.append(backup_path)  # 성공한 경로만 추가
                except FileNotFoundError:
                    error_msg = f"파일 없음: {os.path.basename(file_path)}"
                    print(f"경고: {error_msg}")
                    error_files.append(error_msg)
                except PermissionError:
                     error_msg = f"권한 오류: {os.path.basename(file_path)}"
                     print(f"경고: {error_msg}")
                     error_files.append(error_msg)
                except Exception as backup_err:
                    error_msg = f"{os.path.basename(file_path)}: {backup_err}"
                    print(f"오류: '{os.path.basename(file_path)}' 백업 중 오류 발생 - {backup_err}")
                    error_files.append(error_msg)

            # 실제로 백업된 파일이 있을 경우에만 세트 정보 저장
            if not backup_paths:
                 message = "선택된 파일을 백업하지 못했습니다."
                 if error_files:
                      message += "\n\n오류 목록:\n" + "\n".join(error_files)
                 messagebox.showwarning("백업 실패", message)
                 self.status_label.config(text="백업 실패")
                 return

            # 백업 세트 설명 가져오기
            description = self.desc_entry.get().strip()
            if not description:  # 기본 설명 생성
                try:
                    current_time_obj = datetime.strptime(timestamp, "%y%m%d_%H%M%S")
                    current_time_str = current_time_obj.strftime("%Y-%m-%d %H:%M:%S")
                    description = f"백업 ({current_time_str})"
                except ValueError:
                    description = f"백업 ({timestamp})"

            # 백업 세트 정보 저장
            save_backup_set(self.backup_folder, timestamp, backup_paths, description)

            # 백업 세트 목록 갱신
            self.load_backup_sets()

            self.status_label.config(text="백업 완료")
            success_message = f"{len(backup_paths)}개의 파일이 '{description}' 백업 세트에 저장되었습니다."
            if error_files:
                 success_message += f"\n\n{len(error_files)}개 파일 백업 실패/건너뜀."
                 print("백업 실패/건너뜀 상세:", error_files)
                 messagebox.showwarning("백업 완료 (일부 오류)", success_message)
            else:
                 messagebox.showinfo("성공", success_message)

        except Exception as e:
            self.status_label.config(text="백업 중 오류 발생")
            messagebox.showerror("오류", f"백업 작업 중 예상치 못한 오류 발생:\n{e}")


    def restore_backup_set(self):
        """선택한 백업 세트의 모든 파일 복원"""
         # 활성 프로필 & 폴더 유효성 검사
        if not self.active_profile_name:
             messagebox.showwarning("프로필 필요", "복원을 진행하려면 먼저 프로필을 선택하거나 생성해주세요.")
             return
        if not self.save_folder or not os.path.isdir(self.save_folder):
             messagebox.showerror("오류", "세이브 폴더 경로가 유효하지 않습니다.\n현재 프로필의 세이브 폴더 설정을 확인하세요.")
             return
        if not self.backup_folder or not os.path.isdir(self.backup_folder):
            messagebox.showerror("오류", "백업 폴더 경로가 유효하지 않습니다.\n현재 프로필의 백업 폴더 설정을 확인하세요.")
            return

        # 복원할 세트 선택 확인
        selected_items = self.sets_tree.selection()
        if not selected_items:
            messagebox.showinfo("알림", "복원할 백업 세트를 목록에서 선택해주세요.")
            return

        set_id = selected_items[0]

        # backup_sets 데이터 유효성 확인
        if not isinstance(self.backup_sets, dict) or set_id not in self.backup_sets:
             messagebox.showerror("오류", "선택한 백업 세트 정보를 찾을 수 없습니다. 목록을 새로고침하거나 백업 데이터를 확인하세요.")
             return

        backup_set = self.backup_sets.get(set_id)

        # backup_set 데이터 구조 유효성 검사
        if not isinstance(backup_set, dict) or not all(k in backup_set for k in ["description", "files"]) or not isinstance(backup_set["files"], list):
             messagebox.showerror("오류", "백업 세트 데이터 형식이 잘못되었습니다.\n'backup_sets.json' 파일을 확인하세요.")
             return

        # 복원할 파일 목록 확인
        files_in_set = backup_set['files']
        if not files_in_set:
             messagebox.showinfo("알림", "선택한 백업 세트에는 복원할 파일이 없습니다.")
             return

        # 복원 확인
        file_count = len(files_in_set)
        confirm = messagebox.askyesno(
            "복원 확인",
            f"'{backup_set['description']}' 백업 세트의 {file_count}개 파일을 복원하시겠습니까?\n\n"
            f"대상 폴더:\n{self.save_folder}\n\n"
            "주의: 대상 폴더에 같은 이름의 파일이 있다면 덮어씁니다!",
            icon='warning', # 경고 아이콘 추가
            parent=self.root
        )

        if not confirm:
            return

        try:
            self.progress_bar["value"] = 0
            self.status_label.config(text="복원 준비 중...")
            self.root.update_idletasks()

            # 백업 세트에 속한 파일 경로 가져오기
            backup_files_paths = get_backup_set_files(self.backup_folder, set_id)

            total_files = len(backup_files_paths)
            restored_count = 0
            skipped_count = 0
            error_details = [] # 오류 상세 정보 저장

            for idx, backup_file_path in enumerate(backup_files_paths, 1):
                self.update_progress(idx, total_files)
                backup_file_name = os.path.basename(backup_file_path) # 오류 보고용

                if not isinstance(backup_file_path, str) or not backup_file_path:
                     msg = f"잘못된 경로 데이터: {backup_file_path}"
                     print(f"경고: {msg}")
                     error_details.append(msg)
                     skipped_count += 1
                     continue

                if os.path.exists(backup_file_path):
                    try:
                        original_file_name = get_original_filename(backup_file_name)
                        if not original_file_name:
                            msg = f"{backup_file_name}: 원본 파일명 추출 불가"
                            print(f"경고: {msg}")
                            error_details.append(msg)
                            skipped_count += 1
                            continue

                        # 대상 경로 생성
                        destination_path = os.path.join(self.save_folder, original_file_name)

                        # (선택사항) 대상 파일이 이미 존재하고, 백업 파일과 동일한 경우 건너뛰기
                        # if os.path.exists(destination_path) and filecmp.cmp(backup_file_path, destination_path, shallow=False):
                        #     restored_count += 1 # 동일해도 복원된 것으로 간주하거나, 별도 카운트
                        #     continue

                        # 파일 복원
                        restore_save_file(backup_file_path, self.save_folder, original_file_name)
                        restored_count += 1

                    except FileNotFoundError:
                         msg = f"{backup_file_name}: 복원 중 파일 없음"
                         print(f"경고: {msg}")
                         error_details.append(msg)
                         skipped_count += 1
                    except PermissionError:
                         msg = f"{backup_file_name}: 대상 폴더 쓰기 권한 없음"
                         print(f"오류: {msg}")
                         error_details.append(msg)
                         skipped_count += 1
                    except Exception as restore_err:
                         msg = f"{backup_file_name}: {restore_err}"
                         print(f"오류: '{backup_file_name}' 복원 중 오류 발생 - {restore_err}")
                         error_details.append(msg)
                         skipped_count += 1
                else:
                    msg = f"{backup_file_name}: 백업 파일 없음"
                    print(f"경고: {msg}")
                    error_details.append(msg)
                    skipped_count += 1


            # 복원 결과 요약
            result_title = "복원 완료"
            result_message = f"{restored_count}개의 파일이 성공적으로 복원되었습니다."
            if skipped_count > 0:
                result_title += " (일부 실패/건너뜀)"
                result_message += f"\n{skipped_count}개의 파일 복원에 실패했거나 건너뛰었습니다."
                print("\n--- 복원 실패/건너뜀 상세 ---")
                for detail in error_details:
                    print(f"- {detail}")
                print("----------------------------\n")
                # 사용자에게도 간략히 알림
                messagebox.showwarning(result_title, result_message + "\n\n자세한 내용은 콘솔 로그를 확인하세요.", parent=self.root)
            else:
                 messagebox.showinfo(result_title, result_message, parent=self.root)

            self.status_label.config(text=result_title)

        except Exception as e:
            self.status_label.config(text="복원 중 오류 발생")
            messagebox.showerror("치명적 오류", f"복원 작업 중 예상치 못한 오류 발생:\n{e}", parent=self.root)

    def start_auto_refresh(self):
        """파일 목록 자동 새로고침 시작"""
        if self.refresh_thread is None or not self.refresh_thread.is_alive():
            self.stop_refresh = False
            self.refresh_thread = threading.Thread(target=self._auto_refresh_loop)
            self.refresh_thread.daemon = True
            self.refresh_thread.start()

    def stop_auto_refresh(self):
        """파일 목록 자동 새로고침 중지"""
        self.stop_refresh = True
        if self.refresh_thread:
            self.refresh_thread.join(timeout=1.0)

    def _auto_refresh_loop(self):
        """파일 목록 자동 새로고침 루프"""
        while not self.stop_refresh:
            current_time = time.time()
            if current_time - self.last_refresh_time >= self.refresh_interval:
                if self.save_folder and os.path.isdir(self.save_folder):
                    self.root.after(0, self._refresh_file_list)
                self.last_refresh_time = current_time
            time.sleep(1)

    def _refresh_file_list(self):
        """파일 목록 새로고침"""
        if not self.save_folder or not os.path.isdir(self.save_folder):
            return

        try:
            # 현재 선택된 파일들 저장
            selected_files = [filename for filename, var in self.checkbox_vars.items() if var.get()]

            # 기존 체크박스들 제거
            for widget in self.checkbox_frame.winfo_children():
                widget.destroy()
            self.checkbox_vars.clear()
            self.save_files = []

            # 새로운 파일 목록 추가
            for file in os.listdir(self.save_folder):
                if os.path.isfile(os.path.join(self.save_folder, file)):
                    self.save_files.append(os.path.join(self.save_folder, file))
                    
                    # 체크박스 변수 생성
                    var = tk.BooleanVar(value=file in selected_files)
                    self.checkbox_vars[file] = var
                    
                    # 체크박스와 파일명을 담을 프레임
                    file_frame = ttk.Frame(self.checkbox_frame)
                    file_frame.pack(fill=tk.X, padx=5, pady=2)
                    
                    # 체크박스 생성
                    checkbox = ttk.Checkbutton(
                        file_frame, 
                        text=file,
                        variable=var,
                        style='TCheckbutton'
                    )
                    checkbox.pack(side=tk.LEFT, anchor=tk.W)
                    
                    # 체크박스 프레임에도 마우스 휠 이벤트 바인딩
                    def _on_checkbox_mousewheel(event):
                        self.checkbox_frame.event_generate("<MouseWheel>", delta=event.delta)
                        return "break"  # 이벤트 전파 중지
                    file_frame.bind("<MouseWheel>", _on_checkbox_mousewheel)
                    checkbox.bind("<MouseWheel>", _on_checkbox_mousewheel)

        except Exception as e:
            print(f"파일 목록 새로고침 중 오류 발생: {e}")

