import React, { useState } from "react";
import { Box, Grid, Card, CardMedia, CardContent, Typography, Button } from "@mui/material";

const ImageGallery = ({ images, onPageChange }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 6;

  // Calculate total pages
  const totalPages = Math.ceil(images.length / imagesPerPage);

  // Get images for the current page
  const startIndex = (currentPage - 1) * imagesPerPage;
  const selectedImages = images.slice(startIndex, startIndex + imagesPerPage);

  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);

    // Call recommendations only when changing pages
    const nextVisiblePuzzleIds = images.slice((newPage - 1) * imagesPerPage, newPage * imagesPerPage)
      .map((img) => img.puzzle_id);
    onPageChange(nextVisiblePuzzleIds);
  };

  return (
    <Box>
      <Grid container spacing={2}>
        {selectedImages.length === 0 ? (
          <Typography variant="body1">No images found.</Typography>
        ) : (
          selectedImages.map((image, index) => (
            <Grid item xs={4} key={index}>
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
            </Grid>
          ))
        )}
      </Grid>

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" mt={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handlePageChange(currentPage - 1)}
            disabled={currentPage === 1}
            sx={{ mr: 2 }}
          >
            Previous
          </Button>
          <Typography variant="body1">
            Page {currentPage} of {totalPages}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handlePageChange(currentPage + 1)}
            disabled={currentPage === totalPages}
            sx={{ ml: 2 }}
          >
            Next
          </Button>
        </Box>
      )}
    </Box>
  );
};

export default ImageGallery;
