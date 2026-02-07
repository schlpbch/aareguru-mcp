# Aareguru API - Detailed Analysis Report

## Executive Summary

The **Aareguru API** is a public, non-commercial API that provides real-time and
historical data about the Aare river in Switzerland, including water
temperature, flow rates, weather conditions, and forecasts. The API is
maintained by Christian Studer and Aare.guru GmbH, serving the popular
[Aare.guru](https://aare.guru/) service.

**Key Characteristics:**

- **Version**: 2018 (current stable version)
- **Base URL**: `https://aareguru.existenz.ch`
- **Protocol**: HTTP/HTTPS (both supported)
- **Data Format**: JSON (with JSONP support via callback parameter)
- **CORS**: Enabled with wildcard (`*`)
- **Update Frequency**: Every 10 minutes (data arrives with 10-20 minute delay)
- **Recommended Polling**: 5 minutes
- **Cache Duration**: 2 minutes (default)
- **License**: Free for non-commercial use with attribution

---

## API Architecture

### Technology Stack

The API follows a "boring technology" philosophy for reliability:

- **Backend**: PHP
- **Storage**: Text files (flat file system)
- **Caching**: Built-in caching with 2-minute default TTL
- **Microservices**: Internal services for data aggregation

This simple stack ensures high availability and easy maintenance for a hobby
project.

---

## Data Sources

The API aggregates data from multiple authoritative sources:

| Data Type                                | Source                                                                                                        | Description                          |
| ---------------------------------------- | ------------------------------------------------------------------------------------------------------------- | ------------------------------------ |
| **Aare Measurements (Switzerland-wide)** | [BAFU (Federal Office for the Environment)](https://www.hydrodaten.admin.ch/de/)                              | Official hydrological data           |
| **Aare Measurements (Olten)**            | [TemperAare App](https://temperaare.ch)                                                                       | Community-sourced temperature data   |
| **Weather Measurements**                 | [MeteoSchweiz SwissMetNet](https://opendata.swiss/en/dataset/automatische-wetterstationen-aktuelle-messwerte) | Automatic weather stations           |
| **Weather Forecasts**                    | [Meteotest, Bern](https://meteotest.ch/wetter-api/wetterprognosen)                                            | Professional weather API (sponsored) |
| **Historical Data**                      | [Existenz.ch APIs](https://api.existenz.ch)                                                                   | Proprietary time-series data         |

---

## API Endpoints

### Current API (v2018)

#### 1. `/v2018/cities`

**Purpose**: List all available locations

**Method**: GET

**Parameters**:

- `app` (optional): Application identifier
- `version` (optional): Application version
- `values` (optional): Comma-separated field names for text extraction

**Response**: Returns all available cities with overview data

**Use Case**: Discovery endpoint to find available locations and their
identifiers

---

#### 2. `/v2018/today`

**Purpose**: Minimal current data for a specific location

**Method**: GET

**Parameters**:

- `city` (optional, default: `Bern`): Location identifier
- `app` (optional): Application identifier
- `version` (optional): Application version
- `values` (optional): Comma-separated field names

**Response**: Minimal response with current Aare temperature and text ("Spruch")

**Use Case**: Lightweight endpoint for simple integrations (e.g., IoT devices,
status displays)

**Example**:

```
https://aareguru.existenz.ch/v2018/today?city=Bern&app=my.app.ch&version=1.0.42
```

---

#### 3. `/v2018/current`

**Purpose**: Complete current data for a specific location

**Method**: GET

**Parameters**:

- `city` (optional, default: `Bern`): Location identifier
- `app` (optional): Application identifier
- `version` (optional): Application version
- `values` (optional): Comma-separated field names

**Response**: Maximum response with:

- Current measurements
- Historical data
- Forecasts
- Weather data
- Additional metadata ("Beigemüse" = side dishes)

**Use Case**: Full-featured applications requiring comprehensive data

**Example**:

```
https://aareguru.existenz.ch/v2018/current?city=Bern&app=my.app.ch&version=1.0.42
```

---

#### 4. `/v2018/widget`

**Purpose**: Current data for all locations at once

**Method**: GET

**Parameters**:

- `app` (optional): Application identifier
- `version` (optional): Application version
- `values` (optional): Comma-separated field names

**Response**: Medium-sized response with current data and forecasts for all
cities

**Use Case**: Widgets, dashboards, or applications displaying multiple locations
simultaneously

---

#### 5. `/v2018/history`

**Purpose**: Historical time-series data

**Method**: GET

**Parameters**:

- `city` (required): Location identifier
- `start` (required): Start date/time in various formats (ISO, timestamp,
  relative like "-1 day")
- `end` (required): End date/time in various formats (ISO, timestamp, "now")
- `app` (optional): Application identifier
- `version` (optional): Application version
- `values` (optional): Comma-separated field names

**Response**: Historical time series for:

- Water temperature
- Flow rate
- Air temperature

**Automatic Period Selection**: The API automatically chooses the appropriate
data granularity based on the requested time range

**Use Case**: Charts, trend analysis, historical comparisons

**Example**:

```
https://aareguru.existenz.ch/v2018/history?city=Bern&start=-7%20days&end=now&app=my.app.ch&version=1.0
```

---

### Legacy Endpoints

These endpoints are maintained for backward compatibility:

| Endpoint     | Description              | Target Version                     |
| ------------ | ------------------------ | ---------------------------------- |
| `/currentV2` | Full data for Bern       | 2017 app version                   |
| `/current`   | Full data for Bern       | Original 2017 website              |
| `/today`     | Minimal data for Bern    | 2017 app version                   |
| `/slack`     | Custom Slack integration | Slack custom commands (deprecated) |

---

### Internal/Utility Endpoints

| Endpoint                | Description                               | Access                         |
| ----------------------- | ----------------------------------------- | ------------------------------ |
| `/rawdata`              | Direct access to cached microservice data | Public (ask for service names) |
| `/logs`                 | Internal command logs                     | Public (ask for service names) |
| `/slack-admin-commands` | Admin commands for managing content       | Protected                      |

---

## Response Parameters

### Core Parameters

#### Location Information

| Parameter     | Type   | Description                                |
| ------------- | ------ | ------------------------------------------ |
| `city`        | string | Location identifier (e.g., "Bern", "Thun") |
| `name`        | string | Short location name                        |
| `longname`    | string | Full location name                         |
| `url`         | string | URL to location-specific page              |
| `position`    | object | Geographic coordinates                     |
| `coordinates` | array  | [longitude, latitude]                      |

---

#### Water Data (Aare)

| Parameter                     | Type    | Description                                                                                        |
| ----------------------------- | ------- | -------------------------------------------------------------------------------------------------- |
| `aare.temperature`            | float   | Current water temperature in °C                                                                    |
| `aare.temperature_prec`       | float   | Precise water temperature measurement                                                              |
| `aare.temperature_text`       | string  | Human-readable temperature description                                                             |
| `aare.temperature_text_short` | string  | Short temperature description                                                                      |
| `flow`                        | float   | Current flow rate in m³/s                                                                          |
| `flow_text`                   | string  | Human-readable flow description                                                                    |
| `flow_gefahrenstufe`          | integer | [BAFU danger level](https://www.hydrodaten.admin.ch/de/die-5-gefahrenstufen-fuer-hochwasser) (1-5) |
| `flow_scale_threshold`        | float   | Threshold for danger level scaling                                                                 |
| `height`                      | float   | Water level/height                                                                                 |
| `historical_temp_max`         | float   | Historical maximum temperature                                                                     |

---

#### Weather Data

| Parameter     | Type    | Description                                                                                         |
| ------------- | ------- | --------------------------------------------------------------------------------------------------- |
| `sy` / `symt` | integer | [Weather symbol code](https://meteotest.ch/en/weather-api/wetter-api-dokumentation/weather-symbols) |
| `syt`         | string  | Weather symbol text description                                                                     |
| `tt`          | float   | Current air temperature in °C                                                                       |
| `tn`          | float   | Minimum air temperature                                                                             |
| `tx`          | float   | Maximum air temperature                                                                             |
| `rr`          | float   | Precipitation amount                                                                                |
| `rrreal`      | float   | Actual measured precipitation                                                                       |
| `rrisk`       | float   | Precipitation risk/probability                                                                      |
| `v`           | float   | Wind speed                                                                                          |
| `n`           | float   | Cloud coverage                                                                                      |
| `a`           | float   | Atmospheric pressure                                                                                |

---

#### Sun & Daylight

| Parameter          | Type    | Description                                      |
| ------------------ | ------- | ------------------------------------------------ |
| `suntotal`         | integer | Total sunshine duration in minutes               |
| `suntotalrelative` | float   | Relative sunshine percentage                     |
| `ss`               | string  | Sunset time                                      |
| `sun_locations`    | array   | Array of nearby sunny locations with travel time |

---

#### Forecast Data

| Parameter    | Type    | Description                               |
| ------------ | ------- | ----------------------------------------- |
| `forecast`   | boolean | Whether data is forecasted (vs. measured) |
| `forecast2h` | object  | 2-hour forecast data                      |
| `time`       | string  | Timestamp of the data point               |
| `today`      | object  | Today's summary data                      |

---

### Special Features

#### Value Extraction

The `values` parameter allows extracting specific fields as plain text (one per
line):

**Example**:

```
https://aareguru.existenz.ch/v2018/current?city=Bern&app=my.app&version=1.0&values=aare.temperature,aare.temperature_text
```

**Response** (plain text):

```
17.2
geil aber chli chalt
```

This is particularly useful for:

- IoT devices with limited parsing capabilities
- Simple integrations
- Command-line tools
- Monitoring systems

**Syntax**: Use dot notation to access nested values:

- `aare.temperature`
- `sun.sunlocations.0.timeleft` (array indexing)

---

## Integration Guidelines

### Best Practices

1. **Required Parameters**
   - Always include `app` parameter with your application identifier
   - Always include `version` parameter with your app version
   - Example: `?app=app.identifier.meine.app&version=1.42`

2. **Polling Strategy**
   - **Recommended interval**: 5 minutes
   - **Data update frequency**: 10 minutes
   - **Data delay**: 10-20 minutes from actual measurement
   - **Cache duration**: 2 minutes

3. **Defensive Programming**
   - Any value can be `null` at any time
   - Always validate and handle missing data gracefully
   - Don't assume data structure stability

4. **Performance Optimization**
   - Use the `values` parameter to extract only needed fields
   - Use `/v2018/today` for minimal data needs
   - Use `/v2018/current` only when full data is required
   - Respect cache headers

5. **Protocol**
   - HTTPS is available and recommended
   - HTTP is also supported for IoT devices with limited capabilities

6. **Cross-Origin Requests**
   - CORS headers set to `*` (all origins allowed)
   - JSONP supported via `callback` parameter

---

### Attribution Requirements

> [!IMPORTANT] This API is free for non-commercial use with the following
> requirements:
>
> - Notify the team at [aaregurus@existenz.ch](mailto:aaregurus@existenz.ch)
> - Link back to [Aare.guru](https://aare.guru)
> - Link to [BAFU](https://www.hydrodaten.admin.ch)

---

## Example Use Cases

### 1. Simple Temperature Display

**Endpoint**: `/v2018/today`

```
GET https://aareguru.existenz.ch/v2018/today?city=Bern&app=my.display&version=1.0
```

### 2. IoT Device (Temperature Only)

**Endpoint**: `/v2018/current` with value extraction

```
GET https://aareguru.existenz.ch/v2018/current?city=Bern&app=iot.device&version=1.0&values=aare.temperature
```

### 3. Dashboard with Multiple Cities

**Endpoint**: `/v2018/widget`

```
GET https://aareguru.existenz.ch/v2018/widget?app=dashboard.app&version=2.0
```

### 4. Historical Chart (Last 7 Days)

**Endpoint**: `/v2018/history`

```
GET https://aareguru.existenz.ch/v2018/history?city=Bern&start=-7%20days&end=now&app=chart.app&version=1.0
```

### 5. JSONP Integration

```
GET https://aareguru.existenz.ch/v2018/current?city=Bern&callback=handleAareData&app=web.app&version=1.0
```

---

## Monitoring & Status

- **Status Page**: [status.existenz.ch](https://status.existenz.ch/)
- **Newsletter**:
  [API News Mailing List](mailto:cstuder@existenz.ch?subject=Newsletter%20Aare.guru%20API)
- **RSS Feed**:
  [Newsletter Tag](https://hymnos.existenz.ch/tag/newsletter/feed/)

---

## Security

- **Security Policy**: Available at
  `https://aareguru.existenz.ch/.well-known/security.txt`
- **Generated via**: [securitytxt.org](https://securitytxt.org)
- **Report Issues**: Follow the security.txt contact information

---

## API Versioning Strategy

The API uses URL-based versioning:

- **Current**: `/v2018/*` (stable, recommended)
- **Legacy**: `/currentV2`, `/current`, `/today` (maintained for compatibility)

The version number represents the year of the major API revision. This approach
provides:

- Clear version identification
- Long-term stability for integrations
- Backward compatibility for legacy clients

---

## Data Quality & Reliability

### Strengths

- ✅ Official government data sources (BAFU, MeteoSchweiz)
- ✅ Professional weather forecasts (Meteotest)
- ✅ Regular updates (10-minute intervals)
- ✅ Simple, reliable technology stack
- ✅ Active maintenance and monitoring

### Limitations

- ⚠️ 10-20 minute data delay from actual measurements
- ⚠️ Any field can be `null` (sensor failures, maintenance)
- ⚠️ Non-commercial use only
- ⚠️ No SLA guarantees (hobby project)

---

## Technical Architecture Insights

Based on the
[Aare Guru Techstack Webinar](https://hymnos.existenz.ch/2021/12/03/video-aare-guru-techstack-webinar/):

1. **Philosophy**: "Boring technology" for reliability
2. **Backend**: PHP with flat file storage
3. **Caching**: Aggressive caching to reduce load on upstream sources
4. **Microservices**: Internal services aggregate data from multiple sources
5. **Deployment**: Simple, maintainable infrastructure

This architecture prioritizes:

- **Reliability** over cutting-edge technology
- **Simplicity** over complexity
- **Maintainability** for a small team/hobby project

---

## Comparison: Endpoint Selection Guide

| Need                      | Recommended Endpoint        | Reason                           |
| ------------------------- | --------------------------- | -------------------------------- |
| Single city, minimal data | `/v2018/today`              | Lightweight, fast                |
| Single city, full data    | `/v2018/current`            | Complete dataset                 |
| All cities at once        | `/v2018/widget`             | Efficient batch retrieval        |
| Historical analysis       | `/v2018/history`            | Time-series data                 |
| City discovery            | `/v2018/cities`             | List all locations               |
| IoT/embedded device       | `/v2018/current` + `values` | Text extraction, minimal parsing |

---

## Community & Support

- **Contact**: [aaregurus@existenz.ch](mailto:aaregurus@existenz.ch)
- **Developer**: Christian Studer
  ([cstuder@existenz.ch](mailto:cstuder@existenz.ch))
- **Company**: [Aare.guru GmbH](https://firma.aare.guru)
- **Related**: [Opendata.ch](https://opendata.ch) - Swiss Open Knowledge
  Foundation

---

## Conclusion

The Aareguru API is a well-designed, reliable public API that successfully
balances simplicity with functionality. Its strengths include:

1. **Clear Documentation**: OpenAPI spec + detailed parameter descriptions
2. **Flexible Data Access**: Multiple endpoints for different use cases
3. **Developer-Friendly**: CORS, JSONP, value extraction, flexible date formats
4. **Reliable Data**: Authoritative government and professional sources
5. **Sustainable Architecture**: Simple technology stack for long-term
   maintenance

**Ideal For**:

- Public information displays
- Mobile applications
- IoT projects
- Data visualization
- Environmental monitoring
- Educational projects

**Not Suitable For**:

- Commercial applications (license restriction)
- Real-time critical systems (10-20 minute delay)
- High-frequency polling (respect 5-minute recommendation)
- Applications requiring SLA guarantees

---

_Report Generated: 2025-11-30_  
_API Version Analyzed: v2018_  
_Documentation Sources: OpenAPI Specification + Official Parameter
Documentation_
