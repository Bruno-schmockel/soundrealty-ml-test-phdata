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
        self._demographics: Optional[pandas.DataFrame] = None

    def load_demographics(self) -> pandas.DataFrame:
        """Load demographics data, caching for subsequent calls.
        
        Returns:
            DataFrame with demographics data indexed by zipcode
        """
        if self._demographics is None:
            self._demographics = pandas.read_csv(
                self.demographics_path,
                dtype={'zipcode': str}
            )
        return self._demographics

    def get_demographics_for_zipcode(self, zipcode: str) -> Optional[dict]:
        """Get demographics data for a specific zipcode.
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            Dictionary of demographics data or None if zipcode not found
        """
        demographics = self.load_demographics()
        
        # Filter by zipcode
        zipcode_data = demographics[demographics['zipcode'] == zipcode]
        
        if zipcode_data.empty:
            return None
        
        return zipcode_data.iloc[0].to_dict()

    def is_valid_zipcode(self, zipcode: str) -> bool:
        """Check if a zipcode exists in the demographics data.
        
        Args:
            zipcode: 5-digit zipcode string
            
        Returns:
            True if zipcode exists, False otherwise
        """
        demographics = self.load_demographics()
        return zipcode in demographics['zipcode'].values

    def reload_demographics(self) -> None:
        """Force reload of demographics data from disk."""
        self._demographics = None
        self.load_demographics()
