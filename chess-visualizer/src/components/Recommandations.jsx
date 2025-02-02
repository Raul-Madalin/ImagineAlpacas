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

      const puzzleSize = Math.min(Math.max(offsetWidth, MIN_SIZE), MAX_SIZE);
      const usableHeight = offsetHeight - VERTICAL_PADDING_PX;

      let usedHeight = 0;
      const fitting = [];

      for (let i = 0; i < recommendations.length; i++) {
        const extraSpace = i === 0 ? 0 : ITEM_SPACING_PX;
        const needed = usedHeight + extraSpace + puzzleSize;
        if (needed <= usableHeight) {
          fitting.push(recommendations[i]);
          usedHeight = needed;
        } else {
          break;
        }
      }

      setVisibleRecs(fitting);
    }

    updateLayout();
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
      vocab="http://schema.org/"
      typeof="RecommendationList"
      sx={{
        width: "100%",
        height: "100%",
        p: 2,
        boxSizing: "border-box",
        display: "flex",
        flexDirection: "column",
        gap: 2,
        overflow: "hidden",
      }}
    >
      <Typography variant="h6" property="name">
        Recommended <i>{recommendations.length > 0 ? recommendations[0].dominant_feature : "feature"}</i>:
      </Typography>

      {visibleRecs.length > 0 ? (
        visibleRecs.map((rec) => (
          <Card
            key={rec.puzzle_id}
            typeof="ListItem ImageObject"
            resource={rec.metadata?.contentUrl}
            sx={{
              maxWidth: 400,
              width: "clamp(200px, 100%, 400px)",
              mx: "auto",
            }}
          >
            <CardMedia
              component="img"
              property="contentUrl"
              src={rec.metadata?.contentUrl}
              alt={`Chess Position ${rec.metadata?.identifier}`}
              sx={{
                aspectRatio: "1 / 1",
                objectFit: "contain",
                width: "100%",
                maxWidth: 400,
              }}
            />
            <CardContent>
              <Typography variant="h6" align="center" property="name">
                Puzzle <span property="identifier">{rec.metadata?.identifier}</span>
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
