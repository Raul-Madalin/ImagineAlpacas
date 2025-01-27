import React, { useState } from 'react';
import axios from 'axios';

const FilterPanel = ({ setImages }) => {
  const [filters, setFilters] = useState({
    pawns: '',
    rooks: '',
    queens: '',
  });

  const handleFilter = async () => {
    try {
      const response = await axios.post('http://127.0.0.1:5000/filter', filters);
      setImages(response.data); // Update the Image Gallery
    } catch (error) {
      console.error('Error applying filters:', error);
    }
  };

  return (
    <div>
      <input
        type="number"
        placeholder="Number of Pawns"
        onChange={(e) =>
          setFilters({ ...filters, pawns: `>${e.target.value}` })
        }
      />
      <input
        type="number"
        placeholder="Number of Rooks"
        onChange={(e) =>
          setFilters({ ...filters, rooks: `=${e.target.value}` })
        }
      />
      <input
        type="number"
        placeholder="Number of Queens"
        onChange={(e) =>
          setFilters({ ...filters, queens: `=${e.target.value}` })
        }
      />
      <button onClick={handleFilter}>Apply Filters</button>
    </div>
  );
};

export default FilterPanel;