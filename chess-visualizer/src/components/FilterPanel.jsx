import React, { useState, useEffect } from "react";
import { Box, Button, FormControl, FormControlLabel, Checkbox, Typography } from "@mui/material";

const FilterPanel = ({ onFilter }) => {
  const [selectedFilters, setSelectedFilters] = useState({
    rooks: [],
    queens: [],
    bishops: [],
    knights: [],
    pawns: [],
  });

  const [expandedSections, setExpandedSections] = useState({
    rooks: false,
    queens: false,
    bishops: false,
    knights: false,
    pawns: false,
  });

  const pieceFilterOptions = {
    rooks: [0, 1, 2, "3+"],
    queens: [0, 1, "2+"],
    bishops: [0, 1, 2, "3+"],
    knights: [0, 1, 2, "3+"],
    pawns: [0, 1, 2, 3, 4, 5, 6, 7, 8, "9+"],
  };

  const handleCheckboxChange = (piece, value) => {
    setSelectedFilters((prev) => {
      const currentSelection = prev[piece];
      const newSelection = currentSelection.includes(value)
        ? currentSelection.filter((item) => item !== value) // Uncheck
        : [...currentSelection, value]; // Check
      return { ...prev, [piece]: newSelection };
    });
  };

  const toggleSection = (piece) => {
    setExpandedSections((prev) => ({
      ...prev,
      [piece]: !prev[piece], // Toggle the section's expanded state
    }));
  };


  useEffect(() => {
    
  }, [selectedFilters]);

  return (
    <div className="filters-container">
      {Object.keys(pieceFilterOptions).map((piece) => (
        <div key={piece} className="filter-group">
          {/* Collapsible Header */}
          <div
            style={{
              display: "flex",
              justifyContent: "space-between",
              alignItems: "center",
              cursor: "pointer",
              backgroundColor: "#f0f0f0",
              padding: "10px",
              borderRadius: "5px",
              marginBottom: "5px",
            }}
            onClick={() => toggleSection(piece)}
          >
            <h4 style={{ margin: 0 }}>{piece.charAt(0).toUpperCase() + piece.slice(1)}</h4>
            <span>{expandedSections[piece] ? "▲" : "▼"}</span>
          </div>

          {/* Collapsible Content */}
          {expandedSections[piece] && (
            <div style={{ marginLeft: "10px", marginBottom: "10px" }}>
              {pieceFilterOptions[piece].map((option) => (
                <label
                  key={`${piece}-${option}`}
                  style={{ display: "block", margin: "5px 0" }}
                >
                  <input
                    type="checkbox"
                    value={option}
                    checked={selectedFilters[piece].includes(option)}
                    onChange={() => handleCheckboxChange(piece, option)}
                  />
                  {option}
                </label>
              ))}
            </div>
          )}
        </div>
      ))}
      <Button
        variant="contained"
        color="primary"
        style={{ marginTop: "10px", width: "100%" }}
        onClick={() => onFilter(selectedFilters)}
      >
        Apply Filters
      </Button>
    </div>
  );
};


export default FilterPanel;
