import React, { useState, useEffect } from "react";
import { Box, CssBaseline, AppBar, Toolbar, Typography } from "@mui/material";
import SearchBar from "./components/SearchBar";
import FilterPanel from "./components/FilterPanel";
import Recommandations from "./components/Recommandations";
import ImageGallery from "./components/ImageGallery";
import axios from "axios";

const ChessOntologyApp = () => {
  const [images, setImages] = useState([]);

  useEffect(() => {
    // Fetch initial 4 images when the app loads
    const fetchInitialImages = async () => {
      try {
        const response = await axios.get("http://localhost:5000/initial");
        setImages(response.data);
      } catch (error) {
        console.error("Error fetching initial images:", error);
      }
    };

    fetchInitialImages();
  }, []);

  const handleSearch = async (query) => {
    try {
      const response = await axios.get(`http://localhost:5000/search?query=${query}`);
      setImages(response.data);
    } catch (error) {
      console.error("Error fetching search results:", error);
    }
  };

  const handleFilter = async (filters) => {
    try {
      const response = await axios.post("http://localhost:5000/filter", filters, {
        headers: { "Content-Type": "application/json" },
      });
      setImages(response.data);
    } catch (error) {
      console.error("Error applying filters:", error);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <CssBaseline />
      <AppBar position="static">
        <Toolbar>
          <Box display="flex" flexGrow={1} justifyContent="center">
            <Typography variant="h6">Chess Puzzles App</Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Box sx={{ width: 250, bgcolor: "grey.200", p: 2, overflowY: "auto" }}>
          <SearchBar onSearch={handleSearch} />
          <FilterPanel onFilter={handleFilter} />
        </Box>

        <Box sx={{ flex: 1, p: 2, overflowY: "auto" }}>
          <ImageGallery images={images} />
        </Box>

        <Box sx={{ width: 400, bgcolor: "grey.200", p: 2, overflowY: "auto" }}>
          <Recommandations />
        </Box>
      </Box>

      <Box sx={{ bgcolor: "grey.800", color: "white", textAlign: "center", p: 1 }}>
        <Typography variant="body2">© 2025 ChessOntologyApp</Typography>
      </Box>
    </Box>
  );
};

export default ChessOntologyApp;
