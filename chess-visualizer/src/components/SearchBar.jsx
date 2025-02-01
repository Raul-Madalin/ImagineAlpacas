import React, { useState } from "react";
import { Box, TextField, Button, Typography } from "@mui/material";

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState("");

  return (
    <Box>
      <Typography variant="h6">Search Chess Positions</Typography>
      <TextField
        fullWidth
        label="Search Pieces (e.g. 'rooks pawns')"
        variant="outlined"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        sx={{ mb: 2 }}
      />
      <Button variant="contained" color="primary" fullWidth onClick={() => onSearch(query)}>
        Search
      </Button>
    </Box>
  );
};

export default SearchBar;
