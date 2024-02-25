import argparse
import cv2
import time
import requests
import socket

from ddp import DDPDevice


def resize_keep_aspect_ratio(image, target_width, target_height):
    # First crop the image to the target aspect ratio
    aspect_ratio = target_width / target_height
    image_aspect_ratio = image.shape[1] / image.shape[0]

    if image_aspect_ratio > aspect_ratio:
        # Crop the width
        new_width = int(image.shape[0] * aspect_ratio)
        start = (image.shape[1] - new_width) // 2
        image = image[:, start : start + new_width]
    else:
        # Crop the height
        new_height = int(image.shape[1] / aspect_ratio)
        start = (image.shape[0] - new_height) // 2
        image = image[start : start + new_height, :]
    # Resize to the target size
    image = cv2.resize(image, (target_width, target_height))
    return image


def get_matrix_dimensions(host):
    # Get WLED infos
    response = requests.get(f"http://{host}/json/info")
    response.raise_for_status()
    matrix = response.json()["leds"]["matrix"]
    return matrix["w"], matrix["h"]


def main():
    parser = argparse.ArgumentParser(description="Play video on DDP")
    parser.add_argument("ip", help="IP address of DDP")
    parser.add_argument("video", help="Path to video file")
    args = parser.parse_args()

    # This seems to be much much faster than
    # letting `requests` do the DNS resolution
    ip = socket.gethostbyname(args.ip)

    video = cv2.VideoCapture(args.video)
    fps = video.get(cv2.CAP_PROP_FPS)
    frame_delay = 1.0 / fps
    ddp = DDPDevice(ip)
    matrix_w, matrix_h = get_matrix_dimensions(ip)

    frame_count = 0
    last_frame = time.time()
    while True:
        success, image = video.read()
        if not success:
            break

        image = resize_keep_aspect_ratio(image, matrix_w, matrix_h)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

        ddp.flush(image)
        frame_count += 1

        elapsed = time.time() - last_frame
        if elapsed < frame_delay:
            time.sleep(frame_delay - elapsed)
        last_frame = time.time()


if __name__ == "__main__":
    main()
