import React from "react";
import { Box, Typography, Card, CardMedia, CardContent, CircularProgress } from "@mui/material";

const Recommandations = ({ recommendations, isLoading }) => {
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box>
      {recommendations.length > 0 ? (
        recommendations.map((image, index) => (
          // <Box key={index} sx={{ mb: 2 }}>
          //   <img
          //     src={`http://localhost:5000/images/${image.filename}`} 
          //     alt={`Chess Position ${image.puzzle_id}`}
          //     style={{ width: "100%", borderRadius: "8px" }}
          //   />
          //   <Typography variant="body2">Puzzle: {image.puzzle_id}</Typography>
          // </Box>
          <Card>
            <CardMedia
              component="img"
              image={`http://localhost:5000/images/${image.filename}`}
              alt={`Chess Position ${image.puzzle_id}`}
              sx={{ width: "100%", height: "auto" }}
            />
            <CardContent>
              <Box display="flex" flexGrow={1} justifyContent="center">
                <Typography variant="h6">Puzzle {image.puzzle_id}</Typography>
              </Box>
            </CardContent>
          </Card>
        ))
      ) : (
        <Typography variant="h8" sx={{ mt: 2, color: "gray" }}>
          No recommendations available.
        </Typography>
      )}
    </Box>
  );
};

export default Recommandations;
