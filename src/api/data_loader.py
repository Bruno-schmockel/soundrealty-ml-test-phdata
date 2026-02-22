"""Data loading utilities for demographics and other static data."""

import pathlib
from typing import Optional
import pandas


class DataLoader:
    """Handles loading and caching of static data files."""

    def __init__(self, demographics_path: str = "data/zipcode_demographics.csv"):
        """Initialize data loader.
        
        Args:
            demographics_path: Path to demographics CSV file
        """
        self.demographics_path = pathlib.Path(demographics_path)
        self._demographics_by_zipcode: Optional[dict] = None

    def load_demographics(self) -> None:
        """Load demographics data from CSV into memory-efficient dictionary.
        
        Converts CSV to dict with zipcode as key for O(1) lookups.
        """
        if self._demographics_by_zipcode is None:
            # Load DataFrame, convert to dict, then discard DataFrame
            df = pandas.read_csv(
                self.demographics_path,
                dtype={'zipcode': str}
            )
            self._demographics_by_zipcode = {
                row['zipcode']: row.to_dict() 
                for _, row in df.iterrows()
            }

    def get_demographics_for_zipcode(self, zipcode: str) -> Optional[dict]:
        """Get demographics data for a specific zipcode (O(1) lookup).
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            Dictionary of demographics data or None if zipcode not found
        """
        self.load_demographics()  # Ensure dict is populated
        assert self._demographics_by_zipcode is not None
        return self._demographics_by_zipcode.get(zipcode)

    def is_valid_zipcode(self, zipcode: str) -> Optional[dict]:
        """Check if zipcode exists and return its demographics data (O(1)).
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            Dictionary of demographics data if found, None if zipcode not found
        """
        return self.get_demographics_for_zipcode(zipcode)

    def reload_demographics(self) -> None:
        """Force reload of demographics data from disk."""
        self._demographics_by_zipcode = None
        self.load_demographics()
