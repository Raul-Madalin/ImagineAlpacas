import React from "react";
import { Box, Grid, Card, CardMedia, CardContent, Typography } from "@mui/material";

const ImageGallery = ({ images }) => {
  return (
    <Grid container spacing={2}>
      {images.length === 0 ? (
        <Typography variant="body1">No images found.</Typography>
      ) : (
        images.map((image, index) => (
          <Grid item xs={4} key={index}>
            <Card>
              <CardMedia
                component="img"
                image={`http://localhost:5000/images/${image.filename}`}
                alt={`Chess Position ${index + 1}`}
                sx={{ width: "100%", height: "auto" }}
              />
              <CardContent>
                <Box display="flex" flexGrow={1} justifyContent="center">
                  <Typography variant="h6">Puzzle ID: {image.puzzle_id}</Typography>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))
      )}
    </Grid>
  );
};

export default ImageGallery;
