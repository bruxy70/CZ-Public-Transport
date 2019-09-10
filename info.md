# Czech Public Transport

The `CZ-Public-Transport` component is a Home Assistant custom sensor that finds Public Transport connections in the Czech Republic. It uses test version of CRWS - an REST API managed by CHAPS s.r.o. The test version is unfortunately limited to limited combinations of connections - ABCz, witch is PID (Pražská Integrovaná Doprava) without trains. The full version would require client ID, but CHAPS does not provide that to public as far as I know. I did write them an email about my intention to write this sensor, but they did not respond.

<img src="https://github.com/bruxy70/CZ-Public-Transport/blob/master/images/overview.png">
Overview (using standard picture-elements card - with the table in background image)


<img src="https://github.com/bruxy70/CZ-Public-Transport/blob/master/images/connection.png">
Connection detail (using markdown custom card, displayed as popup-card)


## Configuration
Add `cz_pub_tran` sensor in your `configuration.yaml` as per the example below:
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

### CONFIGURATION PARAMETERS
| Attribute | Optional | Description
|:---------|-----------|-----------
| `cz_pub_tran` | No | This is the platform name
| `user_id` | Yes | ...if you have one (if you do, please let me know where you got it. Thanks!). Otherwise it will use the trial account. 
| `scan_interval` | Yes | The sensor refresh rate (seconds)<br/>**Default**: 60
| `force_refresh_period` | Yes | The sensor will skip update if there is already scheduled connection. But, every n-th refresh, it will force the update, to check delay changes. This can be disabled by setting this to 0.<br/>**Default**: 5  **Range**: 0-60
| `description_format` | Yes | The **description** attribute can be rendered in 2 different formats:<br/>- **text**: plain text, each connection on 1 line (**default**)<br/>- **HTML**: HTML table
| `name` | Yes | Sensor friendly name.<br/>**Default**: cz_pub_tran
| `origin` | No | Name of the originating bus stop
| `destination` | No | Name of the destination bus stop
| `combination_id` | Yes | Name of the combination of timetables.<br/>**Default**: `ABCz`

## STATE AND ATTRIBUTES
### State
The next connection short description in format *time (bus line)*. If there are line changes to be made, the status will only show the first connection (see attribute description for the complete plan)

### Attributes
| Attribute | Description
|:---------|-----------
| `departure` | Departure time
| `line` | Bus line (1st one if there are more connections - for more look in the description)
| `connections` | List of the connections to take (or simply line number if this is a direct connection)
| `duration` | Trip duration
| `delay` | Dlayed connections (including the line number and the delay)
| `description` | Full description of the connections - each connection on 1 line, in the format<br/>*line time (bus stop to get-in) -> time (bus stop to get-off)   (!!! delay if applicable)*,<br/>or as a HTML table
| `detail` | A list of 2 connections. Each connection is a dictionary of values (see the example at the end of <a href="https://github.com/bruxy70/CZ-Public-Transport/blob/master/README.md">README.md</a>)

---
<a href="https://www.buymeacoffee.com/3nXx0bJDP" target="_blank"><img src="https://www.buymeacoffee.com/assets/img/custom_images/white_img.png" alt="Buy Me A Coffee" style="height: auto !important;width: auto !important;" ></a>
