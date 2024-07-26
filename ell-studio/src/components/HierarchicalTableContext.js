import React, { createContext, useContext, useState, useCallback, useMemo } from 'react';

const HierarchicalTableContext = createContext();

export const useHierarchicalTable = () => useContext(HierarchicalTableContext);

export const HierarchicalTableProvider = ({ children, data, onSelectionChange, initialSortConfig }) => {
  const [expandedRows, setExpandedRows] = useState({});
  const [selectedRows, setSelectedRows] = useState({});
  const [sortConfig, setSortConfig] = useState(initialSortConfig || { key: null, direction: 'asc' });

  const toggleRow = useCallback((rowId) => {
    setExpandedRows(prev => ({
      ...prev,
      [rowId]: !prev[rowId]
    }));
  }, []);

  const toggleSelection = useCallback((item, isSelected) => {
    setSelectedRows(prev => {
      const newSelectedRows = { ...prev };
      const updateSelection = (currentItem, status) => {
        newSelectedRows[currentItem.id] = status;
        if (currentItem.children) {
          currentItem.children.forEach(child => updateSelection(child, status));
        }
      };
      updateSelection(item, isSelected);
      return newSelectedRows;
    });
  }, []);

  const toggleAllSelection = useCallback((isSelected) => {
    const newSelectedRows = {};
    const updateAllSelection = (items) => {
      items.forEach(item => {
        newSelectedRows[item.id] = isSelected;
        if (item.children) {
          updateAllSelection(item.children);
        }
      });
    };
    updateAllSelection(data);
    setSelectedRows(newSelectedRows);
  }, [data]);

  const isAllSelected = useCallback(() => {
    return data.every(item => isItemSelected(item));
  }, [data, selectedRows]);

  const isItemSelected = useCallback((item) => {
    if (!selectedRows[item.id]) return false;
    if (item.children) {
      return item.children.every(child => isItemSelected(child));
    }
    return true;
  }, [selectedRows]);

  const onSort = useCallback((key) => {
    setSortConfig((prevConfig) => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;
    return [...data].sort((a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    });
  }, [data, sortConfig]);

  React.useEffect(() => {
    if (onSelectionChange) {
      onSelectionChange(selectedRows);
    }
  }, [selectedRows, onSelectionChange]);

  const value = {
    expandedRows,
    selectedRows,
    toggleRow,
    toggleSelection,
    toggleAllSelection,
    isAllSelected,
    isItemSelected,
    sortConfig,
    onSort,
    sortedData,
  };

  return (
    <HierarchicalTableContext.Provider value={value}>
      {children}
    </HierarchicalTableContext.Provider>
  );
};