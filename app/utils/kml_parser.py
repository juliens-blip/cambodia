"""KML parser utility for extracting geographic and production data."""
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
import logging
import re

logger = logging.getLogger(__name__)


class KMLParser:
    """
    Parser for KML (Keyhole Markup Language) files.

    Extracts coordinates, placemarks, and associated production data.
    """

    def __init__(self):
        """Initialize KML parser."""
        self.ns = {"kml": "http://www.opengis.net/kml/2.2"}

    def parse(self, content: bytes) -> Dict[str, Any]:
        """
        Parse KML file content.

        Args:
            content: KML file content as bytes

        Returns:
            Dictionary with parsed data including placemarks, coordinates, etc.
        """
        try:
            root = ET.fromstring(content.decode("utf-8"))

            placemarks = self._extract_placemarks(root)
            coordinates = self._extract_all_coordinates(root)

            return {
                "placemarks": placemarks,
                "coordinates": coordinates,
                "total_placemarks": len(placemarks),
                "total_coordinates": len(coordinates)
            }

        except Exception as e:
            logger.error(f"Error parsing KML: {e}")
            return {
                "placemarks": [],
                "coordinates": [],
                "total_placemarks": 0,
                "total_coordinates": 0,
                "error": str(e)
            }

    def _extract_placemarks(self, root: ET.Element) -> List[Dict[str, Any]]:
        """
        Extract all placemarks from KML.

        Args:
            root: KML root element

        Returns:
            List of placemark dictionaries
        """
        placemarks = []

        for placemark in root.findall(".//kml:Placemark", self.ns):
            name_elem = placemark.find(".//kml:name", self.ns)
            desc_elem = placemark.find(".//kml:description", self.ns)

            name = name_elem.text if name_elem is not None else None
            description = desc_elem.text if desc_elem is not None else None

            # Extract coordinates
            point = placemark.find(".//kml:Point/kml:coordinates", self.ns)
            polygon = placemark.find(".//kml:Polygon/kml:outerBoundaryIs/kml:LinearRing/kml:coordinates", self.ns)

            coordinates = None

            if point is not None and point.text:
                coords = point.text.strip().split(",")
                if len(coords) >= 2:
                    coordinates = {
                        "type": "Point",
                        "lat": float(coords[1]),
                        "lon": float(coords[0]),
                        "alt": float(coords[2]) if len(coords) > 2 else None
                    }

            elif polygon is not None and polygon.text:
                # Extract polygon coordinates
                coord_pairs = polygon.text.strip().split()
                polygon_coords = []

                for pair in coord_pairs:
                    coords = pair.split(",")
                    if len(coords) >= 2:
                        polygon_coords.append({
                            "lat": float(coords[1]),
                            "lon": float(coords[0])
                        })

                if polygon_coords:
                    coordinates = {
                        "type": "Polygon",
                        "coordinates": polygon_coords,
                        "centroid": self._calculate_centroid(polygon_coords)
                    }

            # Extract extended data if available
            extended_data = self._extract_extended_data(placemark)

            placemark_data = {
                "name": name,
                "description": description,
                "coordinates": coordinates,
                "extended_data": extended_data
            }

            placemarks.append(placemark_data)

        return placemarks

    def _extract_all_coordinates(self, root: ET.Element) -> List[Dict[str, float]]:
        """
        Extract all point coordinates from KML.

        Args:
            root: KML root element

        Returns:
            List of coordinate dictionaries with lat/lon
        """
        coordinates = []

        for point in root.findall(".//kml:Point/kml:coordinates", self.ns):
            if point.text:
                coords = point.text.strip().split(",")
                if len(coords) >= 2:
                    try:
                        coordinates.append({
                            "lat": float(coords[1]),
                            "lon": float(coords[0])
                        })
                    except (ValueError, IndexError):
                        continue

        return coordinates

    def _extract_extended_data(self, placemark: ET.Element) -> Dict[str, Any]:
        """
        Extract ExtendedData from placemark.

        Args:
            placemark: Placemark element

        Returns:
            Dictionary of extended data
        """
        extended_data = {}

        # Look for ExtendedData element
        ext_data_elem = placemark.find(".//kml:ExtendedData", self.ns)

        if ext_data_elem is not None:
            # Extract Data elements
            for data_elem in ext_data_elem.findall(".//kml:Data", self.ns):
                name_attr = data_elem.get("name")
                value_elem = data_elem.find(".//kml:value", self.ns)

                if name_attr and value_elem is not None:
                    extended_data[name_attr] = value_elem.text

        return extended_data

    def _calculate_centroid(self, coordinates: List[Dict[str, float]]) -> Dict[str, float]:
        """
        Calculate centroid of polygon.

        Args:
            coordinates: List of lat/lon dictionaries

        Returns:
            Centroid lat/lon dictionary
        """
        if not coordinates:
            return {"lat": 0.0, "lon": 0.0}

        avg_lat = sum(c["lat"] for c in coordinates) / len(coordinates)
        avg_lon = sum(c["lon"] for c in coordinates) / len(coordinates)

        return {"lat": avg_lat, "lon": avg_lon}

    def extract_production_data(
        self,
        content: bytes,
        commodity: str,
        source: str = "KML"
    ) -> List[Dict[str, Any]]:
        """
        Extract production data from KML file.

        Looks for placemarks with production information in name, description, or extended data.

        Args:
            content: KML file content
            commodity: Commodity name (cashew/rubber)
            source: Data source name

        Returns:
            List of production records
        """
        parsed = self.parse(content)
        records = []

        for placemark in parsed.get("placemarks", []):
            # Try to extract province
            province = self._extract_province(placemark)

            if not province:
                continue

            # Extract year
            year = self._extract_year(placemark)

            # Extract production data
            production_tons = self._extract_production_tons(placemark)
            area_hectares = self._extract_area_hectares(placemark)

            if production_tons or area_hectares:
                record = {
                    "commodity": commodity,
                    "year": year,
                    "province": province,
                    "production_tons": production_tons,
                    "area_hectares": area_hectares,
                    "geolocation": placemark.get("coordinates"),
                    "source": source,
                    "metadata": {
                        "placemark_name": placemark.get("name"),
                        "description": placemark.get("description"),
                        "extended_data": placemark.get("extended_data", {})
                    }
                }

                records.append(record)

        logger.info(f"Extracted {len(records)} production records from KML")
        return records

    def _extract_province(self, placemark: Dict[str, Any]) -> Optional[str]:
        """
        Extract province name from placemark.

        Args:
            placemark: Placemark dictionary

        Returns:
            Province name or None
        """
        # Cambodian provinces
        provinces = [
            "Kampong Cham", "Kampong Thom", "Kratie", "Mondulkiri", "Ratanakiri",
            "Stung Treng", "Preah Vihear", "Kampong Speu", "Pursat", "Battambang",
            "Banteay Meanchey", "Oddar Meanchey", "Pailin", "Siem Reap", "Kampot",
            "Kep", "Koh Kong", "Preah Sihanouk", "Takeo", "Kandal", "Prey Veng",
            "Svay Rieng", "Tbong Khmum", "Phnom Penh"
        ]

        # Check in name, description, and extended data
        search_text = " ".join([
            placemark.get("name", ""),
            placemark.get("description", ""),
            str(placemark.get("extended_data", {}))
        ]).lower()

        for province in provinces:
            if province.lower() in search_text:
                return province

        # Check extended data specifically
        ext_data = placemark.get("extended_data", {})
        for key in ["province", "Province", "PROVINCE", "region", "Region"]:
            if key in ext_data:
                return ext_data[key]

        return None

    def _extract_year(self, placemark: Dict[str, Any]) -> int:
        """
        Extract year from placemark.

        Args:
            placemark: Placemark dictionary

        Returns:
            Year (defaults to current year if not found)
        """
        from datetime import datetime

        # Check extended data first
        ext_data = placemark.get("extended_data", {})
        for key in ["year", "Year", "YEAR", "date", "Date"]:
            if key in ext_data:
                match = re.search(r'20[0-9]{2}', str(ext_data[key]))
                if match:
                    return int(match.group(0))

        # Check name and description
        search_text = " ".join([
            placemark.get("name", ""),
            placemark.get("description", "")
        ])

        match = re.search(r'20[0-9]{2}', search_text)
        if match:
            return int(match.group(0))

        return datetime.now().year

    def _extract_production_tons(self, placemark: Dict[str, Any]) -> Optional[float]:
        """
        Extract production in tons from placemark.

        Args:
            placemark: Placemark dictionary

        Returns:
            Production in tons or None
        """
        # Check extended data
        ext_data = placemark.get("extended_data", {})
        for key in ["production_tons", "production", "Production", "tons", "Tons", "yield"]:
            if key in ext_data:
                try:
                    value = str(ext_data[key]).replace(",", "")
                    return float(value)
                except (ValueError, TypeError):
                    continue

        # Check description
        description = placemark.get("description", "")
        match = re.search(r'(\d+[\d,]*\.?\d*)\s*(?:tons|tonnes|metric tons|MT)', description, re.IGNORECASE)

        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass

        return None

    def _extract_area_hectares(self, placemark: Dict[str, Any]) -> Optional[float]:
        """
        Extract area in hectares from placemark.

        Args:
            placemark: Placemark dictionary

        Returns:
            Area in hectares or None
        """
        # Check extended data
        ext_data = placemark.get("extended_data", {})
        for key in ["area_hectares", "area", "Area", "hectares", "Hectares", "ha"]:
            if key in ext_data:
                try:
                    value = str(ext_data[key]).replace(",", "")
                    return float(value)
                except (ValueError, TypeError):
                    continue

        # Check description
        description = placemark.get("description", "")
        match = re.search(r'(\d+[\d,]*\.?\d*)\s*(?:ha|hectares|hectare)', description, re.IGNORECASE)

        if match:
            try:
                return float(match.group(1).replace(",", ""))
            except ValueError:
                pass

        return None
