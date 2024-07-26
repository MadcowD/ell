import React, { createContext, useContext, useState, useCallback } from 'react';

const HierarchicalTableContext = createContext();

export const useHierarchicalTable = () => useContext(HierarchicalTableContext);

export const HierarchicalTableProvider = ({ children, data, onSelectionChange }) => {
  const [expandedRows, setExpandedRows] = useState({});
  const [selectedRows, setSelectedRows] = useState({});

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
  };

  return (
    <HierarchicalTableContext.Provider value={value}>
      {children}
    </HierarchicalTableContext.Provider>
  );
};