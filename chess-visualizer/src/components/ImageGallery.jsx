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
    imagesPerPage = 8;
  } else if (isMdUp) {
    imagesPerPage = 6;
  } else if (isSmUp) {
    imagesPerPage = 4;
  } else {
    imagesPerPage = 2;
  }

  // 3) If loading, show a spinner
  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" height="100%">
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
      {/* RDFa Vocabulary Declaration */}
      <div vocab="http://schema.org/" typeof="CollectionPage">

        {selectedImages.length === 0 && (
          <Typography variant="body1">No images found.</Typography>
        )}

        {!!selectedImages.length && (
          <Grid container spacing={2} wrap="wrap" property="mainEntity" typeof="ItemList">
            {selectedImages.map((image, index) => (
              <Grid
                item
                xs={12}
                sm={6}
                md={4}
                lg={3}
                key={index}
                sx={{ display: "flex", justifyContent: "center" }}
              >
                <Card
                  typeof="ImageObject"
                  resource={image.metadata?.contentUrl} // RDFa resource
                  sx={{
                    maxWidth: 400,
                    width: "100%",
                  }}
                >
                  {/* Image with RDFa attributes */}
                  <CardMedia
                    component="img"
                    property="contentUrl"
                    src={image.metadata?.contentUrl}
                    alt={`Chess Position ${image.metadata?.identifier}`}
                    sx={{
                      aspectRatio: "1 / 1",
                      objectFit: "contain",
                      maxWidth: "400px",
                      width: "100%",
                    }}
                  />
                  <CardContent>
                    <Typography variant="h6" align="center" property="name">
                      Puzzle <span property="identifier">{image.metadata?.identifier}</span>
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
      </div>
    </Box>
  );
}
