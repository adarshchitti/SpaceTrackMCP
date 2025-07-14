import asyncio
import aiohttp
import json
import os
from urllib.parse import urlencode
from typing import List, Dict, Optional, Union
import datetime

class SpaceTrackClient:
    def __init__(self, username: str, password: str):
        """
        Initialize the SpaceTrackClient with user credentials.
        Args:
            username (str): Space-Track.org username.
            password (str): Space-Track.org password.
        """
        self.username = username
        self.password = password
        self.base_url = "https://www.space-track.org"
        self.session = None 
        self._authenticated = False

    async def _ensure_session(self):
        """
        Ensure an active aiohttp session exists for making requests.
        """
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def login(self):
        """
        Authenticate with Space-Track.org using provided credentials.
        Ensures a session is established and sets authentication state.
        Raises:
            Exception: If authentication fails or connection issues occur.
        """
        if self._authenticated:
            return

        await self._ensure_session()  # Make sure session exists

        login_url = f"{self.base_url}/ajaxauth/login"
        payload = {"identity": self.username, "password": self.password}
        try:
            async with self.session.post(login_url, data=payload) as response:
                response.raise_for_status()
                response_text = await response.text()
                # Space-Track doesn't always return "Login Successful" - check for redirect or cookies
                if response.status == 200:
                    self._authenticated = True
                    print("Successfully authenticated with Space-Track.")
                else:
                    raise Exception("Space-Track authentication failed. Check credentials.")
        except aiohttp.ClientError as e:
            raise Exception(f"Failed to connect to Space-Track for authentication: {e}")

    async def make_request(self, endpoint: str) -> Union[List[Dict], str]:
        """
        Make a request to the Space-Track API for a given endpoint.
        Args:
            endpoint (str): The API endpoint to query (relative to /basicspacedata/query/).
        Returns:
            Union[List[Dict], str]: Parsed JSON data or raw text depending on response type.
        Raises:
            Exception: If the request fails or response cannot be decoded.
        """
        await self.login()  # This will ensure session exists
        
        try:
            url = f'{self.base_url}/basicspacedata/query/{endpoint}'
            print(f"Making request to: {url}", file=os.sys.stderr)  # Debug logging
            
            async with self.session.get(url) as response:
                response.raise_for_status()  # Raises an exception for 4xx/5xx responses
                
                # Check content type to determine how to parse
                content_type = response.headers.get('content-type', '').lower()
                
                if 'application/json' in content_type:
                    return await response.json()
                else:
                    # For TLE format, XML, CSV, etc.
                    return await response.text()
                    
        except aiohttp.ClientError as e:
            error_text = await response.text() if 'response' in locals() else "No response body"
            raise Exception(f"Request failed with status {response.status}: {error_text}. Error: {e}")
        except json.JSONDecodeError:
            error_text = await response.text() if 'response' in locals() else "No response body"
            raise Exception(f"Failed to decode JSON from Space-Track response: {error_text}")

    async def get_tles(
        self,
        norad_cat_id: Optional[int] = None,
        start_date: Optional[str] = None,  
        end_date: Optional[str] = None,    
        mean_motion_min: Optional[float] = None,  # Example: 15.0 for 15 revs/day
        mean_motion_max: Optional[float] = None,  # Example: 16.0 for 16 revs/day
        eccentricity_min: Optional[float] = None,  # Example: 0.0
        eccentricity_max: Optional[float] = None,  # Example: 0.1
        format_type: Optional[str] = None,  # 'json', 'tle', 'xml', 'csv'
        limit: int = 10 
    ) -> Union[List[Dict], str]:
        """
        Fetch TLEs from Space-Track based on various criteria.
        Args:
            norad_cat_id (Optional[int]): NORAD Catalog ID of the satellite.
            start_date (Optional[str]): Filter TLEs by epoch start time (ISO 8601).
            end_date (Optional[str]): Filter TLEs by epoch end time (ISO 8601).
            mean_motion_min (Optional[float]): Minimum mean motion (revs/day).
            mean_motion_max (Optional[float]): Maximum mean motion (revs/day).
            eccentricity_min (Optional[float]): Minimum eccentricity.
            eccentricity_max (Optional[float]): Maximum eccentricity.
            format_type (Optional[str]): Output format ('json', 'tle', 'xml', 'csv').
            limit (int): Maximum number of results to return.
        Returns:
            Union[List[Dict], str]: List of TLE dictionaries or raw string, depending on format_type.
        """
        print(f" DEBUG: Entering get_tles. Received params: norad_cat_id={norad_cat_id}, start_date={start_date}, end_date={end_date}, mean_min={mean_motion_min}, mean_max={mean_motion_max}, ecc_min={eccentricity_min}, ecc_max={eccentricity_max}, format={format_type}", file=os.sys.stderr)
        class_name = 'tle'
        # Determine which API class to use
        if norad_cat_id:
            # Use tle_latest for single satellite
            filter_segments = [f"NORAD_CAT_ID/{norad_cat_id}"]
        else:
            # Use tle for broader queries
            filter_segments = []

        # Add date filters if provided
        if start_date and end_date:
            filter_segments.append(f"EPOCH/{start_date}%2D%2D{end_date}")
        elif start_date:
            filter_segments.append(f"EPOCH/%3E{start_date}")
        elif end_date:
            filter_segments.append(f"EPOCH/%3C{end_date}")
        else:
            filter_segments.append("EPOCH/%3Enow-1")
        # Add mean motion and eccentricity filters if provided
        if mean_motion_max and mean_motion_min:
            filter_segments.append(f"MEAN_MOTION/{mean_motion_min}%2D%2D{mean_motion_max}")
        elif mean_motion_min:
            filter_segments.append(f"MEAN_MOTION/%3E{mean_motion_min}")
        elif mean_motion_max:
            filter_segments.append(f"MEAN_MOTION/%3C{mean_motion_max}")
        
        if eccentricity_max and eccentricity_min:
            filter_segments.append(f"ECCENTRICITY/{eccentricity_min}%2D%2D{eccentricity_max}")
        elif eccentricity_min:
            filter_segments.append(f"ECCENTRICITY/%3E{eccentricity_min}")
        elif eccentricity_max:
            filter_segments.append(f"ECCENTRICITY/%3C{eccentricity_max}")

        # Build the endpoint
        base_endpoint = f"class/{class_name}"
        
        if filter_segments:
            full_endpoint = f"{base_endpoint}/" + "/".join(filter_segments)
        else:
            full_endpoint = base_endpoint
        if format_type is None:
            format_type = 'json'
        # Add ordering and format
        full_endpoint += f"/orderby/EPOCH%20DESC/format/{format_type}/LIMIT/{limit}/emptyresult/show"

        print(f"Space-Track API Query Endpoint: {full_endpoint}")  
        
        try:
            data = await self.make_request(full_endpoint)
            return data
                
        except Exception as e:
            print(f"Error in get_tles: {e}")
            if format_type == 'json':
                return []
            else:
                return ""

    async def close(self):
        """
        Close the aiohttp session if it exists and reset authentication state.
        """
        if self.session:
            await self.session.close()
            self.session = None
            self._authenticated = False