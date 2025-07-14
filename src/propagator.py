from sgp4.api import Satrec, jday
from datetime import datetime
import json

class TLEPropagator:
    """
    Provides utilities for parsing TLEs and propagating satellite orbits using SGP4.
    """
    def __init__(self):
        """
        Initialize the TLEPropagator.
        """
        pass

    def parse_tle(self, line1: str, line2: str):
        """
        Parse a single TLE (two lines) into a Satrec object.
        Args:
            line1 (str): First line of the TLE.
            line2 (str): Second line of the TLE.
        Returns:
            Satrec: Parsed satellite record object, or None if parsing fails.
        """
        try:
            sat = Satrec.twoline2rv(line1, line2)
            return sat
        except Exception as e:
            print(f"Error parsing TLE lines:\n{line1}\n{line2}\nError: {e}")
            return None

    def propagate_satellite(self, satrec, target_epoch: datetime):
        """
        Propagate a satellite (Satrec object) to a target epoch.
        Args:
            satrec (Satrec): Satellite record object from sgp4.
            target_epoch (datetime): Target epoch to propagate to.
        Returns:
            tuple: (position_km, velocity_km_per_s) in TEME frame, or (None, None) if propagation fails.
        """
        try:
            # Convert datetime to Julian date using sgp4.api.jday
            jd, fr = jday(
                target_epoch.year, 
                target_epoch.month, 
                target_epoch.day,
                target_epoch.hour, 
                target_epoch.minute, 
                target_epoch.second + target_epoch.microsecond/1e6
            )
            
            error, r, v = satrec.sgp4(jd, fr)

            if error:
                # SGP4_ERRORS is a dictionary in sgp4.api
                try:
                    from sgp4.api import SGP4_ERRORS
                    error_msg = SGP4_ERRORS.get(error, f"Unknown SGP4 error code: {error}")
                except ImportError:
                    error_msg = f"SGP4 error code: {error}"
                print(f"SGP4 propagation error: {error_msg}")
                return None, None
            
            # Convert to lists for JSON serialization
            return list(r), list(v)

        except Exception as e:
            print(f"Error during propagation: {e}")
            return None, None