import requests
from PIL import Image
import numpy as np
import os
import time


url = "http://wled-timo.local/json"


def get_state():
    response = requests.get(url)
    print(response.status_code)
    print(response.text)


def set_state(pixels):
    data = {
        "seg": {
            "i": pixels,
            "start": 0,
            "stop": 16,
            "startY": 0,
            "stopY": 16,
            "bri": 20,
        }
    }

    requests.post(url, json=data)


def image_to_hex_arr(path):
    img = Image.open(path)

    numpydata = np.asarray(img)

    # reshape to 2D array
    numpydata = numpydata.reshape(-1, 3)
    pixels = []
    for pixel in numpydata:
        # convert RGB to Hex
        pixels.append("{:02x}{:02x}{:02x}".format(pixel[0], pixel[1], pixel[2]))
    return pixels


def frames_to_wled(framefolder, target_fps=30):
    frames = []
    for filename in os.listdir(framefolder):
        frames.append(image_to_hex_arr(framefolder + "/" + filename))
        print(filename)

    last_60_frametimes = []
    previous_time = time.time()
    framecount = 0
    skipper = 4
    skipper_max = 10
    while True:
        for frame in frames:
            framecount += 1
            if framecount % skipper == 0:
                set_state(frame)
            current_time = time.time()
            if len(last_60_frametimes) > 120:
                last_60_frametimes.pop(0)
            last_60_frametimes.append(current_time - previous_time)

            average_fps = 1 / np.average(last_60_frametimes)

            if framecount % 240 == 0:
                print(
                    "Average FPS: "
                    + str(average_fps)
                    + " Target FPS: "
                    + str(target_fps)
                    + " Skipper: "
                    + str(skipper)
                )
                if average_fps < target_fps - 2:
                    if skipper < skipper_max:
                        skipper += 1
                elif average_fps > target_fps + 2:
                    if skipper > 1:
                        skipper -= 1

            previous_time = current_time
