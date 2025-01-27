import tkinter as tk
import random
import time
import tkinter.messagebox
from PIL import Image, ImageTk
import os

class MathQuiz(tk.Tk):
    def get_time_limit(self):
        dialog = tk.Toplevel(self)
        dialog.title("Quiz Settings")
        dialog.geometry("400x200")
        dialog.transient(self)
    
        dialog.geometry("+%d+%d" % (
            self.winfo_rootx() + 50,
            self.winfo_rooty() + 50))
        tk.Label(
            dialog,
            text="Enter time limit in seconds:",
            font=("Arial", 14)
        ).pack(pady=20)
        
        entry = tk.Entry(dialog, font=("Arial", 14))
        entry.pack(pady=10)
        entry.insert(0, "120")
        
        self.time_input = None
        
        def on_ok():
            try:
                time_val = int(entry.get())
                if time_val > 0:
                    self.time_input = time_val
                    dialog.destroy()
                else:
                    tk.messagebox.showerror(
                        "Error",
                        "Please enter a positive number"
                    )
            except ValueError:
                tk.messagebox.showerror(
                    "Error",
                    "Please enter a valid number"
                )
        
        tk.Button(
            dialog,
            text="OK",
            command=on_ok,
            font=("Arial", 12)
        ).pack(pady=20)
        
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        
        entry.focus_set()
        entry.selection_range(0, tk.END)
        
        dialog.grab_set()
        self.wait_window(dialog)
        
        return self.time_input or 120 
    
    def play_celebration_gif(self):
        self.gif_label = tk.Label(self)
        self.gif_label.place(relx=0.8, rely=0.5, anchor="center")
    
        gif_path = os.path.join("Silly_Folder", "oia-uia.gif")
        gif = Image.open(gif_path)
        
        self.gif_frames = []
        self.current_frame = 0
        
        try:
            while True:
                self.gif_frames.append(ImageTk.PhotoImage(gif.copy()))
                gif.seek(len(self.gif_frames))
        except EOFError:
            pass
        
        def update_frame():
            if hasattr(self, 'gif_label'):
                frame = self.gif_frames[self.current_frame]
                self.gif_label.configure(image=frame)
                self.current_frame = (self.current_frame + 1) % len(self.gif_frames)
                self.after(50, update_frame)
        
        update_frame()

    def __init__(self):
        super().__init__()
        self.title("Arithmetic Quiz")

        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        
        # Add Ctrl+R shortcut binding
        self.bind("<Control-r>", lambda e: self.reset_quiz())

        self.num_questions = 200   
        self.time_limit = self.get_time_limit()       

        self.correct_answers = 0
        self.current_question = 0
        self.start_time = 0  
        self.quiz_ended = False  

        self.timer_label = tk.Label(self, font=("Arial", 24), fg="black")
        self.timer_label.place(x=10, y=10)

        # Add reset button in bottom left
        self.reset_button = tk.Button(
            self,
            text="Reset Quiz",
            font=("Arial", 14),
            command=self.reset_quiz
        )
        self.reset_button.place(x=10, rely=0.95, anchor="sw")

        self.center_frame = tk.Frame(self)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        self.countdown_label = tk.Label(self.center_frame, font=("Arial", 40))
        self.countdown_label.pack(pady=20)

        self.question_label = tk.Label(self.center_frame, font=("Arial", 40))

        self.answer_var = tk.StringVar()
        self.answer_var.trace_add("write", self.on_text_change)

        self.answer_entry = tk.Entry(
            self.center_frame, font=("Arial", 36), textvariable=self.answer_var, width=5
        )

        self.try_again_button = None
        self.end_button = None

        self.countdown_seconds = 3
        self.update_start_countdown()

    def update_start_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.config(
                text=f"Starting in {self.countdown_seconds}..."
            )
            self.countdown_seconds -= 1
            self.after(1000, self.update_start_countdown)
        else:
            self.countdown_label.pack_forget()
            self.question_label.pack(pady=20)
            self.answer_entry.pack(pady=10)
            self.answer_entry.focus()

            self.start_time = time.time()

            self.quiz_ended = False
            self.next_question()

            self.update_quiz_timer()

    def update_quiz_timer(self):
        if self.quiz_ended:
            return

        elapsed = time.time() - self.start_time
        time_left = max(0, self.time_limit - int(elapsed))

        if time_left <= 0:
            self.timer_label.config(text="Time left: 0s")
            self.end_quiz()
        else:
            self.timer_label.config(text=f"Time left: {time_left}s")
            next_update = 1000 - (int(elapsed * 1000) % 1000)
            self.after(next_update, self.update_quiz_timer)

    def next_question(self):
        elapsed = time.time() - self.start_time
        if self.current_question >= self.num_questions or elapsed >= self.time_limit:
            self.end_quiz()
            return

        self.A = random.randint(2, 100)
        self.B = random.randint(2, 100)
        self.C = random.randint(2, 12)

        self.operation = random.choice(["Addition", "Subtraction",
                                        "Multiplication", "Division"])

        if self.operation == "Addition":
            self.expected = self.A + self.B
            prompt = f"{self.A} + {self.B}"
        elif self.operation == "Subtraction":
            D = self.A + self.B
            self.expected = self.B
            prompt = f"{D} - {self.A}"
        elif self.operation == "Multiplication":
            self.expected = self.C * self.B
            prompt = f"{self.C} x {self.B}"
        else: 
            mult_rand = self.C * self.B
            self.expected = mult_rand // self.C
            prompt = f"{mult_rand} / {self.C}"

        self.question_label.config(text=prompt)
        self.answer_var.set("")

        self.current_question += 1

    def on_text_change(self, *args):
        if self.quiz_ended:
            return 

        elapsed = time.time() - self.start_time
        if elapsed >= self.time_limit:
            self.end_quiz()
            return

        user_input = self.answer_var.get().strip()
        if not user_input:
            return 

        try:
            user_number = int(user_input)
        except ValueError:
            return 

        if user_number == self.expected:
            self.correct_answers += 1
            self.next_question()

    def end_quiz(self):
        if self.quiz_ended:
            return

        self.quiz_ended = True
        self.answer_entry.config(state=tk.DISABLED)

        elapsed = time.time() - self.start_time
        total_time = elapsed if elapsed < self.time_limit else self.time_limit
        summary = f"Score: {self.correct_answers}"
        self.question_label.config(text=summary)

        if self.correct_answers >= 100 and self.time_limit == 120:
            self.play_celebration_gif()

        self.try_again_button = tk.Button(
            self.center_frame, text="Try Again", font=("Arial", 30),
            command=self.reset_quiz
        )
        self.try_again_button.pack(pady=10)

        self.end_button = tk.Button(
            self.center_frame, text="End Application", font=("Arial", 30),
            command=self.quit_application
        )
        self.end_button.pack(pady=10)

    def reset_quiz(self):
        if hasattr(self, 'gif_label'):
            self.gif_label.destroy()
            delattr(self, 'gif_label')
        
        self.correct_answers = 0
        self.current_question = 0
        self.answer_entry.config(state=tk.NORMAL)

        if self.try_again_button:
            self.try_again_button.destroy()
            self.try_again_button = None
        if self.end_button:
            self.end_button.destroy()
            self.end_button = None

        self.question_label.pack_forget()
        self.answer_entry.pack_forget()
        self.answer_var.set("")

        self.timer_label.config(text=f"Time left: {self.time_limit}s")

        self.countdown_label.config(text="")
        self.countdown_label.pack(pady=20)      

        self.countdown_seconds = 3
        self.update_start_countdown()

    def quit_application(self):
        self.destroy()

if __name__ == "__main__":
    app = MathQuiz()
    app.mainloop()