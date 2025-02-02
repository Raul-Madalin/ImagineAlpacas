import React, { useState } from "react";
import {
  Box,
  Grid,
  Card,
  CardMedia,
  CardContent,
  Typography,
  Button,
  CircularProgress,
  useMediaQuery,
  useTheme,
} from "@mui/material";

export default function ImageGallery({ images, isLoading, onPageChange }) {
  const [currentPage, setCurrentPage] = useState(1);

  // 1) Check breakpoints
  const theme = useTheme();
  const isLgUp = useMediaQuery(theme.breakpoints.up("lg")); // >= lg
  const isMdUp = useMediaQuery(theme.breakpoints.up("md")); // >= md
  const isSmUp = useMediaQuery(theme.breakpoints.up("sm")); // >= sm

  // 2) Decide how many images to show per page based on screen size
  let imagesPerPage;
  if (isLgUp) {
    // Large desktop or bigger, e.g. 4 columns => 2 rows => 8 total
    imagesPerPage = 8;
  } else if (isMdUp) {
    // Medium screens => 3 columns => 2 rows => 6 total
    imagesPerPage = 6;
  } else if (isSmUp) {
    // Small screens => 2 columns => maybe 2 or 3 rows => you pick
    imagesPerPage = 4;
  } else {
    // XS screens => just 1 column => maybe 2 rows => 2 images
    imagesPerPage = 2;
  }

  // 3) If loading, spinner
  if (isLoading) {
    return (
      <Box
        display="flex"
        justifyContent="center"
        alignItems="center"
        height="100%"
      >
        <CircularProgress />
      </Box>
    );
  }

  // 4) Compute total pages & clamp current page
  const totalPages = Math.ceil(images.length / imagesPerPage);
  const safePage = Math.min(currentPage, totalPages || 1);
  if (safePage !== currentPage) {
    setCurrentPage(safePage);
  }

  // 5) Slice images for this page
  const startIndex = (safePage - 1) * imagesPerPage;
  const selectedImages = images.slice(startIndex, startIndex + imagesPerPage);

  // 6) Handle pagination
  const handlePageChange = (newPage) => {
    setCurrentPage(newPage);
    const nextIds = images
      .slice((newPage - 1) * imagesPerPage, newPage * imagesPerPage)
      .map((img) => img.puzzle_id);
    onPageChange(nextIds);
  };

  return (
    <Box sx={{ width: "100%", height: "100%", p: 2, overflow: "hidden" }}>
      {selectedImages.length === 0 && (
        <Typography variant="body1">No images found.</Typography>
      )}

      {!!selectedImages.length && (
        <Grid container spacing={2} wrap="wrap">
          {selectedImages.map((image, index) => (
            <Grid
              item
              xs={12}  // 1 col on extra-small
              sm={6}   // 2 cols on small
              md={4}   // 3 cols on medium
              lg={3}   // 4 cols on large
              key={index}
              sx={{ display: "flex", justifyContent: "center" }}
            >
              <Card
                sx={{
                  maxWidth: 400,
                  width: "100%", // fill the grid cell
                }}
              >
                <CardMedia
                  component="img"
                  image={`http://localhost:5000/images/${image.filename}`}
                  alt={`Chess Position ${image.puzzle_id}`}
                  sx={{
                    aspectRatio: "1 / 1", 
                    objectFit: "contain",
                    maxWidth: "400px",
                    width: "100%",
                  }}
                />
                <CardContent>
                  <Typography variant="h6" align="center">
                    Puzzle {image.puzzle_id}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Pagination */}
      {totalPages > 1 && (
        <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handlePageChange(safePage - 1)}
            disabled={safePage === 1}
            sx={{ mr: 2 }}
          >
            Previous
          </Button>
          <Typography variant="body1">
            Page {safePage} of {totalPages}
          </Typography>
          <Button
            variant="contained"
            color="primary"
            onClick={() => handlePageChange(safePage + 1)}
            disabled={safePage === totalPages}
            sx={{ ml: 2 }}
          >
            Next
          </Button>
        </Box>
      )}
    </Box>
  );
}
