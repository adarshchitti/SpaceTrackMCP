# src/server.py (Using decorator syntax)
import os
import asyncio
import atexit
from datetime import datetime, timezone
from typing import List, Optional, Dict, Union
from dotenv import load_dotenv

from mcp.server import Server, FastMCP
from mcp.types import Tool, TextContent, CallToolResult, Resource
from spacetrack_client import SpaceTrackClient
from propagator import TLEPropagator

# Load environment variables
load_dotenv()

# Initialize Space-Track client
ST_USERNAME = os.getenv("SPACE_TRACK_USERNAME")
ST_PASSWORD = os.getenv("SPACE_TRACK_PASSWORD")

if not ST_USERNAME or not ST_PASSWORD:
    raise ValueError("SPACE_TRACK_USERNAME and SPACE_TRACK_PASSWORD must be set in the .env file.")

space_track_client = SpaceTrackClient(ST_USERNAME, ST_PASSWORD)
tle_propagator = TLEPropagator()

# Initialize FastMCP server
mcp = FastMCP("Space-Track MCP Server")

# Tool 1: Get TLE data (using decorator)
@mcp.tool()
async def get_tles(
    norad_cat_id: Optional[int] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    mean_motion_min: Optional[float] = None,
    mean_motion_max: Optional[float] = None,
    eccentricity_min: Optional[float] = None,
    eccentricity_max: Optional[float] = None,
    format_type: str = 'json'
) -> Union[List[Dict], str]:
    """
    Retrieves Two-Line Element (TLE) sets from Space-Track.org based on various criteria.
    (Gets the 10 latest TLEs for the query parameters provided to prevent timeouts and crashes.)
    Args:
        norad_cat_id: The NORAD Catalog ID of the satellite.
        start_date:(Not Inclusive) Filter TLEs by epoch start time - only returns TLEs with epochs > this datetime. MUST be ISO 8601 format with timezone. Example: '2025-07-12T00:00:00Z'. 
        end_date:(Not Inclusive) Filter TLEs by epoch end time - only returns TLEs with epochs < this datetime. MUST be ISO 8601 format with timezone. Example: '2025-07-12T23:59:59Z'.
        mean_motion_min: Minimum mean motion (revolutions per day) for filtering (inclusive).
            (example: geo might have a minimum mean motion of 0.99)
        mean_motion_max: Maximum mean motion (revolutions per day) for filtering (inclusive).
            (example: geo might have a max mean motion of 1.1)
        eccentricity_min: Minimum eccentricity for filtering.
        eccentricity_max: Maximum eccentricity for filtering.
            (example: geo has a max eccentricity of 0.01)
        format_type: The desired output format ('json', 'tle', 'xml', 'csv').
    Returns:
        A list of TLE dictionaries if format_type is 'json', or a raw string for other formats.
    """
    try:
        # Assuming space_track_client.get_tles handles all filtering at the API level
        tle_data = await space_track_client.get_tles(
            norad_cat_id=norad_cat_id,
            start_date=start_date,
            end_date=end_date,
            format_type=format_type,
            mean_motion_min=mean_motion_min,
            mean_motion_max=mean_motion_max,
            eccentricity_min=eccentricity_min,
            eccentricity_max=eccentricity_max
        )

        # No client-side filtering needed here, just return what the client gave us
        return tle_data

    except Exception as e:
        return {"error": str(e)}


# Tool 2: Propagate satellite position (using decorator)
@mcp.tool()
async def propagate_satellite_position(
    norad_cat_id: int,
    epoch: str
) -> Dict:
    """
    Propagates a satellite's position to a future epoch given its NORAD Catalog ID (in the TEME frame).
    Args:
        norad_cat_id: The NORAD Catalog ID of the satellite.
        epoch: The target epoch for propagation in ISO 8601 format (e.g., '2025-12-31T12:00:00Z').
    Returns:
        A dictionary containing the NORAD ID, target epoch, and propagated position/velocity.
    """
    try:
        # 1. Get the latest TLE for the given NORAD ID
        tle = await space_track_client.get_tles(norad_cat_id=norad_cat_id, format_type='json', limit=1)
        
        if not tle:
            return {"error": f"No TLEs found for NORAD ID: {norad_cat_id}"}
        

        tle_line1 = tle[0]['TLE_LINE1']
        tle_line2 = tle[0]['TLE_LINE2']

        satrec = tle_propagator.parse_tle(tle_line1, tle_line2)
        if not satrec:
            return {"error": f"Failed to parse TLE for NORAD ID {norad_cat_id}."}

        # 3. Propagate to the target epoch
        try:
            target_datetime = datetime.fromisoformat(epoch)
        except ValueError:
            return {"error": "Invalid epoch format. Please use ISO 8601 (e.g., '2025-12-31T12:00:00Z')."}

        position, velocity = tle_propagator.propagate_satellite(satrec, target_datetime)

        if position is None:
            return {"error": f"Failed to propagate satellite {norad_cat_id} to {epoch}."}

        return {
            "norad_cat_id": norad_cat_id,
            "target_epoch": epoch,
            "position_km": position,
            "velocity_km_per_s": velocity,
            "tle_epoch": tle[0]['EPOCH']
        }

    except Exception as e:
        return {"error": str(e)}
    
    
# Cleanup function
def cleanup_session():
    """Cleanup function to close the Space-Track client session."""
    try:
        print("Closing Space-Track client session...")
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(space_track_client.close())
        loop.close()
        print("Session closed successfully.")
    except Exception as e:
        print(f"Error during session cleanup: {e}")

# Register cleanup function
atexit.register(cleanup_session)

# Main execution
if __name__ == "__main__":
    try:        
        mcp.run()
        
    except KeyboardInterrupt:
        print("\nShutting down server...")
        cleanup_session()
    except Exception as e:
        print(f"Error running server: {e}")
        cleanup_session()