import React, { useState } from 'react';

const ImageGallery = ({ images }) => {
  const [currentPage, setCurrentPage] = useState(1);
  const imagesPerPage = 10;

  const indexOfLastImage = currentPage * imagesPerPage;
  const indexOfFirstImage = indexOfLastImage - imagesPerPage;
  const currentImages = images.slice(indexOfFirstImage, indexOfLastImage);

  const nextPage = () => {
    if (currentPage < Math.ceil(images.length / imagesPerPage)) {
      setCurrentPage(currentPage + 1);
    }
  };

  const prevPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  return (
    <div>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)' }}>
        {currentImages.map((image, index) => (
          <img
            key={index}
            src={`http://127.0.0.1:5000/images/${image.filename}`}
            alt={`Chessboard ${index}`}
            style={{ width: '100px', height: '100px' }}
          />
        ))}
      </div>
      <div>
        <button onClick={prevPage} disabled={currentPage === 1}>
          Previous
        </button>
        <button
          onClick={nextPage}
          disabled={currentPage >= Math.ceil(images.length / imagesPerPage)}
        >
          Next
        </button>
      </div>
    </div>
  );
};

export default ImageGallery;