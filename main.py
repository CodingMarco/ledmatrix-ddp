import argparse
import cv2
import time

from ddp import DDPDevice


def main():
    parser = argparse.ArgumentParser(description="Play video on DDP")
    parser.add_argument("video", help="Path to video file")
    parser.add_argument("ip", help="IP address of DDP")
    args = parser.parse_args()

    vidcap = cv2.VideoCapture(args.video)
    ddp = DDPDevice(args.ip)

    frame_count = 0
    last_frame = time.time()
    while True:
        success, image = vidcap.read()
        if not success:
            break

        ddp.flush(image / 255.0 * 80)
        frame_count += 1

        # Limit to 25fps
        now = time.time()
        elapsed = now - last_frame
        if elapsed < 1 / 25:
            time.sleep(1 / 25 - elapsed)
        last_frame = time.time()


if __name__ == "__main__":
    main()
