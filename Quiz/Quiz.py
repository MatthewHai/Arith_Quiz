import tkinter as tk
import random
import time
import tkinter.messagebox
from PIL import Image, ImageTk, ImageFilter, ImageDraw, ImageFont
import os
import pygame
import vlc
import yt_dlp

class MathQuiz(tk.Tk):
    def get_time_limit(self):
        dialog = tk.Toplevel(self)
        dialog.title("Quiz Settings")
        dialog.geometry("400x200")
        dialog.transient(self)
        dialog.geometry("+%d+%d" % (self.winfo_rootx() + 50, self.winfo_rooty() + 50))
        tk.Label(dialog, text="Enter time limit in seconds:", font=("Arial", 14)).pack(pady=20)
        
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
                    tk.messagebox.showerror("Error", "Please enter a positive number")
            except ValueError:
                tk.messagebox.showerror("Error", "Please enter a valid number")
        
        tk.Button(dialog, text="OK", command=on_ok, font=("Arial", 12)).pack(pady=20)
        dialog.protocol("WM_DELETE_WINDOW", lambda: None)
        entry.focus_set()
        entry.selection_range(0, tk.END)
        dialog.grab_set()
        self.wait_window(dialog)
        return self.time_input or 120 

    def play_celebration_gif(self):
        self.gif_label = tk.Label(self)
        self.gif_label.place(relx=0.8, rely=0.5, anchor="center")
    
        gif_path1 = os.path.join("Silly_Folder", "oia-uia.gif")
        gif1 = Image.open(gif_path1)
        self.gif1_frames = []
        self.current_frame1 = 0
        try:
            while True:
                self.gif1_frames.append(ImageTk.PhotoImage(gif1.copy()))
                gif1.seek(len(self.gif1_frames))
        except EOFError:
            pass
        
        def update_frame():
            if hasattr(self, 'gif_label'):
                frame = self.gif1_frames[self.current_frame1]
                self.gif_label.configure(image=frame)
                self.current_frame1 = (self.current_frame1 + 1) % len(self.gif1_frames)
                self.after(50, update_frame)
        
        update_frame()

    def play_left_gif2(self):
        if hasattr(self, 'gif2_label'):
            return
        
        self.gif2_label = tk.Label(self)
        self.gif2_label.place(relx=0.1, rely=0.5, anchor="center")
        gif_path2 = os.path.join("Silly_Folder", "fish-spinning.gif")
        gif2 = Image.open(gif_path2)
        self.gif2_frames = []
        self.current_frame2 = 0
        try:
            while True:
                self.gif2_frames.append(ImageTk.PhotoImage(gif2.copy()))
                gif2.seek(len(self.gif2_frames))
        except EOFError:
            pass

        def update_frame2():
            if hasattr(self, 'gif2_label'):
                frame = self.gif2_frames[self.current_frame2]
                self.gif2_label.configure(image=frame)
                self.current_frame2 = (self.current_frame2 + 1) % len(self.gif2_frames)
                self.after(50, update_frame2)
        update_frame2()

    def __init__(self):
        super().__init__()
        self.title("Arithmetic Quiz")
        pygame.mixer.init()
        self.bayle_sound = pygame.mixer.Sound(os.path.join("Silly_Folder", "Bayle.mp3"))
        self.attributes('-fullscreen', True)
        self.bind("<Escape>", lambda e: self.attributes("-fullscreen", False))
        self.bind("<Control-r>", lambda e: self.reset_quiz())
        self.num_questions = 200
        self.time_limit = self.get_time_limit()

        self.correct_answers = 0         # how many correct so far
        self.current_question = 0        # which question # is currently displayed
        self.start_time = 0
        self.quiz_ended = False

        self.timer_label = tk.Label(self, font=("Arial", 24), fg="black")
        self.timer_label.place(x=10, y=10)
        self.score_label = tk.Label(self, text="Score: 0", font=("Arial", 24), fg="black")
        self.score_label.place(relx=0.98, y=10, anchor="ne")
        self.reset_button = tk.Button(self, text="Reset Quiz (Ctrl+R)", font=("Arial", 14), command=self.reset_quiz)
        self.reset_button.place(x=10, rely=0.95, anchor="sw")

        # Center frame (place) but using grid inside it
        self.center_frame = tk.Frame(self)
        self.center_frame.place(relx=0.5, rely=0.5, anchor="center")

        # Convert default BG to a hex string
        self.default_bg = self.center_frame.cget("bg")
        try:
            from PIL import ImageColor
            _ = ImageColor.getrgb(self.default_bg)
        except Exception:
            r, g, b = self.center_frame.winfo_rgb(self.default_bg)
            self.default_bg = f"#{r//256:02x}{g//256:02x}{b//256:02x}"

        self.countdown_label = tk.Label(self.center_frame, font=("Arial", 40))
        self.countdown_label.grid(row=0, column=0, pady=20)

        self.question_image_label = None
        self.current_prompt = ""

        self.answer_var = tk.StringVar()
        self.answer_var.trace_add("write", self.on_text_change)
        self.answer_entry = tk.Entry(
            self.center_frame,
            font=("Arial", 36),
            textvariable=self.answer_var,
            width=5,
            bd=0,
            highlightthickness=0,
            relief="flat"
        )

        self.try_again_button = None
        self.end_button = None
        self.countdown_seconds = 3
        self.update_start_countdown()

        # Setup VLC
        self.video_width = 320
        self.video_height = 180
        self.video_frame = tk.Frame(self, width=self.video_width, height=self.video_height, bg="black")
        self.vlc_instance = vlc.Instance()
        self.vlc_player = self.vlc_instance.media_player_new()

        youtube_url = "https://www.youtube.com/watch?v=IbrQDkNLesw"
        info = self.get_ytdlp_info(youtube_url)
        self.direct_stream_url = None
        self.video_duration = 0
        if info:
            self.direct_stream_url = info["direct_url"]
            self.video_duration = info["duration"]
            media = self.vlc_instance.media_new(self.direct_stream_url)
            self.vlc_player.set_media(media)

        # We'll store a reference to our 15-second timer so we can cancel/re-schedule if needed
        self.nemesis_timer = None

    def get_ytdlp_info(self, youtube_url):
        ydl_opts = {'format': 'best', 'quiet': True, 'noprogress': True}
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                meta = ydl.extract_info(youtube_url, download=False)
            if "entries" in meta:
                meta = meta["entries"][0]
            direct_url = meta.get("url")
            duration = meta.get("duration", 0)
            if not direct_url or not duration:
                print("yt-dlp: Missing 'url' or 'duration'")
                return None
            return {"direct_url": direct_url, "duration": duration}
        except Exception as e:
            print("yt-dlp error:", e)
            return None

    def generate_text_image(self, text, blur_radius, bg_color):
        try:
            font = ImageFont.truetype("arial.ttf", 40)
        except Exception:
            font = ImageFont.load_default()
        dummy_img = Image.new("RGB", (1, 1))
        draw = ImageDraw.Draw(dummy_img)
        bbox = draw.textbbox((0, 0), text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        image = Image.new("RGB", (text_width + 20, text_height + 20), bg_color)
        draw = ImageDraw.Draw(image)
        draw.text((10, 10), text, fill="black", font=font)
        if blur_radius > 0:
            image = image.filter(ImageFilter.GaussianBlur(radius=blur_radius))
        return ImageTk.PhotoImage(image)

    def render_question_image(self):
        if self.question_image_label is not None and self.current_prompt:
            elapsed = time.time() - self.question_start_time
            MAX_BLUR = 20
            if elapsed < 10:
                blur_radius = 0
            else:
                blur_radius = min(elapsed - 10, 20) / 20 * MAX_BLUR
            bg_color = getattr(self, "current_flash_bg", self.default_bg)
            photo = self.generate_text_image(self.current_prompt, blur_radius, bg_color)
            self.question_image_label.configure(image=photo)
            self.question_image_label.image = photo

    def update_blur_effect(self):
        if self.quiz_ended or self.question_image_label is None:
            return
        self.render_question_image()
        self.blur_job = self.after(500, self.update_blur_effect)

    # Just a helper to schedule Nemesis in 15s
    def schedule_tf_nemesis_timer(self):
        if self.nemesis_timer:
            self.after_cancel(self.nemesis_timer)
        self.nemesis_timer = self.after(20000, self.play_tf_nemesis_sound)

    def play_tf_nemesis_sound(self):
        nemesis_path = os.path.join("Silly_Folder", "tf_nemesis.mp3")
        if os.path.exists(nemesis_path):
            nemesis_sound = pygame.mixer.Sound(nemesis_path)
            nemesis_sound.play()
        else:
            print("Nemesis sound not found:", nemesis_path)

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

        # If correct:
        if user_number == self.expected:
            self.correct_answers += 1
            self.score_label.config(text=f"Score: {self.correct_answers}")

            # 1) rap.mp3 after first correct answer
            if self.correct_answers == 1:
                rap_path = os.path.join("Silly_Folder", "rap.mp3")
                if os.path.exists(rap_path):
                    rap_sound = pygame.mixer.Sound(rap_path)
                    rap_sound.play()
                else:
                    print("rap.mp3 not found in Silly_Folder!")

            # 2) Check multiples of 3 => airhorn, multiples of 7 => wombo
            question_just_answered = self.current_question
            if question_just_answered % 3 == 0:
                # airhorn
                airhorn_path = os.path.join("Silly_Folder", "dj-airhorn-sound-effect-kingbeatz_1.mp3")
                if os.path.exists(airhorn_path):
                    airhorn_sound = pygame.mixer.Sound(airhorn_path)
                    airhorn_sound.play()
                else:
                    print("dj-airhorn-sound-effect-kingbeatz_1.mp3 not found in Silly_Folder!")

            if question_just_answered % 7 == 0:
                # wombo
                wombo_path = os.path.join("Silly_Folder", "wombo-combo_2.mp3")
                if os.path.exists(wombo_path):
                    wombo_sound = pygame.mixer.Sound(wombo_path)
                    wombo_sound.play()
                else:
                    print("wombo-combo_2.mp3 not found in Silly_Folder!")

            # 3) 15-second timer for tf_nemesis
            self.schedule_tf_nemesis_timer()

            self.flash_screen()

            # If user reached 25 correct answers -> fish spinning
            if self.correct_answers == 25:
                self.play_left_gif2()

            # Random video seek every 5 correct answers
            if self.direct_stream_url and self.correct_answers % 5 == 0:
                self.randomize_location_and_seek()

            self.next_question()

    def flash_screen(self):
        if hasattr(self, 'flash_overlay'):
            return
        flash_count = 3 + self.correct_answers // 10
        interval = max(50, 150 - self.correct_answers // 2)

        self.flash_overlay = tk.Frame(self)
        self.flash_overlay.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.flash_overlay.lower()

        def complementary(hex_color):
            hex_color = hex_color.lstrip('#')
            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)
            return f"#{255 - r:02x}{255 - g:02x}{255 - b:02x}"

        default_bg = self.default_bg
        default_fg = "black"
        default_entry_bg = "white"

        def do_flash(i):
            if i < flash_count:
                if self.correct_answers < 20:
                    new_color = "#%06x" % random.randint(0, 0xFFFFFF)
                else:
                    new_color = random.choice(["#ff0000", "#00ff00", "#0000ff", "#ffff00", "#ff00ff", "#00ffff"])
                self.flash_overlay.config(bg=new_color)
                self.current_flash_bg = new_color
                self.center_frame.config(bg=new_color)
                self.timer_label.config(bg=new_color, fg=complementary(new_color))
                self.score_label.config(bg=new_color, fg=complementary(new_color))
                self.answer_entry.config(
                    bg=new_color,
                    fg=complementary(new_color),
                    insertbackground=complementary(new_color)
                )

                self.render_question_image()
                self.video_frame.lift()
                self.after(interval, lambda: do_flash(i + 1))
            else:
                # revert everything to default
                self.center_frame.config(bg=default_bg)
                self.timer_label.config(bg=default_bg, fg=default_fg)
                self.score_label.config(bg=default_bg, fg=default_fg)
                self.answer_entry.config(bg=default_entry_bg, fg=default_fg, insertbackground=default_fg)
                self.flash_overlay.destroy()
                del self.flash_overlay
                self.current_flash_bg = default_bg
                self.render_question_image()

        do_flash(0)

    def randomize_location_and_seek(self):
        if not self.direct_stream_url:
            return
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        EXCLUSION_WIDTH, EXCLUSION_HEIGHT = 600, 400
        center_x, center_y = screen_w // 2, screen_h // 2
        exclusion_left = center_x - EXCLUSION_WIDTH // 2
        exclusion_right = center_x + EXCLUSION_WIDTH // 2
        exclusion_top = center_y - EXCLUSION_HEIGHT // 2
        exclusion_bottom = center_y + EXCLUSION_HEIGHT // 2

        while True:
            rand_x = random.randint(0, screen_w - self.video_width)
            rand_y = random.randint(0, screen_h - self.video_height)
            overlap = not (rand_x + self.video_width < exclusion_left or
                           rand_x > exclusion_right or
                           rand_y + self.video_height < exclusion_top or
                           rand_y > exclusion_bottom)
            if not overlap:
                break

        self.video_frame.place_forget()
        self.vlc_player.stop()
        self.update_idletasks()
        self.update()

        self.vlc_player.set_hwnd(self.video_frame.winfo_id())
        self.vlc_player.play()

        self.after(100, lambda: self._pause_seek_show(rand_x, rand_y))

    def _pause_seek_show(self, rand_x, rand_y):
        if self.video_duration < 2:
            return
        self.vlc_player.set_pause(1)
        random_sec = random.randint(0, self.video_duration - 1)
        ms = random_sec * 1000
        print(f"Seek => {random_sec} seconds")
        self.vlc_player.set_time(ms)
        self.video_frame.place(x=rand_x, y=rand_y)
        self.vlc_player.set_pause(0)

    def update_start_countdown(self):
        if self.countdown_seconds > 0:
            self.countdown_label.config(text=f"Starting in {self.countdown_seconds}...")
            self.countdown_seconds -= 1
            self.after(1000, self.update_start_countdown)
        else:
            self.countdown_label.grid_remove()
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
        if hasattr(self, 'blur_job'):
            self.after_cancel(self.blur_job)
            del self.blur_job

        # Remove previous question label if it exists
        if self.question_image_label is not None:
            self.question_image_label.destroy()
            self.question_image_label = None

        elapsed = time.time() - self.start_time
        if self.current_question >= self.num_questions or elapsed >= self.time_limit:
            self.end_quiz()
            return

        A = random.randint(2, 100)
        B = random.randint(2, 100)
        C = random.randint(2, 12)
        self.operation = random.choice(["Addition", "Subtraction", "Multiplication", "Division"])

        if self.operation == "Addition":
            self.expected = A + B
            prompt = f"{A} + {B}"
        elif self.operation == "Subtraction":
            D = A + B
            self.expected = B
            prompt = f"{D} - {A}"
        elif self.operation == "Multiplication":
            self.expected = C * B
            prompt = f"{C} x {B}"
        else:
            mult_rand = C * B
            self.expected = mult_rand // C
            prompt = f"{mult_rand} / {C}"

        self.current_prompt = prompt
        self.question_start_time = time.time()

        # Create a label for the question
        self.question_image_label = tk.Label(
            self.center_frame,
            bd=0,
            highlightthickness=0,
            relief="flat"
        )
        self.question_image_label.grid(row=1, column=0, pady=20)
        self.render_question_image()

        self.answer_var.set("")
        self.answer_entry.grid(row=2, column=0, pady=10)
        self.answer_entry.focus()

        # We have now created question # (self.current_question + 1)
        self.current_question += 1

        # Update displayed score
        self.score_label.config(text=f"Score: {self.correct_answers}")

        # Start blur effect updates
        self.blur_job = self.after(500, self.update_blur_effect)

    def end_quiz(self):
        if self.quiz_ended:
            return
        self.quiz_ended = True
        self.answer_entry.config(state=tk.DISABLED)
        summary = f"Score: {self.correct_answers}"
        if self.question_image_label is not None:
            self.question_image_label.destroy()
            self.question_image_label = None

        self.question_label = tk.Label(self.center_frame, text=summary, font=("Arial", 40))
        self.question_label.grid(row=1, column=0, pady=20)

        if hasattr(self, 'blur_job'):
            self.after_cancel(self.blur_job)
            del self.blur_job

        if self.correct_answers == 99 and self.time_limit == 120:
            self.bayle_sound.play()
        elif self.correct_answers >= 100 and self.time_limit == 120:
            self.play_celebration_gif()

        self.try_again_button = tk.Button(
            self.center_frame, text="Try Again", font=("Arial", 30), command=self.reset_quiz
        )
        self.try_again_button.grid(row=2, column=0, pady=10)

        self.end_button = tk.Button(
            self.center_frame, text="End Application", font=("Arial", 30), command=self.quit_application
        )
        self.end_button.grid(row=3, column=0, pady=10)

    def reset_quiz(self):
        if hasattr(self, 'blur_job'):
            self.after_cancel(self.blur_job)
            del self.blur_job

        # Cancel Nemesis timer if it exists
        if self.nemesis_timer:
            self.after_cancel(self.nemesis_timer)
            self.nemesis_timer = None

        if self.question_image_label is not None:
            self.question_image_label.destroy()
            self.question_image_label = None
        if hasattr(self, 'gif2_label'):
            self.gif2_label.destroy()
            delattr(self, 'gif2_label')
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
        if hasattr(self, 'question_label'):
            self.question_label.destroy()

        self.answer_var.set("")
        self.timer_label.config(text=f"Time left: {self.time_limit}s")
        self.score_label.config(text="Score: 0")

        self.countdown_label.config(text="")
        self.countdown_label.grid(row=0, column=0, pady=20)
        self.countdown_seconds = 3

        self.video_frame.place_forget()
        self.vlc_player.stop()

        self.update_start_countdown()

    def quit_application(self):
        pygame.mixer.quit()
        self.destroy()

if __name__ == "__main__":
    app = MathQuiz()
    app.mainloop()
