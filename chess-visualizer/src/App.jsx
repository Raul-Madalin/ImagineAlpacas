import React, { useState, useEffect } from "react";
import { Box, CssBaseline, AppBar, Toolbar, Typography, Button, CircularProgress } from "@mui/material";
import SearchBar from "./components/SearchBar";
import FilterPanel from "./components/FilterPanel";
import Recommandations from "./components/Recommandations";
import ImageGallery from "./components/ImageGallery";
import axios from "axios";

const ChessOntologyApp = () => {
  const [images, setImages] = useState([]);
  const [originalImages, setOriginalImages] = useState([]); // Stores initial images (if no search)
  const [searchResults, setSearchResults] = useState([]); // Stores latest search results
  const [searchPerformed, setSearchPerformed] = useState(false); 
  const [recommendations, setRecommendations] = useState([]);
  const [isLoadingImages, setIsLoadingImages] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);

  useEffect(() => {
    const fetchInitialImages = async () => {
      try {
        setIsLoadingImages(true);
        const response = await axios.get("http://localhost:5000/initial");
        setImages(response.data);
        setOriginalImages(response.data);
      } catch (error) {
        console.error("Error fetching initial images:", error);
      } finally {
        setIsLoadingImages(false);
      }
    };

    fetchInitialImages();
  }, []);

  const fetchRecommendations = async (puzzleIds) => {
    if (puzzleIds.length === 0) return;

    try {
      setIsLoadingRecommendations(true);
      const response = await axios.post("http://localhost:5000/recommendations", {
        puzzle_ids: puzzleIds,
      });

      setRecommendations(response.data);
    } catch (error) {
      console.error("Error fetching recommendations:", error);
    } finally {
      setIsLoadingRecommendations(false);
    }
  };

  const handleSearch = async (query) => {
    try {
      setIsLoadingImages(true);
      const response = await axios.get(`http://localhost:5000/search?query=${query}`);
      setImages(response.data);
      setSearchResults(response.data);
      setSearchPerformed(true);

      const visiblePuzzleIds = response.data.slice(0, 6).map((image) => image.puzzle_id);
      fetchRecommendations(visiblePuzzleIds);
    } catch (error) {
      console.error("Error fetching search results:", error);
    } finally {
      setIsLoadingImages(false);
    }
  };

  const handleFilter = async (filters) => {
    try {
      setIsLoadingImages(true);

      const baseImages = searchPerformed ? searchResults : originalImages;
      const puzzleIds = baseImages.map((image) => image.puzzle_id);

      if (puzzleIds.length === 0) {
        console.warn("No images available to filter.");
        return;
      }

      const requestBody = {
        filters: filters,
        puzzle_ids: puzzleIds
      };

      const response = await axios.post("http://localhost:5000/filter", requestBody, {
        headers: { "Content-Type": "application/json" },
      });

      setImages(response.data);

      const visiblePuzzleIds = response.data.slice(0, 6).map((image) => image.puzzle_id);
      fetchRecommendations(visiblePuzzleIds);
    } catch (error) {
      console.error("Error applying filters:", error);
    } finally {
      setIsLoadingImages(false);
    }
  };

  return (
    <Box sx={{ display: "flex", flexDirection: "column", height: "100vh" }}>
      <CssBaseline />
      <AppBar position="static" sx={{
          backgroundColor: "#4e4091",
        }}
      >
        <Toolbar>
          <Box display="flex" flexGrow={0} mr={2}>
            <Button variant="contained" color="primary" onClick={() => window.location.reload()}>
              Home
            </Button>
          </Box>
          <Box display="flex" flexGrow={1} justifyContent="center">
            <Typography variant="h6">Chess Puzzles App</Typography>
          </Box>
        </Toolbar>
      </AppBar>

      <Box sx={{ display: "flex", flex: 1, overflow: "hidden" }}>
        <Box sx={{ width: 250, bgcolor: "grey.200", p: 2, overflowY: "auto" }}>
          <SearchBar onSearch={handleSearch} />
          <br></br>
          <FilterPanel onFilter={handleFilter} />
        </Box>

        <Box sx={{ flex: 1, p: 2, overflowY: "auto" }}>
          <ImageGallery 
            images={images} 
            isLoading={isLoadingImages}
            onPageChange={(visiblePuzzleIds) => fetchRecommendations(visiblePuzzleIds)}
          />
        </Box>

        <Box sx={{ width: 400, bgcolor: "grey.200", p: 2, overflowY: "auto" }}>
          <Recommandations 
            recommendations={recommendations} 
            isLoading={isLoadingRecommendations}
          />
        </Box>
      </Box>

      <Box sx={{ bgcolor: "grey.800", color: "white", textAlign: "center", p: 1 }}>
        <Typography variant="body2">© 2025 ChessOntologyApp</Typography>
      </Box>
    </Box>
  );
};

export default ChessOntologyApp;
