import React, { useState } from 'react';
import SearchBar from './components/SearchBar';
import FilterPanel from './components/FilterPanel';
import ImageGallery from './components/ImageGallery';

const ChessOntologyApp = () => {
  const [images, setImages] = useState([]);

  return (
    <div>
      <h1>Chess Board Visualizer</h1>
      <SearchBar setImages={setImages} />
      <FilterPanel setImages={setImages} />
      <ImageGallery images={images} />
    </div>
  );
};

export default ChessOntologyApp;