import os
import cv2
import numpy as np
import logging
import PySimpleGUI as sg
from concurrent.futures import ThreadPoolExecutor, as_completed
from moviepy.editor import VideoFileClip, AudioFileClip, ImageClip, concatenate_videoclips

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

def generate_video(image_folder, output_video_file, fps=30, time_per_image=5, fade_duration=1, is_shorts=False):
    try:
        images = [os.path.join(image_folder, img) for img in os.listdir(image_folder) if img.endswith((".jpg", ".png"))]
        images.sort()

        if not images:
            logging.error("No images found in the folder.")
            return

        video_clips = []
        total_duration = 0
        max_duration = 60 

        if is_shorts:
            video_height = 1920
            video_width = 1080
        else:
            video_height = 1080
            video_width = 1920

        with ThreadPoolExecutor() as executor:
            futures = {executor.submit(process_image, img_path, video_width, video_height): img_path for img_path in images}

            for future in as_completed(futures):
                image_result = future.result()
                if image_result is not None:
                    img_clip = ImageClip(image_result).set_duration(time_per_image).fadein(fade_duration).fadeout(fade_duration)

                    if total_duration + time_per_image <= max_duration:
                        video_clips.append(img_clip)
                        total_duration += time_per_image
                    else:
                        logging.info("Video duration reached 60 seconds, stopping further additions.")
                        break

        if not video_clips:
            logging.error("No valid images were processed for the video.")
            return

        final_video = concatenate_videoclips(video_clips, method="compose")
        final_video.write_videofile(output_video_file, fps=fps, codec="libx264", audio_codec="aac")
        logging.info(f"Video saved as {output_video_file}")

    except Exception as e:
        logging.error(f"An error occurred while generating the video: {str(e)}")

def add_audio_to_video(video_file, audio_file, output_with_audio, fade_duration=2):
    try:
        video_clip = VideoFileClip(video_file)
        audio_clip = AudioFileClip(audio_file)

        final_audio = audio_clip.subclip(0, video_clip.duration).audio_fadein(fade_duration).audio_fadeout(fade_duration)
        final_clip = video_clip.set_audio(final_audio)

        final_clip.write_videofile(output_with_audio, codec="libx264", audio_codec="aac")
        logging.info(f"Video with audio saved as {output_with_audio}")
    except Exception as e:
        logging.error(f"An error occurred while adding audio to the video: {str(e)}")

def main():
    layout = [
        [sg.Text("Select Image Folder"), sg.Input(), sg.FolderBrowse(key="-IMAGEFOLDER-")],
        [sg.Text("Select Audio File"), sg.Input(), sg.FileBrowse(key="-AUDIOFILE-")],
        [sg.Text("Select Video Type"), sg.Radio('Regular Video', "RADIO1", default=True, key="-REGULAR-"), sg.Radio('YouTube Shorts', "RADIO1", key="-SHORTS-")],
        [sg.Button("Create Video"), sg.Exit()]
    ]

    window = sg.Window("Video Generator", layout)

    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == "Create Video":
            image_folder = values["-IMAGEFOLDER-"]
            audio_file = values["-AUDIOFILE-"]
            is_shorts = values["-SHORTS-"]
            output_video_file = os.path.join(os.path.dirname(image_folder), 'output_video.mp4')
            output_with_audio = os.path.join(os.path.dirname(image_folder), 'output_video_with_audio.mp4')

            generate_video(image_folder, output_video_file, fps=30, time_per_image=5, is_shorts=is_shorts)
            add_audio_to_video(output_video_file, audio_file, output_with_audio)

    window.close()

if __name__ == "__main__":
    main()
