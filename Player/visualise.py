import time
from numpy import average
# from serial import SerialTimeoutException, SerialException
from stream_analyzer import Stream_Analyzer
import websocket

from textual.app import App, ComposeResult, RenderResult
from textual.widgets import Footer, Header
from textual.widgets import Static
from textual.reactive import reactive
from textual.content import Content

BASS_DEFAULT_THRESH = 100

DEFAULT_IP = "192.168.188.160"
DEFAULT_DEVICE_NAME = "Line 1"


# def listener_loop():
#     print("Initalising audio listener")
#     ear = Stream_Analyzer(
#         device="Line 1",
#         rate=None,  # Audio samplerate, None uses the default source settings
#         FFT_window_size_ms=80,  # Window size used for the FFT transform
#         updates_per_second=2000,  # How often to read the audio stream for new data
#         smoothing_length_ms=100,  # Apply some temporal smoothing to reduce noisy features
#         n_frequency_bins=100,  # The FFT features are grouped in bins
#         visualize=1,  # Visualize the FFT features with PyGame
#         verbose=0  # Print running statistics (latency, fps, ...)
#     )
#
#     while True:
#         try:
#             print("Connecting websocket.....")
#             websocket_url = "ws://192.168.188.160/ws"
#             ws = websocket.WebSocket()
#             ws.connect(websocket_url)
#             ws.send("hello")
#             while not ws.connected:
#                 time.sleep(0.2)
#                 print(".")
#             print("Connected")
#
#             fps = 100  # How often to update the FFT features + display
#             last_update = time.time()
#             last_bass_avg = 0
#             while True:
#                 if (time.time() - last_update) > (1. / fps):
#                     last_update = time.time()
#                     raw_fftx, raw_fft, binned_fftx, binned_fft = ear.get_audio_features()
#                     # print( binned_fftx)
#                     # print(binned_fft[1:4])
#                     # print(average(binned_fftx))
#                     # print(average(binned_fft))
#                     bass_avg = average(binned_fft[1:8])
#                     try:
#                         bass_diff = last_bass_avg - bass_avg
#                         # print(bass_diff)
#
#                         if bass_avg > bass_threshold:  # and bass_diff > 0:
#                             ws.send("1")
#                             # time.sleep(2 / 1000)
#                             print("1")
#                         else:
#                             ws.send("0")
#                             print("0")
#                     except Exception:
#                         pass
#                     last_bass_avg = bass_avg
#         except (
#                 ConnectionResetError, TimeoutError,
#                 OSError) as e:  ## recover from websocket fails and OSError (e.g sleep mode)
#             print(e)
#             print("crashed")


class Bass_thresh_widget(Static):
    pass


class Curr_Bass_widget(Static):
    pass


class Output_widget(Static):
    pass


class BeatPlugServer(App):
    """A Textual app to manage stopwatches."""

    BINDINGS = [("d", "toggle_dark", "Toggle dark mode"),
                ("[", "lower_thresh", "lower bass threshold"),
                ("]", "raise_thresh", "raise bass threshold")
                ]

    bass_threshold: reactive[int] = reactive(BASS_DEFAULT_THRESH)
    current_bass: reactive[int] = reactive(0)

    past_bass_vals = []

    # def watch_current_bass(self) -> None:
    #     self.query_one(Curr_Bass_widget).update(f"Current bass: {self.current_bass}")

    def watch_bass_threshold(self) -> None:
        self.query_one(Bass_thresh_widget).update(f"bass threshold: {self.bass_threshold}")

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.theme = (
            "textual-dark" if self.theme == "textual-light" else "textual-light"
        )

    def action_lower_thresh(self):
        self.bass_threshold = int(self.bass_threshold) - 5

    def action_raise_thresh(self):
        self.bass_threshold = int(self.bass_threshold) + 5

    def createwebsocket(self):
        print("Connecting websocket.....")
        websocket_url = f"ws://{DEFAULT_IP}/ws"
        self.ws = websocket.WebSocket()
        self.ws.connect(websocket_url)
        self.ws.send("hello")
        while not self.ws.connected:
            time.sleep(0.2)
            print(".")
        print("Connected")

    def create_listener(self):
        self.ear = Stream_Analyzer(
            device=DEFAULT_DEVICE_NAME,
            rate=None,  # Audio samplerate, None uses the default source settings
            FFT_window_size_ms=80,  # Window size used for the FFT transform
            updates_per_second=2000,  # How often to read the audio stream for new data
            smoothing_length_ms=100,  # Apply some temporal smoothing to reduce noisy features
            n_frequency_bins=100,  # The FFT features are grouped in bins
            visualize=1,  # Visualize the FFT features with PyGame
            verbose=0  # Print running statistics (latency, fps, ...)
        )

    def on_mount(self):
        """Event handler called when widget is added to the app."""
        self.create_listener()
        self.createwebsocket()
        self.set_interval(1 / 200, self.main_loop_next_frame)
        self.set_interval(1 / 50, self.update_current_bass)
        self.action_raise_thresh()

    def update_current_bass(self):
        self.query_one(Curr_Bass_widget).update(
            Content(f"Current bass: {int(self.current_bass)}, {[int(x) for x in self.past_bass_vals[:20]]}"))

    def main_loop_next_frame(self):
        if not self.ws or not self.ear:
            return
        try:
            last_update = time.time()
            raw_fftx, raw_fft, binned_fftx, binned_fft = self.ear.get_audio_features()
            # print( binned_fftx)
            # print(binned_fft[1:4])
            # print(average(binned_fftx))
            # print(average(binned_fft))
            bass_avg = average(binned_fft[1:8])
            try:
                # bass_diff = last_bass_avg - bass_avg
                # print(bass_diff)
                self.current_bass = bass_avg
                self.past_bass_vals.append(bass_avg)
                if len(self.past_bass_vals) > 200:
                    self.past_bass_vals.pop(0)
                if bass_avg > self.bass_threshold:  # and bass_diff > 0:
                    self.ws.send("1")
                    self.query_one(Output_widget).update(f"Output: 1")
                    print("1")
                else:
                    self.ws.send("0")
                    self.query_one(Output_widget).update(f"Output: 0")
            except Exception:
                pass
            last_bass_avg = bass_avg
        except (ConnectionResetError, TimeoutError,
                OSError) as e:  ## recover from websocket fails and OSError (e.g sleep mode)
            print(e)
            print("crashed")
            self.createwebsocket()

    def compose(self) -> ComposeResult:
        """Create child widgets for the app."""
        yield Header()
        yield Footer()
        yield Bass_thresh_widget()
        yield Curr_Bass_widget()
        yield Output_widget()


if __name__ == "__main__":
    app = BeatPlugServer()
    app.run()
