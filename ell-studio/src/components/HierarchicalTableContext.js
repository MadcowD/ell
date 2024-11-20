import React, { createContext, useContext, useState, useCallback, useMemo, useEffect } from 'react';

const HierarchicalTableContext = createContext();

export const useHierarchicalTable = () => useContext(HierarchicalTableContext);

export const HierarchicalTableProvider = ({ children, data, schema, onSelectionChange, initialSortConfig, setIsExpanded, expandAll, hierarchicalSort }) => {
  const [expandedRows, setExpandedRows] = useState({});
  const [selectedRows, setSelectedRows] = useState({});
  const [sortConfig, setSortConfig] = useState(initialSortConfig || { key: null, direction: 'asc' });
  const [hoveredRow, setHoveredRow] = useState(null);

  useEffect(() => {
    const allParentRowsCollapsed = data.every(item => !expandedRows[item.id]);
    setIsExpanded(!allParentRowsCollapsed);
  }, [expandedRows, setIsExpanded, data]);

  // expandall specifies if the initial state of row is expanded.
  useEffect(() => {
    if (expandAll) {
      data.forEach(item => {
        if (!(item.id in expandedRows)) {
          setExpandedRows(prev => ({ ...prev, [item.id]: true }));
        }
      });
    }
  }, [data, expandAll, expandedRows]);
  
  const toggleRow = useCallback((rowId) => {
    setExpandedRows(prev => ({
      ...prev,
      [rowId]: !prev[rowId]
    }));
  }, []);

  const isItemSelected = useCallback((item) => {
    if (!selectedRows[item.id]) return false;
    if (item.children) {
      return item.children.every(child => isItemSelected(child));
    }
    return true;
  }, [selectedRows]);

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
  }, [data, isItemSelected]);

  const onSort = useCallback((key) => {
    setSortConfig((prevConfig) => ({
      key,
      direction: prevConfig.key === key && prevConfig.direction === 'asc' ? 'desc' : 'asc',
    }));
  }, []);

  const sortedData = useMemo(() => {
    if (!sortConfig.key) return data;

    const sortItems = (items) => {
      return [...items].sort((a, b) => {
        const column = schema?.columns?.find(col => col.key === sortConfig.key);
        const sortFn = column?.sortFn;

        const comparison = sortFn
          ? (sortConfig.direction === 'asc' ? sortFn(a, b) : sortFn(b, a))
          : defaultCompare(a, b);

        return comparison;
      }).map(item => ({
        ...item,
        // Recursively sort children if hierarchicalSort is enabled
        children: hierarchicalSort && item.children 
          ? sortItems(item.children)
          : item.children
      }));
    };

    const defaultCompare = (a, b) => {
      if (a[sortConfig.key] < b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? -1 : 1;
      }
      if (a[sortConfig.key] > b[sortConfig.key]) {
        return sortConfig.direction === 'asc' ? 1 : -1;
      }
      return 0;
    };

    return sortItems(data);
  }, [data, sortConfig, schema, hierarchicalSort]);

  useEffect(() => {
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
    hoveredRow,
    setHoveredRow,
  };

  return (
    <HierarchicalTableContext.Provider value={value}>
      {children}
    </HierarchicalTableContext.Provider>
  );
};