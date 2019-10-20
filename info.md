[![hacs_badge](https://img.shields.io/badge/HACS-Default-orange.svg)](https://github.com/custom-components/hacs) [![CZ-Public-Transport](https://img.shields.io/github/v/release/bruxy70/CZ-Public-Transport.svg?1)](https://github.com/bruxy70/CZ-Public-Transport) ![Maintenance](https://img.shields.io/maintenance/yes/2019.svg)

[![Buy me a coffee](https://img.shields.io/static/v1.svg?label=Buy%20me%20a%20coffee&message=🥨&color=black&logo=buy%20me%20a%20coffee&logoColor=white&labelColor=6f4e37)](https://www.buymeacoffee.com/3nXx0bJDP)

# Czech Public Transport

The `CZ-Public-Transport` component is a Home Assistant custom sensor that finds Public Transport connections in the Czech Republic. It uses test version of CRWS - an REST API managed by CHAPS s.r.o. The test version is unfortunately limited to limited combinations of connections - ABCz, witch is PID (Pražská Integrovaná Doprava) without trains. The full version would require client ID, but CHAPS does not provide that to public as far as I know. I did write them an email about my intention to write this sensor, but they did not respond.

<img src="https://github.com/bruxy70/CZ-Public-Transport/blob/master/images/overview.png">
Overview (using standard picture-elements card - with the table in background image)


<img src="https://github.com/bruxy70/CZ-Public-Transport/blob/master/images/connection.png">
Connection detail (using markdown custom card, displayed as popup-card)


## Configuration
There are 2 ways to configure the integration:
1. Using *Config Flow*: in `Configuration/Integrations` click on the `+` button, select `CZ Public Transport` and configure the sensor (prefered). If you configure the integration using Config Flow, you can change the entity_name, name and change the sensor parameters from the Integrations configuration. The changes are instant and do not require HA restart.
2. Using *YAML*: Add `cz_pub_tran` sensor in your `configuration.yaml` as per the example below:

Or you can use combination of both. The configuration of `user_id`, `detail_format`, `scan_interval` and `force_refresh_period` is currently possible only in *YAML*. To configure these, only add these paramaters and no `sensors` configuration, then configure sensors using Home Assistant GUI.

```yaml
# Simple example configuration.yaml
cz_pub_tran:
  sensors:
    - origin: "Zbraslavské náměstí"
      destination: "Poliklinika Barrandov"
    - origin: "Cernosice, zel.zast."
      destination: "Florenc"

```

For more detailed configuration please look at the <a href="https://github.com/bruxy70/CZ-Public-Transport/blob/master/README.md">README.md</a>

## STATE AND ATTRIBUTES
### STATE
The next connection short description in format *time (bus line)*. If there are line changes to be made, the status will only show the first connection (see attribute description for the complete plan)

### ATTRIBUTES
| Attribute | Description
|:---------|-----------
| `departure` | Departure time
| `line` | Bus line (1st one if there are more connections - for more look in the description)
| `connections` | List of the connections to take (or simply line number if this is a direct connection)
| `duration` | Trip duration
| `delay` | Dlayed connections (including the line number and the delay)
| `description` | Full description of the connections - each connection on 1 line, in the format<br/>*line time (bus stop to get-in) -> time (bus stop to get-off)   (!!! delay if applicable)*,<br/>or as a HTML table
| `detail` | A list of 2 connections. Each connection is a dictionary of values (see the example at the end of <a href="https://github.com/bruxy70/CZ-Public-Transport/blob/master/README.md">README.md</a>)

## SERVICE sensor.set_start_time
Set the time to start searching for connections - see <a href="https://github.com/bruxy70/CZ-Public-Transport/blob/master/README.md">README.md</a>) for details
