import React, { useState } from "react";
import { Box, TextField, Button } from "@mui/material";

const SearchBar = ({ onSearch }) => {
  const [query, setQuery] = useState("");

  return (
    <Box vocab="http://schema.org/" typeof="SearchAction">
      
      {/* Search Input Field with RDFa metadata */}
      <TextField
        fullWidth
        label="Search Pieces (e.g., 'rooks pawns')"
        variant="outlined"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
        property="query-input"
        sx={{ mb: 2 }}
      />

      {/* Search Button with RDFa metadata */}
      <Button 
        variant="contained" 
        color="primary" 
        fullWidth 
        onClick={() => onSearch(query)}
        property="target"
      >
        Search
      </Button>
    </Box>
  );
};

export default SearchBar;
