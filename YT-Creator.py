import os
import cv2
import numpy as np
import logging
import PySimpleGUI as sg
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips
import threading

logging.basicConfig(level=logging.INFO)

def process_image(image_path, video_width, video_height):
    try:
        frame = cv2.imread(image_path)

        if frame is None:
            logging.warning(f"Skipping image {image_path}: Failed to read image.")
            return None

        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img_height, img_width = frame.shape[:2]

        background = cv2.GaussianBlur(frame, (99, 99), 30)
        background = cv2.resize(background, (video_width, video_height))

        scale = min(video_width / img_width, video_height / img_height)
        new_width = int(img_width * scale)
        new_height = int(img_height * scale)
        resized_image = cv2.resize(frame, (new_width, new_height))

        x_offset = (video_width - new_width) // 2
        y_offset = (video_height - new_height) // 2
        background[y_offset:y_offset + new_height, x_offset:x_offset + new_width] = resized_image

        return background
    except Exception as e:
        logging.error(f"Error processing image {image_path}: {str(e)}")
        return None

def generate_video(image_files, output_video_file, time_per_image=5, fade_duration=1, is_shorts=False, window=None):
    try:
        images = image_files
        if not images:
            logging.error("No images selected.")
            sg.popup_error("No images selected.")
            return

        video_clips = []
        total_duration = 0

        if is_shorts:
            video_height = 1920
            video_width = 1080
            max_duration = 60
        else:
            video_height = 1080
            video_width = 1920
            max_duration = None

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_image, img_path, video_width, video_height): img_path for img_path in images}

            for i, future in enumerate(as_completed(futures)):
                image_result = future.result()
                if image_result is not None:
                    img_clip = ImageClip(image_result).set_duration(time_per_image).fadein(fade_duration).fadeout(fade_duration)

                    if is_shorts:
                        if total_duration + time_per_image <= max_duration:
                            video_clips.append(img_clip)
                            total_duration += time_per_image
                        else:
                            logging.info("Video duration reached the maximum limit for Shorts (60 seconds), stopping further additions.")
                            break
                    else:
                        video_clips.append(img_clip)

                if window:
                    window['progress'].update_bar(i + 1)

        if not video_clips:
            logging.error("No valid images were processed for the video.")
            sg.popup_error("No valid images were processed for the video.")
            return

        final_video = concatenate_videoclips(video_clips, method="compose")
        final_video.write_videofile(output_video_file, codec="libx264", audio_codec="aac")
        logging.info(f"Video saved as {output_video_file}")
        sg.popup("Video generated successfully!")

    except Exception as e:
        logging.error(f"An error occurred while generating the video: {str(e)}")
        sg.popup_error(f"An error occurred while generating the video: {str(e)}")

def add_audio_to_video(video_file, audio_file, output_with_audio, fade_duration=2):
    try:
        video_clip = VideoFileClip(video_file)
        audio_clip = AudioFileClip(audio_file)

        final_audio = audio_clip.subclip(0, video_clip.duration).audio_fadein(fade_duration).audio_fadeout(fade_duration)
        final_clip = video_clip.set_audio(final_audio)

        final_clip.write_videofile(output_with_audio, codec="libx264", audio_codec="aac")
        logging.info(f"Video with audio saved as {output_with_audio}")
        sg.popup("Video with audio generated successfully!")
    except Exception as e:
        logging.error(f"An error occurred while adding audio to the video: {str(e)}")
        sg.popup_error(f"An error occurred while adding audio to the video: {str(e)}")

def create_video_in_background(image_files, audio_file, is_shorts, time_per_image, window):
    output_video_file = os.path.join(os.path.dirname(image_files[0]), 'output_video.mp4')
    output_with_audio = os.path.join(os.path.dirname(image_files[0]), 'output_video_with_audio.mp4')

    generate_video(image_files, output_video_file, time_per_image=time_per_image, is_shorts=is_shorts, window=window)
    if os.path.exists(output_video_file) and audio_file:
        add_audio_to_video(output_video_file, audio_file, output_with_audio)

def main():
    sg.theme('DarkAmber')

    layout = [
        [sg.Text("Select Images"), sg.Input(), sg.FilesBrowse(key="-IMAGEFILES-", file_types=(("Image Files", "*.png;*.jpg;*.jpeg;*.bmp"),))],
        [sg.Text("Select Audio File"), sg.Input(), sg.FileBrowse(key="-AUDIOFILE-")],
        [sg.Text("Video Settings")],
        [sg.Radio('Regular Video', "RADIO1", default=True, key="-REGULAR-"), sg.Radio('YouTube Shorts', "RADIO1", key="-SHORTS-")],
        [sg.Text("Seconds per Image (Regular Video)"), sg.Slider(range=(1, 10), default_value=5, size=(20, 15), orientation='horizontal', key='-TIMEPERIMAGE-')],
        [sg.Button("Create Video"), sg.Exit()],
        [sg.ProgressBar(max_value=100, orientation='h', size=(20, 20), key='progress')],
        [sg.Output(size=(60, 10))]  
    ]

    window = sg.Window("Video Generator", layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == "Create Video":
            image_files = values["-IMAGEFILES-"].split(";")  
            audio_file = values["-AUDIOFILE-"]
            is_shorts = values["-SHORTS-"]
            time_per_image = values['-TIMEPERIMAGE-'] if not is_shorts else 1  

            if not image_files:
                sg.popup_error("No images selected.")
                continue
            if audio_file and not os.path.isfile(audio_file):
                sg.popup_error("Invalid audio file selected.")
                continue

            window['progress'].update_bar(0)  

            threading.Thread(target=create_video_in_background, args=(image_files, audio_file, is_shorts, time_per_image, window), daemon=True).start()

    window.close()

if __name__ == "__main__":
    main()
