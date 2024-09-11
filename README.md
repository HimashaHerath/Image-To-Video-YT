# Image-To-Video-YT

This is a Python-based video generator application that allows users to create videos from a set of images, with optional background audio. It provides options for generating YouTube Shorts (with a maximum duration of 60 seconds) or regular videos, where the user can specify how long each image should appear in the video.

## Features

- Select multiple images (PNG, JPG, JPEG, BMP) to generate a video.
- Option to add background audio to the generated video.
- Choose between creating a YouTube Shorts video or a regular video.
  - YouTube Shorts are limited to 60 seconds and each image stays for 1 second.
  - For regular videos, you can choose how many seconds each image will be displayed.
- Progress bar to show the status of the video generation.
- Saves the video to a specified output location.

## Requirements

The application requires the following Python libraries:

- `opencv-python`
- `PySimpleGUI`
- `moviepy`
- `numpy`

## Installation

1. Clone this repository to your local machine:

   ```bash
   git clone https://github.com/HimashaHerath/Image-To-Video-YT
   cd Image-To-Video-YT
