# Beat plug
#### Analyse system audio and send beats to a microcontroller over websocket
This project consists of two parts, a server side program that listens to system audio and a client that runs on a microcontroller and recieves instructions. 
The Beatplug is super-fast even though it uses Wi-Fi thanks to websockets and the use of a solid state relay.

The time taken to analyse audio, send it over the network and physically switch the relay is about the time it takes for a DAC to convert the system audio for playback.

## Parts list
Hardware
* Beatplug, consisting of
  * ESP32 (any variant)
  * Solid state relay (SSR) capable of switching 220V AC
  * A Smart plug. (This is a useful starter as it already has male pins and a female socket to plug a lamp into)
* Windows PC (at this time. I need to solve real-time system audio listening on Mac)

Software
* ESP32 firmware in C
* Audio analysis in Python
* https://vac.muzychenko.net/en/download.htm (Windows) (There may also be alternative ways to create virtual routing)
* ASIO 4all (for use with DJ decks e.g via Traktor)

## Setup
### Hardware
#### Making the beatplug
This part is the most important and most janky.
1. Open up the smart plug and solder some reasonably thick wire to the live and neutral pins
2. Securely attach the live and neutral wires into the SSR
3. Connect Pin 2 and negative pin to the SSR


### Software
#### ESP 32 setup
1. Change Wi-Fi details in Listener code 
2. Flash Listener firmware to the ESP32

#### Windows setup
Virtual audio cables are required to route sound to this program and also to speakers. This is because this code requires an input device but we want to monitor the audio of an output device
1. Once vac is installed, create a virtual cable. It should be called "Line 1" by default
1. In windows sound settings (You can pull this up via Win+R and enter mmsys.cpl). Set default output to Line1
1. Listen to Line1 output with real audio output device. (In the sound settings go to recording devices, right click > properties, click listen tab) Don't listen with the default device! Select the actual output device


#### Traktor setup
1. Use VAC control panel to create an additional virtual cable
1. Set traktor to use ASIO 4 ALL for audio output
1. Enable both Virtual cables in ASIO4ALL settings
1. in traktor in audio settings set master output to Line 1 and monitor/cue to Line 2
1. In windows sound settings listen to Line2 out of the traktor controller


## Operating
1. Plug in the beat plug and provide power to the ESP
1. Set esp ip address in visualise.py and run the file


## Extra steps
* It can help to assign a static ip to the ESP