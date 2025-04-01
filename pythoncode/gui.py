import tkinter as tk
from tkinter import filedialog, messagebox, ttk, simpledialog
import os
from datetime import datetime  # 이 부분 추가
import re
from file_manager import (
    backup_save_file, restore_save_file, get_original_filename,
    save_backup_set, get_backup_sets, get_backup_set_files
)
from utils import get_timestamp

class SaveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("세이브 파일 관리자")
        self.root.geometry("800x1000")
        self.root.resizable(True, True)
        
        # 스타일 설정
        self.style = ttk.Style()
        self.style.theme_use('clam')  # 'clam', 'alt', 'default', 'classic' 등 가능
        
        # 색상 테마 정의
        self.bg_color = "#f0f0f0"
        self.accent_color = "#4a86e8"
        self.button_color = "#5c9eff"
        self.root.configure(bg=self.bg_color)
        
        # 스타일 설정
        self.style.configure('TFrame', background=self.bg_color)
        self.style.configure('TButton', background=self.button_color, foreground='white', font=('Arial', 10, 'bold'))
        self.style.configure('TLabel', background=self.bg_color, font=('Arial', 10))
        self.style.configure('Header.TLabel', background=self.bg_color, font=('Arial', 12, 'bold'))
        
        # 기본값 설정
        self.save_folder = ""
        self.save_files = []  # 여러 개 선택 가능
        self.backup_folder = ""
        self.backup_sets = {}  # 백업 세트 정보

        self.setup_ui()

    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="게임 세이브 파일 관리자", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # 상단 프레임 (폴더 선택 영역)
        top_frame = ttk.Frame(main_frame)
        top_frame.pack(fill=tk.X, pady=10)
        
        # 왼쪽 프레임 (세이브/백업 폴더 선택)
        left_frame = ttk.Frame(top_frame)
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 세이브 폴더 선택 프레임
        folder_frame = ttk.LabelFrame(left_frame, text="세이브 폴더 선택", padding=10)
        folder_frame.pack(fill=tk.X, pady=5)
        
        folder_frame_inner = ttk.Frame(folder_frame)
        folder_frame_inner.pack(fill=tk.X)
        
        self.folder_entry = ttk.Entry(folder_frame_inner, width=40)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        folder_button = ttk.Button(folder_frame_inner, text="폴더 선택", command=self.select_save_folder)
        folder_button.pack(side=tk.RIGHT)
        
        # 백업 폴더 선택 프레임
        backup_frame = ttk.LabelFrame(left_frame, text="백업 폴더 선택", padding=10)
        backup_frame.pack(fill=tk.X, pady=5)
        
        backup_frame_inner = ttk.Frame(backup_frame)
        backup_frame_inner.pack(fill=tk.X)
        
        self.backup_entry = ttk.Entry(backup_frame_inner, width=40)
        self.backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        backup_folder_button = ttk.Button(backup_frame_inner, text="폴더 선택", command=self.select_backup_folder)
        backup_folder_button.pack(side=tk.RIGHT)
        
        # 중앙 영역 - 노트북(탭) 생성
        self.notebook = ttk.Notebook(main_frame)
        self.notebook.pack(fill=tk.BOTH, expand=True, pady=10)
        
        # 백업 탭
        backup_tab = ttk.Frame(self.notebook)
        self.notebook.add(backup_tab, text="백업")
        
        # 복원 탭
        restore_tab = ttk.Frame(self.notebook)
        self.notebook.add(restore_tab, text="복원")
        
        # 백업 탭 내용
        self.setup_backup_tab(backup_tab)
        
        # 복원 탭 내용
        self.setup_restore_tab(restore_tab)
        
        # 작업 상태 프레임
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="준비됨")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True)

    def setup_backup_tab(self, parent):
        # 세이브 파일 선택 프레임
        files_frame = ttk.LabelFrame(parent, text="세이브 파일 선택", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        files_button = ttk.Button(files_frame, text="파일 선택", command=self.select_save_files)
        files_button.pack(side=tk.TOP, anchor=tk.W)
        
        # 파일 목록을 보여줄 리스트박스
        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=10)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        file_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)
        
        # 선택 파일 제거 버튼
        remove_button = ttk.Button(files_frame, text="선택 파일 제거", command=self.remove_selected_files)
        remove_button.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        
        # 백업 설명 입력 프레임
        desc_frame = ttk.Frame(parent)
        desc_frame.pack(fill=tk.X, pady=5)
        
        ttk.Label(desc_frame, text="백업 설명:").pack(side=tk.LEFT, padx=(0, 5))
        self.desc_entry = ttk.Entry(desc_frame)
        self.desc_entry.pack(side=tk.LEFT, fill=tk.X, expand=True)
        
        # 백업 버튼
        backup_btn = ttk.Button(parent, text="백업하기", command=self.backup_files, width=15)
        backup_btn.pack(side=tk.BOTTOM, pady=10)

    def setup_restore_tab(self, parent):
        # 백업 세트 선택 프레임
        sets_frame = ttk.LabelFrame(parent, text="백업 세트 선택", padding=10)
        sets_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        # 백업 세트 목록을 보여줄 트리뷰
        self.sets_tree = ttk.Treeview(sets_frame, columns=("date", "description", "files"), show="headings")
        self.sets_tree.heading("date", text="날짜")
        self.sets_tree.heading("description", text="설명")
        self.sets_tree.heading("files", text="파일 수")
        
        # 열 너비 설정
        self.sets_tree.column("date", width=150)
        self.sets_tree.column("description", width=300)
        self.sets_tree.column("files", width=100)
        
        self.sets_tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        sets_scrollbar = ttk.Scrollbar(sets_frame, orient="vertical", command=self.sets_tree.yview)
        sets_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.sets_tree.config(yscrollcommand=sets_scrollbar.set)
        
        # 백업 세트 상세 정보 프레임
        details_frame = ttk.LabelFrame(parent, text="세트 상세 정보", padding=10)
        details_frame.pack(fill=tk.BOTH, expand=True, pady=5)
        
        self.details_listbox = tk.Listbox(details_frame, height=6)
        self.details_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        details_scrollbar = ttk.Scrollbar(details_frame, orient="vertical", command=self.details_listbox.yview)
        details_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.details_listbox.config(yscrollcommand=details_scrollbar.set)
        
        # 이벤트 연결
        self.sets_tree.bind("<<TreeviewSelect>>", self.on_backup_set_selected)
        
        # 복원 버튼
        restore_btn = ttk.Button(parent, text="복원하기", command=self.restore_backup_set, width=15)
        restore_btn.pack(side=tk.BOTTOM, pady=10)

    def select_save_folder(self):
        """사용자가 세이브 파일이 있는 폴더를 선택"""
        folder_selected = filedialog.askdirectory(title="세이브 폴더 선택")
        if folder_selected:
            self.save_folder = folder_selected
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)
    
    def remove_selected_files(self):
        """선택한 파일을 리스트에서 제거"""
        selected_indices = self.file_listbox.curselection()
        if not selected_indices:
            return
            
        # 역순으로 삭제 (인덱스가 변경되는 것을 방지)
        for i in sorted(selected_indices, reverse=True):
            self.file_listbox.delete(i)
            if i < len(self.save_files):
                self.save_files.pop(i)

    def select_save_files(self):
        """사용자가 여러 개의 세이브 파일을 선택"""
        if not self.save_folder:
            messagebox.showerror("오류", "먼저 세이브 폴더를 선택해주세요.")
            return
        
        files_selected = filedialog.askopenfilenames(
            title="세이브 파일 선택 (여러 개 가능)",
            initialdir=self.save_folder,
            filetypes=[("모든 파일", "*.*")]
        )

        if files_selected:
            self.save_files.extend(list(files_selected))
            # 중복 제거
            self.save_files = list(dict.fromkeys(self.save_files))
            
            # 리스트박스 갱신
            self.file_listbox.delete(0, tk.END)
            for file in self.save_files:
                self.file_listbox.insert(tk.END, os.path.basename(file))

    def select_backup_folder(self):
        """사용자가 백업을 저장할 폴더를 선택"""
        folder_selected = filedialog.askdirectory(title="백업 폴더 선택")
        if folder_selected:
            self.backup_folder = folder_selected
            self.backup_entry.delete(0, tk.END)
            self.backup_entry.insert(0, folder_selected)
            # 백업 폴더 선택 시 백업 세트 정보 로드
            self.load_backup_sets()

    def load_backup_sets(self):
        """백업 폴더에서 백업 세트 정보 로드"""
        if not self.backup_folder or not os.path.exists(self.backup_folder):
            return
            
        # 트리뷰 초기화
        for item in self.sets_tree.get_children():
            self.sets_tree.delete(item)
            
        # 백업 세트 정보 로드
        self.backup_sets = get_backup_sets(self.backup_folder)
        
        # 트리뷰에 백업 세트 정보 추가 (최신순 정렬)
        for set_id in sorted(self.backup_sets.keys(), reverse=True):
            backup_set = self.backup_sets[set_id]
            self.sets_tree.insert(
                "", "end", 
                iid=set_id,
                values=(
                    backup_set["date"], 
                    backup_set["description"], 
                    len(backup_set["files"])
                )
            )

    def on_backup_set_selected(self, event):
        """백업 세트 선택 시 상세 정보 표시"""
        selected_items = self.sets_tree.selection()
        if not selected_items:
            return
            
        set_id = selected_items[0]
        
        # 상세 정보 리스트박스 초기화
        self.details_listbox.delete(0, tk.END)
        
        # 선택된 백업 세트의 파일 목록 표시
        if set_id in self.backup_sets:
            for file in self.backup_sets[set_id]["files"]:
                self.details_listbox.insert(tk.END, file)

    def update_progress(self, current, total):
        """진행 상태 업데이트"""
        progress = int((current / total) * 100)
        self.progress_bar["value"] = progress
        self.status_label.config(text=f"진행 중... {progress}%")
        self.root.update_idletasks()

    def backup_files(self):
        """선택한 모든 세이브 파일을 백업"""
        if not self.save_files or not self.backup_folder:
            messagebox.showerror("오류", "세이브 파일과 백업 폴더를 선택해주세요.")
            return

        try:
            self.progress_bar["value"] = 0
            self.status_label.config(text="백업 준비 중...")
            self.root.update_idletasks()
            
            # 새 백업 세트를 위한 타임스탬프 생성
            timestamp = get_timestamp()
            backup_files = []
            
            total_files = len(self.save_files)
            for idx, file in enumerate(self.save_files, 1):
                self.update_progress(idx, total_files)
                # 모든 파일에 동일한 타임스탬프 적용
                backup_path = backup_save_file(file, self.backup_folder, timestamp)
                backup_files.append(backup_path)
            
            # 백업 세트 설명 가져오기
            description = self.desc_entry.get()
            if not description:
                current_time = datetime.strptime(timestamp, "%y%m%d_%H%M").strftime("%Y-%m-%d %H:%M")
                description = f"백업 ({current_time})"
            
            # 백업 세트 정보 저장
            save_backup_set(self.backup_folder, timestamp, backup_files, description)
            
            # 백업 세트 목록 갱신
            self.load_backup_sets()
            
            self.status_label.config(text="백업 완료")
            messagebox.showinfo("성공", f"{total_files}개의 파일이 '{description}' 백업 세트에 저장되었습니다.")
            
            # 백업 완료 후 설명만 초기화
            self.desc_entry.delete(0, tk.END)
            
        except Exception as e:
            self.status_label.config(text="오류 발생")
            messagebox.showerror("오류", str(e))
    
    def restore_backup_set(self):
        """선택한 백업 세트의 모든 파일 복원"""
        selected_items = self.sets_tree.selection()
        if not selected_items:
            messagebox.showinfo("알림", "복원할 백업 세트를 선택해주세요.")
            return
            
        if not self.save_folder:
            messagebox.showerror("오류", "세이브 폴더를 먼저 선택해주세요.")
            return
            
        set_id = selected_items[0]
        backup_set = self.backup_sets.get(set_id)
        
        if not backup_set:
            messagebox.showerror("오류", "선택한 백업 세트 정보를 찾을 수 없습니다.")
            return
            
        # 복원 확인
        confirm = messagebox.askyesno(
            "복원 확인", 
            f"'{backup_set['description']}' 백업 세트의 {len(backup_set['files'])}개 파일을 복원하시겠습니까?\n"
            "기존 파일이 있다면 덮어씁니다."
        )
        
        if not confirm:
            return
            
        try:
            self.progress_bar["value"] = 0
            self.status_label.config(text="복원 준비 중...")
            self.root.update_idletasks()
            
            # 백업 세트에 속한 파일 경로 가져오기
            backup_files = get_backup_set_files(self.backup_folder, set_id)
            
            total_files = len(backup_files)
            restored_count = 0
            
            for idx, backup_file in enumerate(backup_files, 1):
                self.update_progress(idx, total_files)
                
                if os.path.exists(backup_file):
                    backup_file_name = os.path.basename(backup_file)
                    original_file_name = get_original_filename(backup_file_name)
                    
                    # 파일 복원
                    restore_save_file(backup_file, self.save_folder, original_file_name)
                    restored_count += 1
                
            self.status_label.config(text="복원 완료")
            messagebox.showinfo("성공", f"{restored_count}개의 파일이 원래 이름으로 복원되었습니다.")
            
        except Exception as e:
            self.status_label.config(text="오류 발생")
            messagebox.showerror("오류", str(e))

# 메인 애플리케이션 실행 코드
if __name__ == "__main__":
    root = tk.Tk()
    app = SaveManagerGUI(root)
    root.mainloop()