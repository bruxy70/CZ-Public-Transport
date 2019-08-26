# Czech Public Transport

The `CZ-Public-Transport` component is a Home Assistant custom sensor that finds Public Transport connections in the Czech Republic. It uses test version of CRWS - an REST API managed by CHAPS s.r.o. The test version is unfortunately limited to limited combinations of connections - ABCz, witch is PID (Pražská Integrovaná Doprava) without trains, and trains. The full version would require client ID, but CHAPS does not provide that to public as far as I know. I did write them an email about my intention to write this sensor, but they dod not respond. 

## Table of Contents
* [Installation](#installation)
  + [Manual Installation](#manual-installation)
  + [Installation via HACS](#installation-via-hacs)
* [Configuration](#configuration)
  + [Configuration Parameters](#configuration-parameters)
* [State and Attributes](#state-and-attributes)

## Installation

### MANUAL INSTALLATION
1. Download the
   [latest release](https://github.com/bruxy70/idos/releases/latest).
2. Unpack the release and copy the `custom_components/idos` directory
   into the `custom_components` directory of your Home Assistant
   installation.
3. Configure the `idos` sensor.
4. Restart Home Assistant.

### INSTALLATION VIA HACS
1. Ensure that [HACS](https://custom-components.github.io/hacs/) is installed.
2. Search for and install the "idos" integration.
3. Configure the `idos` sensor.
4. Restart Home Assistant.

## Configuration
Add `idos` sensor in your `configuration.yaml` as per the example below:
```yaml
# Example configuration.yaml entry
sensor:
  - platform: idos
    name: cernosice_florenc
    origin: "Cernosice, zel.zast."
    destination: "Florenc"
```

### CONFIGURATION PARAMETERS
| Attribute | Optional | Description
|:---------|-----------|-----------
| `platform` | No | `idos`
| `name` | Yes | Sensor friendly name. **Default**: idos
| `origin` | No | Name of the originating bus stop
| `destination` | No | Name of the destination bus stop
| `combination_id` | Yes | Name of the combination of connections. **Default**: `ABCz`
| `user_id` | Yes | ...if you have one (if you do, please let me know where you got it. Thanks!). Otherwise it will use the trial account. 

## STATE AND ATTRIBUTES
### State
The next connection short description in format *time (bus line)*. If there are line changes to be made, the status will only show the first connection (see attribute description for the complete plan)

### Attributes
| Attribute | Description
|:---------|-----------
| `departure` | Departure time
| `connections` | List of the connections to take (or simply line number if this is a direct connection)
| `duration` | Trip duration
| `description` | Full description of the plan - each connection on one line, in the format *line time (bus stop to get-in) -> time (bus stop to get-off)*

---
<a href="https://www.buymeacoffee.com/3nXx0bJDP" target="_blank"><img src="https://bmc-cdn.nyc3.digitaloceanspaces.com/BMC-button-images/custom_images/orange_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
