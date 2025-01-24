import React, { useState } from 'react';
import axios from 'axios';

const SearchBar = ({ setImages }) => {
  const [query, setQuery] = useState('');

  const handleSearch = async () => {
    try {
      const response = await axios.get('http://127.0.0.1:5000/search', {
        params: { query },
      });
      setImages(response.data); // Update the Image Gallery
    } catch (error) {
      console.error('Error fetching search results:', error);
    }
  };

  return (
    <div>
      <input
        type="text"
        placeholder="Search pieces (e.g., Rook Queen)"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};

export default SearchBar;
