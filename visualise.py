import sys
import time
from numpy import average
from serial import SerialTimeoutException, SerialException
from stream_analyzer import Stream_Analyzer
import websocket
from pynput import keyboard

print("Initalising audio listener")

bass_threshold = 60
show_all_vals = False


def on_press(key):
    global bass_threshold, show_all_vals
    if key == keyboard.Key.esc:
        return False  # stop listener
    try:
        k = key.char  # single-char keys
    except:
        k = key.name  # other keys
    if k in ['[', ']', "space"]:  # keys of interest
        # self.keys.append(k)  # store it in global-like variable
        # print('Key pressed: ' + k)
        match k:
            case "]":
                bass_threshold += 5
                print("bass thresh", bass_threshold)
            case "[":
                bass_threshold -= 5
                print("bass thresh", bass_threshold)
            case "space":
                show_all_vals = not show_all_vals
                print("debug on" if show_all_vals else "debug off")


listener = keyboard.Listener(on_press=on_press)
listener.start()  # start to listen on a separate thread

ear = Stream_Analyzer(
    device="Line 1",
    rate=None,  # Audio samplerate, None uses the default source settings
    FFT_window_size_ms=80,  # Window size used for the FFT transform
    updates_per_second=2000,  # How often to read the audio stream for new data
    smoothing_length_ms=100,  # Apply some temporal smoothing to reduce noisy features
    n_frequency_bins=100,  # The FFT features are grouped in bins
    visualize=1,  # Visualize the FFT features with PyGame
    verbose=0  # Print running statistics (latency, fps, ...)
)

while True:
    try:
        print("Connecting websocket.....")
        websocket_url = "ws://192.168.188.60/ws"
        ws = websocket.WebSocket()
        ws.connect(websocket_url)
        ws.send("hello")
        while not ws.connected:
            time.sleep(0.2)
            print(".")
        print("Connected")

        fps = 100  # How often to update the FFT features + display
        last_update = time.time()
        last_bass_avg = 0
        while True:
            if (time.time() - last_update) > (1. / fps):
                last_update = time.time()
                raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
                # print( binned_fftx)
                # print(binned_fft[1:4])
                # print(average(binned_fftx))
                # print(average(binned_fft))
                bass_avg = average(binned_fft[1:8])
                try:
                    bass_diff = last_bass_avg - bass_avg
                    # print(bass_diff)
                    # sys.stdout.write("Download progress: %d%%   \r" % (bass_diff))
                    # sys.stdout.flush()
                    if show_all_vals: print(bass_avg)
                    if bass_avg > bass_threshold:  # and bass_diff > 0:
                        ws.send("1")
                        # time.sleep(2 / 1000)
                        # print("1")
                    else:
                        ws.send("0")
                        # print("0")
                except SerialTimeoutException:
                    pass
                except SerialException:
                    pass
                last_bass_avg = bass_avg
    except (ConnectionResetError, TimeoutError) as e:
        print(e)
        print("crashed")
