# SpaceTrackMCP

**SpaceTrackMCP** is an MCP (Machine Control Protocol) server for the [Space-Track API](https://www.space-track.org/), built to provide programmatic and extensible access to satellite Two-Line Elements (TLEs) and satellite orbit propagation. The server is designed for research, automation, and educational purposes, and exposes a set of tools through an MCP interface.

---

## Features

- **MCP Server**: Easily extensible server using FastMCP for remote control of tools.
- **Get TLEs Tool**: Query the latest or historical TLEs for satellites from Space-Track using various filters (NORAD ID, epoch, mean motion, eccentricity, etc.).
- **Propagate Satellite Tool**: Propagate any satellite's orbit to a specified epoch using the SGP4 algorithm and obtain position and velocity vectors.
- **Extensible Design**: Built to easily add new tools—next up: Satellite interpolation support.
---

## Demo

*A video demo of the server and its tools will be added here soon!*
[![IMAGE ALT TEXT HERE](https://img.youtube.com/vi/w21zwpXZgAE/0.jpg)]([https://www.youtube.com/watch?v=YOUTUBE_VIDEO_ID_HERE](https://youtu.be/w21zwpXZgAE))

---

## Usage

### 1. Environment Setup

- Clone the repository.
- Install dependencies (see below).
- Set up your `.env` file with your Space-Track credentials:
  ```
  SPACE_TRACK_USERNAME=your_username
  SPACE_TRACK_PASSWORD=your_password
  ```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Running the Server

```bash
python src/server.py
```

The server exposes MCP tools you can interact with using an MCP client.

---

## Tools

### 1. Get TLEs

Retrieve Two-Line Elements for satellites from Space-Track with flexible filtering:

- **Inputs**: `norad_cat_id`, `start_date`, `end_date`, `mean_motion_min`, `mean_motion_max`, `eccentricity_min`, `eccentricity_max`, `format_type`
- **Returns**: TLEs in JSON, TLE, XML, or CSV format.

### 2. Propagate Satellite

Propagate a satellite's orbit to a target epoch using SGP4.

- **Inputs**: `norad_cat_id`, `epoch` (ISO 8601)
- **Returns**: Position (km), velocity (km/s) in TEME frame, TLE epoch.

### (Coming Soon) Interpolation Tool

A new tool for orbit interpolation is in progress—stay tuned!

---

## Example Code

```python
# Example: Get TLEs for the ISS (NORAD 25544)
result = await get_tles(norad_cat_id=25544)

# Example: Propagate ISS to a specific datetime
result = await propagate_satellite_position(norad_cat_id=25544, epoch="2025-07-15T00:00:00Z")
```

---

## Architecture

- **`src/server.py`**: Main server logic, tools registration, and entry point.
- **`src/spacetrack_client.py`**: Handles Space-Track API authentication and TLE retrieval.
- **`src/propagator.py`**: TLE parsing and satellite propagation using SGP4.
- Tools are exposed via the MCP protocol and can be extended by adding new decorated methods.

---

## Requirements

- Python 3.8+
- `aiohttp`, `python-dotenv`, `sgp4`, and other dependencies in `requirements.txt`
- Space-Track account credentials

---


## Roadmap

- [x] TLE retrieval and filtering
- [x] SGP4 propagation tool
- [ ] Orbit interpolation tool
- [ ] More sample clients and UI integration
- [ ] Documentation and advanced examples

---

## Contributing

Contributions and suggestions are welcome! Please open issues or pull requests.

---

## Acknowledgements

- [Space-Track.org](https://www.space-track.org/)
- [SGP4 Python Library](https://pypi.org/project/sgp4/)
- MCP/FastMCP framework
