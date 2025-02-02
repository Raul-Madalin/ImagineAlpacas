import React, { useState, useEffect } from "react";
import { Box, CssBaseline, AppBar, Toolbar, Typography, Button, CircularProgress, FormControlLabel, Switch } from "@mui/material";
import SearchBar from "./components/SearchBar";
import FilterPanel from "./components/FilterPanel";
import Recommandations from "./components/Recommandations";
import ImageGallery from "./components/ImageGallery";
import axios from "axios";

const DEFAULT_FILTER_STATE = {
  rooks: [],
  queens: [],
  bishops: [],
  knights: [],
  pawns: [],
  game_state: []
};

const DEFAULT_EXPANDED_SECTIONS = {
  rooks: false,
  queens: false,
  bishops: false,
  knights: false,
  pawns: false,
  game_state: false
};

const ChessOntologyApp = () => {
  const [images, setImages] = useState([]);
  const [originalImages, setOriginalImages] = useState([]); // Stores initial images (if no search)
  const [searchResults, setSearchResults] = useState([]); // Stores latest search results
  const [searchOrFilterPerformed, setSearchOrFilterPerformed] = useState(false); 
  const [recommendations, setRecommendations] = useState([]);
  const [isLoadingImages, setIsLoadingImages] = useState(false);
  const [isLoadingRecommendations, setIsLoadingRecommendations] = useState(false);
  const [useRdfRecommendations, setUseRdfRecommendations] = useState(true);
  const [useRdfGameState, setUseRdfGameState] = useState(true);
  const [selectedFilters, setSelectedFilters] = useState({ ...DEFAULT_FILTER_STATE });
  const [expandedSections, setExpandedSections] = useState({ ...DEFAULT_EXPANDED_SECTIONS });

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

      const endpoint = useRdfRecommendations
        ? "http://localhost:5000/rdf-recommendations"
        : "http://localhost:5000/ml-recommendations";
      const response = await axios.post(endpoint, {
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
      setIsLoadingRecommendations(true);

      const response = await axios.get(`http://localhost:5000/search?query=${query}`);

      setImages(response.data);
      setSearchResults(response.data);
      setSearchOrFilterPerformed(true); 

      setSelectedFilters({ ...DEFAULT_FILTER_STATE });
      setExpandedSections({ ...DEFAULT_EXPANDED_SECTIONS });

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
      setIsLoadingRecommendations(true);
      setSelectedFilters(filters);

      const baseImages = searchOrFilterPerformed ? searchResults : originalImages;
      const puzzleIds = baseImages.map((image) => image.puzzle_id);

      if (puzzleIds.length === 0) {
        console.warn("No images available to filter.");
        return;
      }

      const requestBody = {
        filters: filters,
        puzzle_ids: puzzleIds,
        game_state_filter_endpoint: useRdfGameState
        ? "http://localhost:5000//filter/game-state-rdf"
        : "http://localhost:5000//filter/game-state-ml"
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
          <FilterPanel 
            onFilter={handleFilter} 
            selectedFilters={selectedFilters}
            setSelectedFilters={setSelectedFilters}
            expandedSections={expandedSections}
            setExpandedSections={setExpandedSections}
          />
          <br></br>
          <FormControlLabel
            label="Use RDF for Recommendations"
            control={
              <Switch
                checked={useRdfRecommendations}
                onChange={(e) => setUseRdfRecommendations(e.target.checked)}
                color="primary"
              />
            }
          />
          <br></br><br></br>
          <FormControlLabel
            label="Use RDF for Filtering Game State"
            control={
              <Switch
                checked={useRdfGameState}
                onChange={(e) => setUseRdfGameState(e.target.checked)}
                color="primary"
              />
            }
          />
        </Box>

        <Box sx={{ flex: "3 1 0px", p: 2, overflow: "hidden" }}>
          <ImageGallery 
            images={images} 
            isLoading={isLoadingImages}
            onPageChange={(visiblePuzzleIds) => {
              if (searchOrFilterPerformed) {
                fetchRecommendations(visiblePuzzleIds);
              }
            }}
          />
        </Box>

        <Box sx={{
          flex: "1 1 0px",
          bgcolor: "grey.200",
          minWidth: 50,
          maxWidth: 300,
          p: 2,
          overflow: "hidden"
        }}>
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
