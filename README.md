# Raspberry Pi LED Controller

This application controls addressable LED strips (WS2812B/NeoPixel) on a Raspberry Pi using Python and `rpi_ws281x`.

## Wiring

**Default Configuration:**
*   **VCC** -> 5V External Power Supply (Do not power long strips from the Pi directly!)
*   **GND** -> Common Ground (Connect to Power Supply GND **AND** Pi Pin 6/GND)
*   **DATA** -> **GPIO 18 (Physical Pin 12)**

*Note: GPIO 18 is the standard pin for PWM LED control.*


## Installation

### Option 1: Install via Git (Recommended)

1.  **SSH into your Raspberry Pi**.
2.  **Clone the repository** (replace URL with your GitHub repo URL):
    ```bash
    git clone https://github.com/YOUR_USERNAME/led_controller.git
    cd led_controller
    ```
3.  **Run the installer**:
    ```bash
    chmod +x install.sh
    ./install.sh
    ```

### Option 2: Manual Transfer (SCP)
If you don't use GitHub, you can copy files directly from your computer:
```powershell
scp -r "c:\Users\choog\.gemini\New folder\led_controller" pi@<pi-ip-address>:/home/pi/
```
    - Install necessary Python dependencies.
    - Set up the systemd service.
    - Start the LED controller.

## Configuration

Edit `/home/pi/led_controller/config.json` to change settings:

```json
{
    "LED_COUNT": 50,      // Number of LEDs
    "LED_PIN": 18,        // GPIO Pin (Recommended: 18)
    "LED_BRIGHTNESS": 255 // 0-255
}
```

After changing config, restart the service:
```bash
sudo systemctl restart led-controller
```

## Web Interface

Access the controller at:
`http://<your-pi-ip>:5000`

## Bluetooth Control (Blue Dot)

1.  **Download App**: Install **Blue Dot** by *Martin O'Hanlon* from the App Store or Play Store.
2.  **Pairing**:
    -   Go to your phone's Bluetooth settings.
    -   Pair with your Raspberry Pi (usually named `raspberrypi`).
3.  **Connect**:
    -   Open the Blue Dot app.
    -   Select your Pi from the list.
4.  **Controls**:
    -   **Tap Center**: Toggle On/Off.
    -   **Double Tap**: Next Pattern.
    -   **Touch & Drag**: Change Color (Position determines color).

## Logs

View the logs to see what the application is doing:
```bash
journalctl -u led-controller -f
```
