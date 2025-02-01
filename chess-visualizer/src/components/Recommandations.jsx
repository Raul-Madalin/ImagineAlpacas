import React from "react";
import { Box, Typography } from "@mui/material";

const Recommandations = ({ recommendations }) => {
  return (
    <Box>
      {recommendations.length > 0 ? (
        recommendations.map((image, index) => (
          <Box key={index} sx={{ mb: 2 }}>
            <img
              src={`http://localhost:5000/images/${image.filename}`} 
              alt={`Chess Position ${image.puzzle_id}`}
              style={{ width: "100%", borderRadius: "8px" }}
            />
            <Typography variant="body2">Puzzle: {image.puzzle_id}</Typography>
          </Box>
        ))
      ) : (
        <Typography variant="body2" sx={{ mt: 2, color: "gray" }}>
          No recommendations available.
        </Typography>
      )}
    </Box>
  );
};

export default Recommandations;
