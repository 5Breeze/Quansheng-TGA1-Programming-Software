# Quansheng-TGA1-Programming-Software
This Python program is designed for interacting with Quansheng TGA1 firmware via a serial port. The software enables reading and writing configurations, specifically for 16 communication channels, including frequency settings, CTCSS codes, and features like busy lock, encryption, and frequency hopping.

Here's a user manual for the program in Markdown format:

---

# Configuration Reader and Writer User Manual

This guide provides detailed instructions on how to use the Configuration Reader and Writer program for reading and writing device configurations through a serial port.

## Table of Contents

- [Introduction](#introduction)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Launching the Application](#launching-the-application)
- [Main Interface](#main-interface)
  - [Select Serial Port](#select-serial-port)
  - [Channel Configuration](#channel-configuration)
  - [Buttons](#buttons)
- [Reading Configuration](#reading-configuration)
- [Writing Configuration](#writing-configuration)
- [Error Handling](#error-handling)
- [Troubleshooting](#troubleshooting)
- [Debugging](#debugging)
- [Appendix](#appendix)

## Introduction

This program allows you to read and write configuration settings to a device via a serial port. The configurations include receive and transmit frequencies, CTCSS codes, and various control settings like busy lock, encryption, and frequency hopping.

## Getting Started

### Prerequisites

- Ensure Python is installed on your system.
- Install the necessary Python libraries using the following commands:

  ```sh
  pip install pyserial
  pip install tk
  ```

- Connect the device to your computer via a serial port.

### Launching the Application

Run the Python script in your environment. The application window will appear, allowing you to interact with the device's configuration.

## Main Interface

### Select Serial Port

- **Select Serial Port:**  
  Use the dropdown menu to select the appropriate serial port connected to your device.

### Channel Configuration

The interface provides options to configure up to 16 channels. For each channel, you can set the following:

- **Recv Frequency (MHz):**  
  The receiving frequency in MHz.
- **Recv CTCSS:**  
  The Continuous Tone-Coded Squelch System (CTCSS) code for receiving.
- **Send Frequency (MHz):**  
  The transmitting frequency in MHz.
- **Send CTCSS:**  
  The Continuous Tone-Coded Squelch System (CTCSS) code for transmitting.
- **Busy Lock:**  
  A checkbox to enable or disable the busy lock feature.
- **Encryption:**  
  A checkbox to enable or disable encryption.
- **Freq Hop:**  
  A checkbox to enable or disable frequency hopping.

### Buttons

- **Read Configuration:**  
  Reads the current configuration from the device and updates the UI with the retrieved data.
  
- **Write Configuration:**  
  Writes the current settings from the UI to the device.

## Reading Configuration

1. **Select Serial Port:**  
   Choose the serial port connected to your device.

2. **Read Configuration:**  
   Click the "Read Configuration" button. The program will retrieve the configuration from the device and display it in the UI.

## Writing Configuration

1. **Select Serial Port:**  
   Choose the serial port connected to your device.

2. **Configure Channels:**  
   Modify the settings for each channel as needed using the provided fields.

3. **Write Configuration:**  
   Click the "Write Configuration" button to send the updated settings to the device.

## Error Handling

The program will display error messages in case of any issues during the read or write processes. Common errors include:

- **Failed to open serial port:**  
  Ensure the correct port is selected and that it is not in use by another application.

- **Failed to communicate with the device:**  
  Check the connection and try again.

## Troubleshooting

- **No Serial Ports Listed:**  
  Ensure the device is connected and drivers are installed.
  
- **Configuration Not Updating:**  
  Double-check that the correct port is selected and the device is properly connected.

## Debugging

Enable or disable debugging by setting the `DEBUG` variable in the script. When debugging is enabled, detailed messages will be printed to the console, helping diagnose issues.

## Appendix
Serial Communication and Data Configuration Protocol

### 1. Serial Communication Setup
- **Baud Rate**: 9600
- **Initial Sequence**:
  - Send the following hex sequence: `02 54 47 53 31 52 41 4D`
  - If no acknowledgment (`06`) is received, resend the sequence.
  - If no acknowledgment is received after a second attempt, the serial port is considered failed.
  - Upon receiving `06`, continue the process.

### 2. Data Exchange Protocol
- **Step 1: Send `02` and Expect Response**:
  - Send `02`.
  - Expect to receive: `06 00 00 00 00 00 00 00`.
  - If successful, send `06`.
  - Expect to receive: `06`.
  - Send `05`.
  - Expect to receive: `FF FF FF FF FF FF FF`.
  - Send `06` again and expect `06` as confirmation.

### 3. Configuration Reading Procedure
- **Reading Process**:
  - Send `52 00 00 0D` and read 17 bytes, which should start with `57 00`.
  - Subsequently, send `52 00 0D 0D` and read 17 bytes, again starting with `57 00`. The third byte of this data is calculated by adding 13 to the third byte of the previous data.
  - Repeat this process 18 times, until the third byte reaches `DD`.
  - These 18 sets of 17-byte data form the configuration file.

### 4. Configuration Data Interpretation
- **Data Format**:
  - Example: `57 00 00 0D 10 19 9D 02 10 19 9D 02 FF FF FF FF EA`.
  - **First Two Bytes**: Fixed.
  - **Third Byte**: Represents a sequential index.
  - **Fourth Byte**: Fixed (`0D`).
  - **Fifth to Seventh Bytes**: Reverse the order (7th, 6th, 5th) to form a 6-digit hexadecimal number.
    - Convert this hex number to decimal, subtract `6445568`, divide by `10^5`, then add 400 to get the frequency in MHz (e.g., `410.000 MHz` corresponds to `71 9C 40`).
  - **Eighth Byte**: Fixed (`02`).
  - **Ninth to Eleventh Bytes**: Similar to fifth to seventh bytes, representing the transmit frequency.
  - **Twelfth Byte**: Fixed (`02`).
  - **Thirteenth to Fourteenth Bytes**: Reverse order to determine the receive CTCSS code.
  - **Fifteenth to Sixteenth Bytes**: Same as above, but for transmit CTCSS code.
  - **Seventeenth Byte**: Controls three features: Busy Lock, Encryption, and Frequency Hopping (e.g., `EA` represents `100`, `6A` represents `101`, etc.).

### 5. Configuration Writing Procedure
- **Writing Process**:
  - Perform a read operation before writing, as the writing process depends on the read data.
  - After receiving `06` (from the read procedure), send the first set of 17-byte data.
  - Wait for acknowledgment (`06`), then proceed with the next set of data.
  - Repeat until all 18 sets of data are written.

---
### CTCSS Codes

The application supports the following CTCSS codes:

```text
67.0, 71.9, 74.4, 77.0, 79.7, 82.5, 85.4, 88.5, 91.5, 94.8,
97.4, 100.0, 103.5, 107.2, 110.9, 114.8, 118.8, 123.0, 127.3, 131.8,
136.5, 141.3, 146.2, 151.4, 156.7, 162.2, 167.9, 173.8, 179.9, 186.2,
192.8, 203.5, 210.7, 218.1, 225.7, 233.6, 241.8, 250.3, 3000
```