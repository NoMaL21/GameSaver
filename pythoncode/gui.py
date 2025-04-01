import tkinter as tk
from tkinter import filedialog, messagebox
import os
import re
import shutil
from file_manager import backup_save_file  # 백업 기능만 사용

class SaveManagerGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("세이브 파일 관리자")

        # 기본값 설정
        self.save_folder = ""
        self.save_files = []  # 여러 개 선택 가능
        self.backup_folder = ""

        self.setup_ui()

    def setup_ui(self):
        # 세이브 폴더 선택
        tk.Label(self.root, text="세이브 폴더 선택:").pack(pady=5)
        self.folder_entry = tk.Entry(self.root, width=50)
        self.folder_entry.pack(pady=5)
        tk.Button(self.root, text="폴더 선택", command=self.select_save_folder).pack(pady=5)

        # 세이브 파일 선택 (여러 개 가능)
        tk.Label(self.root, text="세이브 파일 선택 (여러 개 가능):").pack(pady=5)
        self.file_entry = tk.Entry(self.root, width=50)
        self.file_entry.pack(pady=5)
        tk.Button(self.root, text="파일 선택", command=self.select_save_files).pack(pady=5)

        # 백업 폴더 선택
        tk.Label(self.root, text="백업 폴더 선택:").pack(pady=5)
        self.backup_entry = tk.Entry(self.root, width=50)
        self.backup_entry.pack(pady=5)
        tk.Button(self.root, text="폴더 선택", command=self.select_backup_folder).pack(pady=5)

        # 백업 버튼
        backup_btn = tk.Button(self.root, text="백업하기", command=self.backup_files)
        backup_btn.pack(pady=10)

        # 복원 버튼
        restore_btn = tk.Button(self.root, text="복원하기", command=self.restore_files)
        restore_btn.pack(pady=10)

    def select_save_folder(self):
        """사용자가 세이브 파일이 있는 폴더를 선택"""
        folder_selected = filedialog.askdirectory(title="세이브 폴더 선택")
        if folder_selected:
            self.save_folder = folder_selected
            self.folder_entry.delete(0, tk.END)
            self.folder_entry.insert(0, folder_selected)

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
            self.save_files = list(files_selected)
            file_names = ", ".join(os.path.basename(f) for f in self.save_files)
            self.file_entry.delete(0, tk.END)
            self.file_entry.insert(0, file_names)

    def select_backup_folder(self):
        """사용자가 백업을 저장할 폴더를 선택"""
        folder_selected = filedialog.askdirectory(title="백업 폴더 선택")
        if folder_selected:
            self.backup_folder = folder_selected
            self.backup_entry.delete(0, tk.END)
            self.backup_entry.insert(0, folder_selected)

    def backup_files(self):
        """선택한 모든 세이브 파일을 백업"""
        if not self.save_files or not self.backup_folder:
            messagebox.showerror("오류", "세이브 파일과 백업 폴더를 선택해주세요.")
            return

        try:
            for file in self.save_files:
                backup_path = backup_save_file(file, self.backup_folder)
            messagebox.showinfo("성공", f"{len(self.save_files)}개의 파일이 백업되었습니다.")
        except Exception as e:
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
                for backup_file in backup_files:
                    backup_file_name = os.path.basename(backup_file)

                    # 원래 파일명 찾기 (예: "ABC_2504011526.sav" -> "ABC.sav")
                    original_file_name = re.sub(r'_\d{6}_\d{4}', '', backup_file_name)

                    restore_path = os.path.join(self.save_folder, original_file_name)

                    # 백업된 파일을 원본 폴더로 덮어쓰기
                    shutil.copy2(backup_file, restore_path)

                messagebox.showinfo("성공", f"{len(backup_files)}개의 파일이 원래 이름으로 복원되었습니다.")
            except Exception as e:
                messagebox.showerror("오류", str(e))

