import React from "react";
import { Box, Typography } from "@mui/material";

const Recommandations = () => {
  return (
    <Box>
      <Typography variant="h6" sx={{ mb: 2 }}>Recommended Chess Positions</Typography>
      {[1, 2, 3].map((_, index) => (
        <Box key={index} sx={{ mb: 2 }}>
          <img
            src={`https://via.placeholder.com/200x150?text=Chess+Rec+${index + 1}`}
            alt={`Chess Recommendation ${index + 1}`}
            style={{ width: "100%", borderRadius: "8px" }}
          />
        </Box>
      ))}
    </Box>
  );
};

export default Recommandations;
