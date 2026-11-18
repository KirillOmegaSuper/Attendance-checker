import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import sqlite3, csv, os, math
from datetime import datetime


class AttendanceApp:
    def __init__(self, root):
        self.root = root
        root.title("Attendance Control - Course Report")
        root.geometry("1000x700")
        root.configure(bg="#F3F6FC")
        folder = os.path.dirname(os.path.abspath(__file__))
        self.db = os.path.join(folder, "asistencia.db")
        self.report = None
        try:
            self.logo = tk.PhotoImage(file=os.path.join(folder, "logotype.png"))
            root.iconphoto(True, self.logo)
        except tk.TclError:
            self.logo = None
            messagebox.showwarning("Logo Not Found", "Place logotype.png next to the program.")
        self.database("init")
        self.build()
      
    # Database: initialize, save, clear and export all records.
    def database(self, task, data=None):
        with sqlite3.connect(self.db) as con:
            if task == "init":
                con.execute("""CREATE TABLE IF NOT EXISTS students (
                    id INTEGER PRIMARY KEY, student_id TEXT, course TEXT, total INTEGER,
                    attended INTEGER, excused INTEGER, unexcused INTEGER, percentage REAL,
                    minimum REAL, remaining INTEGER, status TEXT, date TEXT,
                    UNIQUE(student_id, course))""")
            elif task == "save":
                con.execute("""INSERT INTO students VALUES (NULL,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(student_id,course) DO UPDATE SET
                    total=excluded.total, attended=excluded.attended, excused=excluded.excused,
                    unexcused=excluded.unexcused, percentage=excluded.percentage,
                    minimum=excluded.minimum, remaining=excluded.remaining,
                    status=excluded.status, date=excluded.date""",
                    (data["DNI"], data["Course"], data["Total"], data["Attended"],
                     data["Excused"], data["Unexcused"], data["Percentage"],
                     data["Minimum"], data["Remaining"], data["Status"],
                     datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
            elif task == "clear":
                if messagebox.askyesno("Clear Database", "Delete all saved student records?"):
                    con.execute("DELETE FROM students")
                    messagebox.showinfo("Database", "Database cleared.")
            elif task == "export":
                rows = con.execute("SELECT student_id,course,total,attended,excused,unexcused,percentage,minimum,remaining,status,date FROM students ORDER BY course,student_id").fetchall()
                if not rows:
                    messagebox.showinfo("Database", "There are no saved records.")
                    return
                path = filedialog.asksaveasfilename(defaultextension=".csv", initialfile="Attendance_Database.csv", filetypes=[("CSV", "*.csv")])
                if path:
                    with open(path, "w", newline="", encoding="utf-8-sig") as f:
                        w = csv.writer(f, delimiter=";")
                        w.writerow(["Student ID", "Course", "Total Classes", "Attended", "Excused", "Unexcused", "Percentage", "Minimum", "Remaining", "Status", "Date"])
                        w.writerows(rows)
                    messagebox.showinfo("Export", f"Exported {len(rows)} records.")

    def calculate(self):
        try:
            course = self.fields["course"].get().strip() or "Not specified"
            dni = self.fields["dni"].get().strip()
            total = int(self.fields["total"].get())
            attended = int(self.fields["attended"].get())
            excused = int(self.fields["excused"].get() or 0)
            minimum = float(self.fields["minimum"].get().replace(",", "."))
            if not dni or len(dni) > 8 or not dni.isdigit():
                raise ValueError("Enter a valid Student ID (up to 8 digits).")
            if total <= 0 or not 0 <= minimum <= 100 or min(attended, excused) < 0 or attended + excused > total:
                raise ValueError("Check the class totals and minimum percentage.")
        except ValueError as e:
            messagebox.showerror("Invalid Input", str(e) or "Enter valid numbers in all fields.")
            return

        percentage = (attended + excused) / total * 100
        unexcused = total - attended - excused
        remaining = total - math.ceil(minimum * total / 100) - unexcused
        passed = percentage >= minimum
        status = "PASSED" if passed else "FAILED"
        margin = f"You may miss {remaining} more class(es)." if passed else f"You need {abs(remaining)} more class(es)."
        self.report = {"DNI": dni, "Course": course, "Total": total, "Attended": attended,
                       "Excused": excused, "Unexcused": unexcused, "Percentage": round(percentage, 2),
                       "Minimum": minimum, "Remaining": remaining, "Status": status}
        self.action("gauge", percentage, "#16A34A" if passed else "#DC2626")
        self.state.config(text="✓ PASSED" if passed else "✕ FAILED", bg="#0C9B50" if passed else "#C62828", fg="white")
        self.details.config(text=f"{course}\nAttended: {attended}/{total}\nExcused: {excused}\nUnexcused: {unexcused}\nRequired: {minimum:g}%\n{margin}")
        try:
            self.database("save", self.report)
            messagebox.showinfo("Saved", "Student record saved to the database.")
        except sqlite3.Error as e:
            messagebox.showerror("Database Error", str(e))
