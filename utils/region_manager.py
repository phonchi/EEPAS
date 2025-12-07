#!/usr/bin/env python3
"""
Region Manager - Spatial region handling for EEPAS.

This module provides unified management of testing region and neighborhood region,
supporting both grid and polygon region types.

Region Types:
    - 'grid': Rectangular grid (e.g., CELLE_ter format)
    - 'polygon': Polygon boundary (e.g., CPTI15 format)

Regional Functions:
    - Testing Region (R): Used for likelihood calculation and forecast output
    - Neighborhood Region (N): Used for edge effect compensation

Examples:
    Single grid region (both regions use same grid)::

        mgr = RegionManager(celle_data, celle_data, 'grid', 'grid')

    Testing grid with neighborhood polygon::

        mgr = RegionManager(celle_data, cpti15_polygon, 'grid', 'polygon')
"""

import numpy as np


class RegionManager:
    """
    Region Manager - Handles spatial determination for testing and neighborhood regions

    Attributes:
        testing_region: Testing region data (grid or polygon)
        neighborhood_region: Neighborhood region data (grid or polygon)
        testing_type: 'grid' or 'polygon'
        neighborhood_type: 'grid' or 'polygon'
    """

    def __init__(self, testing_region_data, neighborhood_region_data=None,
                 testing_type='grid', neighborhood_type='grid'):
        """
        Initialize region manager.

        Args:
            testing_region_data: Testing region data

                - If type='grid': numpy array (N×10), column format is [x_min, x_max, y_min, y_max, ..., cell_id, ...]
                - If type='polygon': numpy array (M×2 or M×4), vertex coordinates

            neighborhood_region_data: Neighborhood region data (optional)

                - If None, then neighborhood = testing (same region for both)
                - Same format as testing_region_data

            testing_type: 'grid' or 'polygon'
            neighborhood_type: 'grid' or 'polygon'
        """
        self.testing_region = testing_region_data
        self.testing_type = testing_type

        # Backward compatibility: if neighborhood region not provided, use testing region
        if neighborhood_region_data is None:
            self.neighborhood_region = testing_region_data
            self.neighborhood_type = testing_type
        else:
            self.neighborhood_region = neighborhood_region_data
            self.neighborhood_type = neighborhood_type

        # Preprocessing: extract polygon vertices (if polygon)
        if self.testing_type == 'polygon':
            self.testing_polygon_vertices = self._extract_polygon_vertices(
                self.testing_region
            )

        if self.neighborhood_type == 'polygon':
            self.neighborhood_polygon_vertices = self._extract_polygon_vertices(
                self.neighborhood_region
            )

        # Preprocessing: extract grid boundaries (if grid)
        if self.testing_type == 'grid':
            self.testing_grid_bounds = self._extract_grid_bounds(
                self.testing_region
            )

        if self.neighborhood_type == 'grid':
            self.neighborhood_grid_bounds = self._extract_grid_bounds(
                self.neighborhood_region
            )


    def _extract_polygon_vertices(self, polygon_data):
        """
        Extract vertex coordinates from polygon data.

        Args:
            polygon_data: numpy array
                - If (N×2): directly [x, y] vertices
                - If (N×4): [lon, lat, x, y], use last two columns

        Returns:
            numpy array (N×2): [x, y] vertex coordinates
        """
        if polygon_data.shape[1] == 2:
            # Already in [x, y] format
            return polygon_data
        elif polygon_data.shape[1] == 4:
            # [lon, lat, x, y] format, use projected coordinates x, y
            return polygon_data[:, 2:4]
        else:
            raise ValueError(
                f"Unsupported polygon data format, number of columns: {polygon_data.shape[1]}"
            )


    def _extract_grid_bounds(self, grid_data):
        """
        Extract boundary information from grid data.

        Args:
            grid_data: numpy array (N×10 or more)
                Column format: [x_min, x_max, y_min, y_max, ...]

        Returns:
            numpy array (N×4): [x_min, x_max, y_min, y_max]
        """
        if grid_data.shape[1] < 4:
            raise ValueError(
                f"Insufficient grid data columns, need at least 4, current: {grid_data.shape[1]}"
            )

        return grid_data[:, 0:4]


    def is_in_testing_region(self, x, y):
        """
        Determine if point (x, y) is within testing region.

        Args:
            x: X coordinate (can be scalar or array)
            y: Y coordinate (can be scalar or array)

        Returns:
            bool or numpy array of bool
        """
        if self.testing_type == 'grid':
            return self._is_in_grid(x, y, self.testing_grid_bounds)
        elif self.testing_type == 'polygon':
            return self._is_in_polygon(x, y, self.testing_polygon_vertices)
        else:
            raise ValueError(f"Unsupported testing region type: {self.testing_type}")


    def is_in_neighborhood_region(self, x, y):
        """
        Determine if point (x, y) is within neighborhood region.

        Args:
            x: X coordinate (can be scalar or array)
            y: Y coordinate (can be scalar or array)

        Returns:
            bool or numpy array of bool
        """
        if self.neighborhood_type == 'grid':
            return self._is_in_grid(x, y, self.neighborhood_grid_bounds)
        elif self.neighborhood_type == 'polygon':
            return self._is_in_polygon(x, y, self.neighborhood_polygon_vertices)
        else:
            raise ValueError(
                f"Unsupported neighborhood region type: {self.neighborhood_type}"
            )


    def _is_in_grid(self, x, y, grid_bounds):
        """
        Determine if point is within rectangular grid (any cell).

        Args:
            x, y: Coordinates (scalar or array)
            grid_bounds: numpy array (N×4) [x_min, x_max, y_min, y_max]

        Returns:
            bool or numpy array of bool
        """
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)

        # Vectorized determination: check if each point is in any grid cell
        in_grid = np.zeros(len(x), dtype=bool)

        for i in range(len(x)):
            # For each point, check if it's in any grid cell
            in_any_cell = np.any(
                (x[i] >= grid_bounds[:, 0]) &
                (x[i] <= grid_bounds[:, 1]) &
                (y[i] >= grid_bounds[:, 2]) &
                (y[i] <= grid_bounds[:, 3])
            )
            in_grid[i] = in_any_cell

        # If input is scalar, return scalar
        if len(in_grid) == 1:
            return bool(in_grid[0])

        return in_grid


    def _is_in_polygon(self, x, y, polygon_vertices):
        """
        Determine if point is within polygon - Ray Casting Algorithm.

        Principle:

            - Cast a ray from the point to the right, count intersections with polygon boundary
            - Odd number of intersections → point inside polygon
            - Even number of intersections → point outside polygon

        Boundary handling:

            - Point exactly on vertex → treat as outside
            - Point exactly on edge → treat as outside
            - This conservative approach avoids incorrectly including boundary earthquakes

        Args:
            x, y: Coordinates (scalar or array)
            polygon_vertices: numpy array (N×2) polygon vertices [x, y]

        Returns:
            bool or numpy.ndarray: Boolean indicating if point(s) inside polygon

        Reference:
            https://en.wikipedia.org/wiki/Point_in_polygon
        """
        x = np.atleast_1d(x)
        y = np.atleast_1d(y)

        n_vertices = len(polygon_vertices)
        inside = np.zeros(len(x), dtype=bool)

        eps = 1e-10  # Numerical tolerance for boundary detection

        for i in range(len(x)):
            xi, yi = x[i], y[i]

            # Check if on vertex (treat as outside)
            is_on_vertex = False
            for vx, vy in polygon_vertices:
                if abs(xi - vx) < eps and abs(yi - vy) < eps:
                    is_on_vertex = True
                    break

            if is_on_vertex:
                inside[i] = False
                continue

            # Ray casting algorithm
            crosses = 0
            for j in range(n_vertices):
                # Two vertices of current edge
                x1, y1 = polygon_vertices[j]
                x2, y2 = polygon_vertices[(j + 1) % n_vertices]

                # Check if ray intersects with edge
                # Condition: point's y coordinate is within edge's y range
                if ((y1 > yi) != (y2 > yi)):
                    # Calculate x coordinate of ray-edge intersection
                    x_intersect = (x2 - x1) * (yi - y1) / (y2 - y1) + x1

                    # If intersection is to the right of point, count+1
                    if xi < x_intersect:
                        crosses += 1

            # Odd number of intersections → inside polygon
            inside[i] = (crosses % 2 == 1)

        # If input is scalar, return scalar
        if len(inside) == 1:
            return bool(inside[0])

        return inside


    def filter_events_for_learning(self, catalog, x_col=7, y_col=6):
        """
        Filter events for learning: events within neighborhood region.

        During PPE/EEPAS learning, use all events within neighborhood as source
        events to avoid edge effects.

        Args:
            catalog: numpy array (N×M) earthquake catalog
            x_col: X coordinate column (default 7, HORUS format)
            y_col: Y coordinate column (default 6, HORUS format)

        Returns:
            numpy array: Filtered catalog
        """
        x = catalog[:, x_col]
        y = catalog[:, y_col]

        mask = self.is_in_neighborhood_region(x, y)

        return catalog[mask]


    def filter_events_for_targets(self, catalog, x_col=7, y_col=6):
        """
        Filter target events: events within testing region.

        During likelihood calculation and forecasting, only use/output events
        within the testing region.

        Args:
            catalog: numpy array (N×M) earthquake catalog
            x_col: X coordinate column (default 7, HORUS format)
            y_col: Y coordinate column (default 6, HORUS format)

        Returns:
            numpy array: Filtered catalog
        """
        x = catalog[:, x_col]
        y = catalog[:, y_col]

        mask = self.is_in_testing_region(x, y)

        return catalog[mask]


    def get_active_cells(self):
        """
        Get active cell list (only when testing region is grid type).

        Returns:
            numpy array (N×4): [x_min, x_max, y_min, y_max] for each cell

        Raises:
            ValueError: If testing region is not grid type
        """
        if self.testing_type != 'grid':
            raise ValueError(
                f"get_active_cells() only supports grid-type testing region, "
                f"current type: {self.testing_type}"
            )

        return self.testing_grid_bounds


    def get_n_active_cells(self):
        """
        Get number of active cells.

        Returns:
            int: Number of cells (returns number of vertices if polygon)
        """
        if self.testing_type == 'grid':
            return len(self.testing_grid_bounds)
        elif self.testing_type == 'polygon':
            return len(self.testing_polygon_vertices)
        else:
            raise ValueError(f"Unknown type: {self.testing_type}")


    def get_region_summary(self):
        """
        Get region manager summary information (for debugging).

        Returns:
            dict: Dictionary containing region types, cell counts, and other metadata
        """
        summary = {
            'testing_type': self.testing_type,
            'neighborhood_type': self.neighborhood_type,
            'n_testing_cells': self.get_n_active_cells(),
        }

        if self.neighborhood_type == 'grid':
            summary['n_neighborhood_cells'] = len(self.neighborhood_grid_bounds)
        elif self.neighborhood_type == 'polygon':
            summary['n_neighborhood_vertices'] = len(self.neighborhood_polygon_vertices)

        return summary
