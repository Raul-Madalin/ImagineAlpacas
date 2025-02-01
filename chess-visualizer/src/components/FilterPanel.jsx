import React, { useState } from "react";
import { Box, Button, FormControl, FormControlLabel, Checkbox, Typography } from "@mui/material";

const FilterPanel = ({ onFilter }) => {
  const [filters, setFilters] = useState({
    rooks: 0,
    queens: 0,
    bishops: 0,
    knights: 0,
    pawns: 0,
  });

  const handleFilterChange = (event) => {
    setFilters({
      ...filters,
      [event.target.name]: event.target.checked ? 1 : 0, // Boolean to numeric
    });
  };

  return (
    <Box sx={{ mt: 3 }}>
      <Typography variant="h6">Filter Chess Positions</Typography>
      <FormControl component="fieldset">
        {Object.keys(filters).map((piece) => (
          <FormControlLabel
            key={piece}
            control={<Checkbox name={piece} onChange={handleFilterChange} />}
            label={piece.charAt(0).toUpperCase() + piece.slice(1)}
          />
        ))}
      </FormControl>

      <Button variant="contained" color="secondary" fullWidth sx={{ mt: 2 }} onClick={() => onFilter(filters)}>
        Apply Filters
      </Button>
    </Box>
  );
};

export default FilterPanel;
