import React, { useMemo, useRef, useEffect, useState } from 'react';
import { FiChevronRight, FiChevronDown, FiArrowUp, FiArrowDown } from 'react-icons/fi';
import { HierarchicalTableProvider, useHierarchicalTable } from './HierarchicalTableContext';
import { Checkbox } from "components/common/Checkbox"


const TableRow = ({ item, schema, level = 0, onRowClick, columnWidths, updateWidth, rowClassName }) => {
  const { expandedRows, selectedRows, toggleRow, toggleSelection, isItemSelected } = useHierarchicalTable();
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = expandedRows[item.id];
  const isSelected = isItemSelected(item);

  const customRowClassName = rowClassName ? rowClassName(item) : '';

  return (
    <React.Fragment>
      <tr
        className={`border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer transition-colors duration-500 ease-in-out ${isSelected ? 'bg-blue-900/30' : ''} ${customRowClassName}`}
        onClick={() => {
          if (onRowClick) onRowClick(item);
        }}
      >
        <td className="py-3 px-4 w-12">
          <Checkbox
            checked={isSelected}
            onCheckedChange={(checked) => toggleSelection(item, checked)}
            onClick={(e) => e.stopPropagation()}
          />
        </td>
        <td className="py-3 px-4 w-12" style={{ paddingLeft: `${level * 20 + 16}px` }}>
          {hasChildren && (
            <span onClick={(e) => { e.stopPropagation(); toggleRow(item.id); }}>
              {isExpanded ? <FiChevronDown className="text-gray-400 text-base" /> : <FiChevronRight className="text-gray-400 text-base" />}
            </span>
          )}
        </td>
        {schema.columns.map((column, index) => {
          const content = column.render ? column.render(item) : item[column.key];
          const maxWidth = column.maxWidth || Infinity;
          return (
            <React.Fragment key={index}>
              <td 
                className={`py-3 px-4 whitespace-nowrap overflow-hidden text-ellipsis ${column.className || ''}`}
                style={{ 
                  ...column.style,
                  maxWidth: maxWidth !== Infinity ? `${maxWidth}px` : undefined,
                  width: `${Math.min(columnWidths[column.key] || 0, maxWidth)}px`
                }}
                title={typeof content === 'string' ? content : ''}
              >
                {content}
              </td>
            </React.Fragment>
          );
        })}
      </tr>
      {hasChildren && isExpanded && item.children.map(child => (
        <TableRow key={child.id} item={child} schema={schema} level={level + 1} onRowClick={onRowClick} columnWidths={columnWidths} updateWidth={updateWidth} rowClassName={rowClassName} />
      ))}
    </React.Fragment>
  );
};

const TableHeader = ({ schema, columnWidths, updateWidth }) => {
  const { isAllSelected, toggleAllSelection, sortConfig, onSort } = useHierarchicalTable();

  return (
    <thead>
      <tr className="text-left text-xs text-gray-400 border-t border-b border-l border-r border-gray-800 bg-gray-800/30">
        <th className="py-2 px-4 w-12">
          <Checkbox
            checked={isAllSelected()}
            onCheckedChange={(checked) => toggleAllSelection(checked)}
          />
        </th>
        <th className="py-2 px-4 w-12">
          <FiChevronRight className="text-gray-400 text-base" />
        </th>
        {schema.columns.map((column, index) => {
          const maxWidth = column.maxWidth || Infinity;
          const isSorted = sortConfig.key === column.key;
          const sortIcon = isSorted ? (sortConfig.direction === 'asc' ? <FiArrowUp /> : <FiArrowDown />) : null;
          return (
            <React.Fragment key={index}>
              <th 
                className={`py-2 px-4 whitespace-nowrap overflow-hidden text-ellipsis ${column.headerClassName || ''} ${column.sortable ? 'cursor-pointer' : ''}`}
                style={{ 
                  maxWidth: maxWidth !== Infinity ? `${maxWidth}px` : undefined,
                  width: `${Math.min(columnWidths[column.key] || 0, maxWidth)}px`,
                  ...column.headerStyle
                }}
                onClick={() => column.sortable && onSort(column.key)}
              >
                <div className="flex items-center justify-between">
                  <span>{column.header}</span>
                  {sortIcon}
                </div>
              </th>
            </React.Fragment>
          );
        })}
      </tr>
    </thead>
  );
};

const TableBody = ({ schema, onRowClick, columnWidths, updateWidth, rowClassName }) => {
  const { sortedData } = useHierarchicalTable();

  return (
    <tbody>
      {sortedData.map(item => (
        <TableRow 
          key={item.id} 
          item={item} 
          schema={schema} 
          onRowClick={onRowClick} 
          columnWidths={columnWidths} 
          updateWidth={updateWidth}
          rowClassName={rowClassName}
        />
      ))}
    </tbody>
  );
};

const HierarchicalTable = ({ schema, data, onRowClick, onSelectionChange, initialSortConfig, rowClassName }) => {
  const [columnWidths, setColumnWidths] = useState({});
  const updateWidth = (key, width, maxWidth) => {
    setColumnWidths(prev => ({
      ...prev,
      [key]: Math.min(Math.max(prev[key] || 0, width), maxWidth)
    }));
  };

  useEffect(() => {
    const initialWidths = {};
    schema.columns.forEach(column => {
      initialWidths[column.key] = 0;
    });
    setColumnWidths(initialWidths);
  }, [schema]);

  return (
    <HierarchicalTableProvider 
      data={data} 
      onSelectionChange={onSelectionChange}
      initialSortConfig={initialSortConfig}
    >
      <div className="overflow-x-auto hide-scrollbar">
        <table className="w-full">
          <TableHeader 
            schema={schema} 
            columnWidths={columnWidths} 
            updateWidth={updateWidth} 
          />
          <TableBody 
            schema={schema} 
            onRowClick={onRowClick} 
            columnWidths={columnWidths} 
            updateWidth={updateWidth}
            rowClassName={rowClassName}
          />
        </table>
      </div>
    </HierarchicalTableProvider>
  );
};

export default HierarchicalTable;