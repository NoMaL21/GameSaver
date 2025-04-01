import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import re
from file_manager import backup_save_file, restore_save_file, get_original_filename

class SaveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("세이브 파일 관리자")
        self.root.geometry("700x700")
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

        self.setup_ui()

    def setup_ui(self):
        # 메인 프레임
        main_frame = ttk.Frame(self.root, padding=20)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # 제목
        title_label = ttk.Label(main_frame, text="게임 세이브 파일 관리자", style='Header.TLabel')
        title_label.pack(pady=10)
        
        # 세이브 폴더 선택 프레임
        folder_frame = ttk.LabelFrame(main_frame, text="세이브 폴더 선택", padding=10)
        folder_frame.pack(fill=tk.X, pady=10)
        
        folder_frame_inner = ttk.Frame(folder_frame)
        folder_frame_inner.pack(fill=tk.X)
        
        self.folder_entry = ttk.Entry(folder_frame_inner, width=50)
        self.folder_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        folder_button = ttk.Button(folder_frame_inner, text="폴더 선택", command=self.select_save_folder)
        folder_button.pack(side=tk.RIGHT)
        
        # 세이브 파일 선택 프레임
        files_frame = ttk.LabelFrame(main_frame, text="세이브 파일 선택", padding=10)
        files_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        files_button = ttk.Button(files_frame, text="파일 선택", command=self.select_save_files)
        files_button.pack(side=tk.TOP, anchor=tk.W)
        
        # 파일 목록을 보여줄 리스트박스
        list_frame = ttk.Frame(files_frame)
        list_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.file_listbox = tk.Listbox(list_frame, selectmode=tk.MULTIPLE, height=6)
        self.file_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # 스크롤바 추가
        file_scrollbar = ttk.Scrollbar(list_frame, orient="vertical", command=self.file_listbox.yview)
        file_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self.file_listbox.config(yscrollcommand=file_scrollbar.set)
        
        # 선택 파일 제거 버튼
        remove_button = ttk.Button(files_frame, text="선택 파일 제거", command=self.remove_selected_files)
        remove_button.pack(side=tk.TOP, anchor=tk.W, pady=(0, 5))
        
        # 백업 폴더 선택 프레임
        backup_frame = ttk.LabelFrame(main_frame, text="백업 폴더 선택", padding=10)
        backup_frame.pack(fill=tk.X, pady=10)
        
        backup_frame_inner = ttk.Frame(backup_frame)
        backup_frame_inner.pack(fill=tk.X)
        
        self.backup_entry = ttk.Entry(backup_frame_inner, width=50)
        self.backup_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 10))
        
        backup_folder_button = ttk.Button(backup_frame_inner, text="폴더 선택", command=self.select_backup_folder)
        backup_folder_button.pack(side=tk.RIGHT)
        
        # 작업 상태 프레임
        status_frame = ttk.Frame(main_frame)
        status_frame.pack(fill=tk.X, pady=10)
        
        self.status_label = ttk.Label(status_frame, text="준비됨")
        self.status_label.pack(side=tk.LEFT)
        
        self.progress_bar = ttk.Progressbar(status_frame, orient="horizontal", length=300, mode="determinate")
        self.progress_bar.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        # 버튼 프레임
        button_frame = ttk.Frame(main_frame)
        button_frame.pack(fill=tk.X, pady=10)
        
        # 백업 버튼
        backup_btn = ttk.Button(button_frame, text="백업하기", command=self.backup_files, width=15)
        backup_btn.pack(side=tk.LEFT, padx=5)
        
        # 복원 버튼
        restore_btn = ttk.Button(button_frame, text="복원하기", command=self.restore_files, width=15)
        restore_btn.pack(side=tk.RIGHT, padx=5)

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
            
            total_files = len(self.save_files)
            for idx, file in enumerate(self.save_files, 1):
                self.update_progress(idx, total_files)
                backup_path = backup_save_file(file, self.backup_folder)
                
            self.status_label.config(text="백업 완료")
            messagebox.showinfo("성공", f"{total_files}개의 파일이 백업되었습니다.")
        except Exception as e:
            self.status_label.config(text="오류 발생")
            messagebox.showerror("오류", str(e))
            
    def restore_files(self):
        """백업 파일을 원래 세이브 파일 이름으로 복원"""
        if not self.save_folder:
            messagebox.showerror("오류", "세이브 폴더를 먼저 선택해주세요.")
            return

        if not self.backup_folder:
            messagebox.showerror("오류", "백업 폴더를 먼저 선택해주세요.")
            return

        backup_files = filedialog.askopenfilenames(
            title="복원할 백업 파일 선택 (여러 개 가능)", 
            initialdir=self.backup_folder,
            filetypes=[("모든 파일", "*.*")]
        )

        if not backup_files:
            return

        try:
            self.progress_bar["value"] = 0
            self.status_label.config(text="복원 준비 중...")
            self.root.update_idletasks()
            
            total_files = len(backup_files)
            for idx, backup_file in enumerate(backup_files, 1):
                self.update_progress(idx, total_files)
                
                backup_file_name = os.path.basename(backup_file)

                # 원래 파일명 찾기 (예: "ABC_2504011526.sav" -> "ABC.sav")
                # 여기서 정규식을 이용한 로직 대신 file_manager.py의 함수 사용
                original_file_name = re.sub(r'_\d{10}', '', backup_file_name)
                
                #원래 파일이름을 가져옴
                original_file_name = get_original_filename(backup_file_name)

                # file_manager의 restore_save_file 함수 사용
                restore_save_file(backup_file, self.save_folder, original_file_name)

            self.status_label.config(text="복원 완료")
            messagebox.showinfo("성공", f"{total_files}개의 파일이 원래 이름으로 복원되었습니다.")
        except Exception as e:
            self.status_label.config(text="오류 발생")
            messagebox.showerror("오류", str(e))

# 메인 애플리케이션 실행 코드
if __name__ == "__main__":
    root = tk.Tk()
    app = SaveManagerGUI(root)
    root.mainloop()