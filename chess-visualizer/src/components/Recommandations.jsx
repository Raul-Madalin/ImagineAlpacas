import React, { useState, useEffect, useRef } from "react";
import {
  Box,
  Typography,
  Card,
  CardMedia,
  CardContent,
  CircularProgress
} from "@mui/material";

// Minimum/Maximum puzzle size in px
const MIN_SIZE = 200;
const MAX_SIZE = 400;

// Vertical gap between puzzles
const ITEM_SPACING_PX = 16;
// If p={2}, that’s 16px top + 16px bottom => total 32px vertical
const VERTICAL_PADDING_PX = 32;

const Recommandations = ({ recommendations, isLoading }) => {
  const containerRef = useRef(null);
  const [visibleRecs, setVisibleRecs] = useState([]);

  useEffect(() => {
    function updateLayout() {
      if (!containerRef.current) return;
      const { offsetWidth, offsetHeight } = containerRef.current;
      if (!offsetWidth || !offsetHeight) return;

      // The puzzle’s width is clamped between MIN_SIZE..offsetWidth..MAX_SIZE
      // Then the puzzle’s height is the same (square).
      const puzzleSize = Math.min(Math.max(offsetWidth, MIN_SIZE), MAX_SIZE);

      // Usable vertical space, minus padding
      const usableHeight = offsetHeight - VERTICAL_PADDING_PX;

      let usedHeight = 0;
      const fitting = [];

      // Try adding recommendations one by one
      for (let i = 0; i < recommendations.length; i++) {
        // If not the first item, we add spacing
        const extraSpace = i === 0 ? 0 : ITEM_SPACING_PX;
        const needed = usedHeight + extraSpace + puzzleSize;
        if (needed <= usableHeight) {
          // It fits
          fitting.push(recommendations[i]);
          usedHeight = needed;
        } else {
          // No more items can fit fully, so break
          break;
        }
      }

      setVisibleRecs(fitting);
    }

    updateLayout(); // run once on mount
    window.addEventListener("resize", updateLayout);
    return () => window.removeEventListener("resize", updateLayout);
  }, [recommendations]);

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box
      ref={containerRef}
      sx={{
        width: "100%",
        height: "100%",
        p: 2,
        boxSizing: "border-box",
        // We'll stack them in a column, and skip any that don't fit:
        display: "flex",
        flexDirection: "column",
        gap: 2,
        overflow: "hidden", // or 'auto' if you want a scrollbar
      }}
    >
      <Typography variant="h6">Recommended puzzles:</Typography>

      {visibleRecs.length > 0 ? (
        visibleRecs.map((rec) => (
          <Card
            key={rec.puzzle_id}
            sx={{
              // same constraints as the gallery
              maxWidth: 400,
              width: "clamp(200px, 100%, 400px)",
              mx: "auto", // center horizontally if there's leftover space
            }}
          >
            <CardMedia
              component="img"
              image={`http://localhost:5000/images/${rec.filename}`}
              alt={`Chess Position ${rec.puzzle_id}`}
              sx={{
                // Keep puzzle images square
                aspectRatio: "1 / 1",
                objectFit: "contain",
                width: "100%",
                maxWidth: 400,
              }}
            />
            <CardContent>
              <Typography variant="h6" align="center">
                Puzzle {rec.puzzle_id}
              </Typography>
            </CardContent>
          </Card>
        ))
      ) : (
        <Typography color="gray" sx={{ mt: 1 }}>
          No recommendations available.
        </Typography>
      )}
    </Box>
  );
};

export default Recommandations;
