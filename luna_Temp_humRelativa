

//https://hifisac.com/shop/am2302-dht22-sensor-de-humedad-y-temperatura-asair-para-arduino-813#attr=
//Sensor de Temperatura Color Blanco DHT
#include <DHT.h>
#include <DHT_U.h>
#include "DHT.h"
#define DHTPIN 2     // Pin digital conectado al sensor DHT22
#define DHTTYPE DHT22   // Definir el tipo de sensor DHT
DHT dht(DHTPIN, DHTTYPE);
void setup() {
  Serial.begin(9600);
  dht.begin();
}
void loop() {
  delay(2000);  // Esperar 2 segundos entre lecturas
  float humedad = dht.readHumidity();
  float temperaturaC = dht.readTemperature();
  float temperaturaF = dht.readTemperature(true);

  if (isnan(humedad) || isnan(temperaturaC) || isnan(temperaturaF)) {
    Serial.println("¡Error al leer del sensor DHT!");
    return;
  }
  Serial.print("Humedad: ");
  Serial.print(humedad);
  Serial.print(" %\t");
  Serial.print("Temperatura: ");
  Serial.print(temperaturaC);
  Serial.print(" °C ");
  Serial.print(temperaturaF);
  Serial.println(" °F");
  
}
