#include <WiFi.h>
#include <AsyncTCP.h>
#include <ESPAsyncWebServer.h>

//#define BT
#ifdef BT
    #include "BluetoothSerial.h"
    BluetoothSerial SerialBT;
#endif

#if !defined(CONFIG_BT_ENABLED) || !defined(CONFIG_BLUEDROID_ENABLED)
#error Bluetooth is not enabled! Please run `make menuconfig` to and enable it
#endif


// Replace with your network credentials
const char* ssid = "";
const char* password = "";

bool ledState = 0;
const int ledPin = 2;

AsyncWebServer server(80);
AsyncWebSocket ws("/ws");
int numClients = 0;
int latestID = 0;

const char start_html[] PROGMEM = R"rawliteral(
<!DOCTYPE HTML><html>
<head>
  <title>ESP Web Server</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="data:,">
  <style>
  html {
    font-family: Arial, Helvetica, sans-serif;
    text-align: center;

  </style>
<title>ESP Web Server</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="icon" href="data:,">
</head>
<body>
  <div class="topnav">
    <h1>ESP WebSocket Server</h1>
  </div>
  <div class="content">
    <div class="card">
      <h2>Output - GPIO 2</h2>
      <p class="state">state: <span id="state">%STATE%</span></p>
      <p><button id="button" class="button">Toggle</button></p>
    </div>
  </div>
<script>
  var gateway = `ws://${window.location.hostname}/ws`;
  var websocket;
  window.addEventListener('load', onLoad);
  function initWebSocket() {
    console.log('Trying to open a WebSocket connection...');
    websocket = new WebSocket(gateway);
    websocket.onopen    = onOpen;
    websocket.onclose   = onClose;
    websocket.onmessage = onMessage; // <-- add this line
  }
  function onOpen(event) {
    console.log('Connection opened');
  }
  function onClose(event) {
    console.log('Connection closed');
    setTimeout(initWebSocket, 2000);
  }
  function onMessage(event) {
    var state;
    if (event.data == "1"){
      state = "ON";
    }
    else{
      state = "OFF";
    }
    document.getElementById('state').innerHTML = state;
  }
  function onLoad(event) {
    initWebSocket();
    initButton();
  }
  function initButton() {
    document.getElementById('button').addEventListener('click', toggle);
  }
  function toggle(){
    websocket.send('toggle');
  }
</script>
</body>
</html>
)rawliteral";


void flash(){
    digitalWrite(2, HIGH);
    delay(8);
    digitalWrite(2, LOW);
}

void notifyClients() {
  ws.textAll(String(ledState));
}

void handleWebSocketMessage(void *arg, uint8_t *data, size_t len) {
  AwsFrameInfo *info = (AwsFrameInfo*)arg;
  if (info->final && info->index == 0 && info->len == len && info->opcode == WS_TEXT) {
    data[len] = 0;
    
    //Serial.println((char*)data);
    if (strcmp((char*)data, "1") == 0) {
      digitalWrite(2, HIGH);
    } else{
        digitalWrite(2, LOW);
    }
  }
}

void onEvent(AsyncWebSocket *server, AsyncWebSocketClient *client, AwsEventType type,
             void *arg, uint8_t *data, size_t len) {
  uint8_t id = client->id();        
  switch (type) {
    case WS_EVT_CONNECT:
      Serial.printf("WebSocket client #%u connected from %s\n", id, client->remoteIP().toString().c_str());
      numClients +=1;
      latestID = id;
      Serial.print("numClients ");
      Serial.println(numClients);
      break;
    case WS_EVT_DISCONNECT:
      Serial.printf("WebSocket client #%u disconnected\n", client->id());
      numClients -=1;
      if(numClients <0){
        numClients = 0;
      }
      Serial.print("numClients ");
      Serial.println(numClients);
      break;
    case WS_EVT_DATA:
      handleWebSocketMessage(arg, data, len);
      break;
    case WS_EVT_PONG:
    case WS_EVT_ERROR:
      break;
  }
}

void initWebSocket() {
  ws.onEvent(onEvent);
  server.addHandler(&ws);
}

String processor(const String& var){
  //Serial.println(var);
  if(var == "STATE"){
    if (ledState){
      return "ON";
    }
    else{
      return "OFF";
    }
  }
  return String();
}

void setup() {
    pinMode(2, OUTPUT);
    Serial.begin(115200);
    #ifdef BT
        SerialBT.begin("ESP32test"); //Bluetooth device name
        Serial.println("The device started, now you can pair it with bluetooth!");
    #endif
    
    // Connect to Wi-Fi
    WiFi.begin(ssid, password);
    Serial.print("Connecting to WiFi..");
    int errCount = 0;
    while (WiFi.status() != WL_CONNECTED) {
        delay(500);
        Serial.print(".");
        errCount +=1;
        if(errCount > 5){
          ESP.restart();
        }
    }

    // Print ESP Local IP Address
    Serial.println(WiFi.localIP());
    Serial.println(WiFi.RSSI());

    initWebSocket();

    // Route for root / web page
    server.on("/", HTTP_GET, [](AsyncWebServerRequest *request){
        request->send_P(200, "text/html", start_html, processor);
    });
    server.begin();   
}



void loop() {

  #ifdef BT
      if (SerialBT.available()) {
          SerialBT.println("got BT serial");
          int val = SerialBT.read();   
          if(val == 13 || val == 10){
              return;
          }

          if (val >= 49){
              flash();
          }
          else {
          digitalWrite(2, LOW);
          }


          Serial.println(val);
          return;
      }
  #endif

  if(latestID >5){
    ESP.restart();
  }

  ws.cleanupClients(1);
  
  delay(20);
}