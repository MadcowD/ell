import React from 'react';

function SearchAndFiltersBar({ searchQuery, setSearchQuery }) {
  return (
    <div className="mb-4 flex gap-4 items-center">
      <div className="flex-1">
        <input
          type="text"
          placeholder="Search results..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          className="w-full px-4 py-2 rounded-md border border-border bg-background text-foreground focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>
      {/* We can add more filters here later */}
    </div>
  );
}

export default SearchAndFiltersBar; 