import os
import cv2
import threading
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips

def process_image(image_path, video_width, video_height):
    try:
        # Read the image in BGR format (OpenCV default)
        frame = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)

        if frame is None:
            print(f"Skipping image {image_path}: Failed to read image.")
            return None

        # Convert BGR to RGB for MoviePy compatibility
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        img_height, img_width = frame_rgb.shape[:2]

        # Apply Gaussian blur to the background only
        background = cv2.GaussianBlur(frame_rgb, (99, 99), 30)  # Use larger kernel for soft blur
        background = cv2.resize(background, (video_width, video_height), interpolation=cv2.INTER_AREA)

        # Resize the original image while maintaining aspect ratio
        scale = min(video_width / img_width, video_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        resized_image = cv2.resize(frame_rgb, (new_width, new_height), interpolation=cv2.INTER_AREA)

        # Center the resized image on the background
        x_offset = (video_width - new_width) // 2
        y_offset = (video_height - new_height) // 2
        background[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

        return background

    except Exception as e:
        print(f"Error processing image {image_path}: {str(e)}")
        return None

def generate_video(image_files, audio_file, output_video_file, time_per_image, fade_duration=1, is_shorts=False, progress_var=None, status_label=None):
    video_clips = []
    total_duration = 0
    video_height, video_width = (1920, 1080) if is_shorts else (1080, 1920)

    # Process each image and create video clips
    for i, image_path in enumerate(image_files):
        image_result = process_image(image_path, video_width, video_height)
        if image_result is not None:
            img_clip = ImageClip(image_result).set_duration(time_per_image).fadein(fade_duration).fadeout(fade_duration)
            video_clips.append(img_clip)
        
        if progress_var:
            progress_var.set((i + 1) / len(image_files) * 100)
    
    final_video = concatenate_videoclips(video_clips, method="compose")

    # Add audio if selected
    if audio_file:
        audio_clip = AudioFileClip(audio_file)
        final_audio = audio_clip.subclip(0, final_video.duration)  # Match audio to video duration
        final_video = final_video.set_audio(final_audio)

    # Save the video
    final_video.write_videofile(output_video_file, codec="libx264", audio_codec="aac", fps=24)

    if status_label:
        status_label.config(text=f"Video saved: {output_video_file}")
    print(f"Video saved as {output_video_file}")

def open_files():
    return filedialog.askopenfilenames(title="Select Images", filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.bmp")])

def select_audio():
    return filedialog.askopenfilename(title="Select Audio File", filetypes=[("Audio Files", "*.mp3;*.wav")])

def select_output_file():
    return filedialog.asksaveasfilename(title="Select Output File", defaultextension=".mp4", filetypes=[("MP4 Files", "*.mp4")])

def create_video_gui():
    root = tk.Tk()
    root.title("Video Generator")
    root.geometry("450x600")
    
    # Styling and Layout
    root.style = ttk.Style()
    root.style.configure('TButton', font=('Helvetica', 12), padding=10)
    root.style.configure('TLabel', font=('Helvetica', 12))

    # Frame for inputs
    frame = ttk.Frame(root, padding="20")
    frame.pack(fill=tk.BOTH, expand=True)

    # Variables for images, audio, output file, image duration, and video type
    image_files = []
    audio_file = None
    output_file = None
    is_shorts = tk.BooleanVar()
    image_duration = tk.DoubleVar(value=5)  # Default image duration to 5 seconds

    def select_images():
        nonlocal image_files
        image_files = open_files()
        status_label.config(text=f"Selected {len(image_files)} images")

    def select_audio_file():
        nonlocal audio_file
        audio_file = select_audio()
        if audio_file:
            status_label.config(text=f"Selected audio: {os.path.basename(audio_file)}")

    def select_output_video_file():
        nonlocal output_file
        output_file = select_output_file()
        if output_file:
            status_label.config(text=f"Selected output file: {os.path.basename(output_file)}")

    def start_video_generation():
        if not image_files:
            messagebox.showerror("Error", "No images selected.")
            return
        if not output_file:
            messagebox.showerror("Error", "No output file selected.")
            return
        status_label.config(text="Generating video...")
        threading.Thread(target=generate_video, args=(image_files, audio_file, output_file, image_duration.get(), 1, is_shorts.get(), progress_var, status_label), daemon=True).start()

    # Progress Bar
    progress_var = tk.DoubleVar()
    progress = ttk.Progressbar(frame, variable=progress_var, maximum=100)
    progress.grid(row=10, column=0, columnspan=2, pady=20, sticky="ew")

    # Status Label
    status_label = ttk.Label(frame, text="Select images, audio, and output file to create a video.")
    status_label.grid(row=11, column=0, columnspan=2, pady=10)

    # Widgets for the UI
    ttk.Label(frame, text="Step 1: Select Images").grid(row=0, column=0, pady=10, sticky="w")
    ttk.Button(frame, text="Select Images", command=select_images).grid(row=0, column=1, padx=10, pady=10, sticky="e")

    ttk.Label(frame, text="Step 2: Select Audio (optional)").grid(row=1, column=0, pady=10, sticky="w")
    ttk.Button(frame, text="Select Audio", command=select_audio_file).grid(row=1, column=1, padx=10, pady=10, sticky="e")

    ttk.Label(frame, text="Step 3: Select Output File").grid(row=2, column=0, pady=10, sticky="w")
    ttk.Button(frame, text="Select Output File", command=select_output_video_file).grid(row=2, column=1, padx=10, pady=10, sticky="e")

    # Slider for Image Duration
    ttk.Label(frame, text="Step 4: Set Image Duration (seconds)").grid(row=3, column=0, pady=10, sticky="w")
    ttk.Scale(frame, from_=1, to=10, orient=tk.HORIZONTAL, variable=image_duration).grid(row=3, column=1, padx=10, pady=10, sticky="ew")
    ttk.Label(frame, textvariable=image_duration).grid(row=4, column=1, pady=10, sticky="e")

    # Video Type Selection (Regular or Shorts)
    ttk.Label(frame, text="Step 5: Select Video Type").grid(row=5, column=0, pady=10, sticky="w")
    ttk.Radiobutton(frame, text="Regular Video", variable=is_shorts, value=False).grid(row=5, column=1, padx=10, pady=10, sticky="w")
    ttk.Radiobutton(frame, text="YouTube Shorts", variable=is_shorts, value=True).grid(row=6, column=1, padx=10, pady=10, sticky="w")

    ttk.Label(frame, text="Step 6: Create Video").grid(row=7, column=0, pady=10, sticky="w")
    ttk.Button(frame, text="Create Video", command=start_video_generation).grid(row=7, column=1, padx=10, pady=10, sticky="e")

    root.mainloop()

if __name__ == "__main__":
    create_video_gui()
