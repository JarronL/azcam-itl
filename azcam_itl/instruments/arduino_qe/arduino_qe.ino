/* 
LAST MODIFIED: 25mar24 - MPL

This program receives commands from a ethernet connection to control 
LEDs and Fe55 output on an Arduino UNO board.
*/

#include <SPI.h>
#include <Ethernet.h>

// Initialize global variables
int pinNum = 0; // pin number
int i = 0; // loop variable for blinking
int shutterInput = 3;  // shutter input signal
String ledstring = "NFFFFFFN";  // first char here is pin 2
String ledstate =  "NFFFFFFN";  // default state - UV pin 9
int shutterMode;  // shutter mode flag

// mac and IP address for Arduino
byte mac[] = {
  0xDE, 0xAD, 0xBE, 0xEF, 0xFE, 0xEF
};
//IPAddress ip(10, 131, 0, 27);
IPAddress ip(10, 0, 2, 50);
//IPAddress myDns(10, 0, 0, 10);
//IPAddress gateway(10, 0, 0, 1);
//IPAddress subnet(255, 255, 255, 128);
IPAddress subnet(255, 255, 255, 0);

byte byteRead;

// port 80 default
EthernetServer server(80);

//------------------------------------------------------------------------------------
void setup() {
  // Called once on reset

  // Arduino resets when serial connection is established on Windows
  delay(10); // 10 ms delay;
  
  // define, declare output pins
  pinMode(9, OUTPUT); // Oriel Shutter
  pinMode(8, OUTPUT); // IR
  pinMode(7, OUTPUT); // red
  pinMode(6, OUTPUT); // orange
  pinMode(5, OUTPUT); // green
  pinMode(4, OUTPUT); // violet
  pinMode(3, INPUT);  // shutter input
  pinMode(2, OUTPUT); // fe55

  // serial port (USB) connection for monitor/debug
  Serial.begin(9600);
  while (!Serial) {
    ; // wait for serial port to connect. Needed for native USB port only
  }
  
  // initialize ethernet device
  Ethernet.begin(mac, ip);
  server.begin();
 
  Serial.println("Hi from the arduino_qb!");
  Serial.print("Server is listening at ");
  Serial.println(Ethernet.localIP());

  // start in shutterMode, default LED state
  shutterMode = 1;
  writeState(ledstate);

} // end setup

//------------------------------------------------------------------------------------
void pinCmd(int pinNum, char state) {
// turn LEDs/Fe55 on or off according to code
  if (state == 'F'){
    digitalWrite(pinNum, LOW);
  }
  if (state == 'N') {
    digitalWrite(pinNum, HIGH);
  }
}

//------------------------------------------------------------------------------------
void writeState(String codestring) {
  char c;
  for (int i=0; i < 8; i++) {
    c = codestring.charAt(i);
    pinCmd(2+i, c);
  }
}

//------------------------------------------------------------------------------------
void loop() {

  char c;
  int val = 0;

  // listen for client
  EthernetClient client = server.available();
  //Serial.print("Ethernet client");
  //Serial.println(client);
  
  // check for incoming command
  // called only if connection is made
  if (client) {
    
    c = client.read();
    Serial.print(c);

    // command is: Sxxxxxxxx to enter shutter mode
    if (c == 'S') {
      shutterMode = 1;

      // read next 8 chars
      ledstring = "";
      for (int i=1; i <= 8; i++) {
         c = client.read();
         ledstring = ledstring + c;
      }
      Serial.print("Shutter mode: ");
      writeState(ledstring);
      Serial.println(ledstring);
    }
    
    //  command is: Cxxxxxxxx to set all LED states
    else if (c == 'C') {
      shutterMode = 0;

      //String ledstring;  // reset ledstring

      // read next 8 chars
      ledstring = "";
      for (int i=1; i <= 8; i++) {
         c = client.read();
         ledstring = ledstring + c;
      }
      Serial.print("Control mode: ");
      writeState(ledstring);
      Serial.println(ledstring);
      
    }
    
  } // end client

  // echo anything from serial port for debug
  if(Serial.available( )) {
    byteRead = Serial.read();
    Serial.write(byteRead);
  }

  // check shutter mode on every loop iteration
  if (shutterMode == 1) {
    
     // read the shutter signal
     val = digitalRead(shutterInput);  // read the input
     //Serial.println(val);

     if (val == 1) {
      //Serial.println("Shutter HIGH (not active): ");
      writeState("NFFFFFFN");
      //writeState(ledstring);
      //Serial.println(ledstring);
     }
     else if (val == 0) {
      //Serial.println("Shutter LOW (active): ");
      writeState("NFFFFFFF");
      //Serial.println(ledstring);
     }
   }
   
   delay(10);
  
} // end main loop
