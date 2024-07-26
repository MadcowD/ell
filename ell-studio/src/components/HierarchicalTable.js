import React, { useMemo, useRef, useEffect, useState } from 'react';
import { FiChevronRight, FiChevronDown } from 'react-icons/fi';
import { HierarchicalTableProvider, useHierarchicalTable } from './HierarchicalTableContext';

const MeasureCell = ({ content, onMeasure }) => {
  const ref = useRef(null);

  useEffect(() => {
    if (ref.current) {
      onMeasure(ref.current.offsetWidth);
    }
  }, [content, onMeasure]);

  return (
    <div ref={ref} style={{ position: 'absolute', visibility: 'hidden', whiteSpace: 'nowrap' }}>
      {content}
    </div>
  );
};

const TableRow = ({ item, schema, level = 0, onRowClick, columnWidths, updateWidth }) => {
  const { expandedRows, selectedRows, toggleRow, toggleSelection, isItemSelected } = useHierarchicalTable();
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = expandedRows[item.id];
  const isSelected = isItemSelected(item);

  return (
    <React.Fragment>
      <tr
        className={`border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer ${isSelected ? 'bg-blue-900/30' : ''}`}
        onClick={() => {
          if (onRowClick) onRowClick(item);
        }}
      >
        <td className="py-3 px-4 w-12">
          <input
            type="checkbox"
            checked={isSelected}
            onChange={(e) => toggleSelection(item, e.target.checked)}
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
              <MeasureCell 
                content={content} 
                onMeasure={(width) => updateWidth(column.key, width, maxWidth)} 
              />
            </React.Fragment>
          );
        })}
      </tr>
      {hasChildren && isExpanded && item.children.map(child => (
        <TableRow key={child.id} item={child} schema={schema} level={level + 1} onRowClick={onRowClick} columnWidths={columnWidths} updateWidth={updateWidth} />
      ))}
    </React.Fragment>
  );
};

const TableHeader = ({ schema, columnWidths, updateWidth }) => {
  const { isAllSelected, toggleAllSelection } = useHierarchicalTable();

  return (
    <thead>
      <tr className="text-left text-xs text-gray-400 border-t border-b border-l border-r border-gray-800 bg-gray-800/30">
        <th className="py-2 px-4 w-12">
          <input
            type="checkbox"
            checked={isAllSelected()}
            onChange={(e) => toggleAllSelection(e.target.checked)}
          />
        </th>
        <th className="py-2 px-4 w-12">
          <FiChevronRight className="text-gray-400 text-base" />
        </th>
        {schema.columns.map((column, index) => {
          const maxWidth = column.maxWidth || Infinity;
          return (
            <React.Fragment key={index}>
              <th 
                className={`py-2 px-4 whitespace-nowrap overflow-hidden text-ellipsis ${column.headerClassName || ''}`}
                style={{ 
                  maxWidth: maxWidth !== Infinity ? `${maxWidth}px` : undefined,
                  width: `${Math.min(columnWidths[column.key] || 0, maxWidth)}px`,
                  ...column.headerStyle
                }}
              >
                {column.header}
              </th>
              <MeasureCell 
                content={column.header} 
                onMeasure={(width) => updateWidth(column.key, width, maxWidth)} 
              />
            </React.Fragment>
          );
        })}
      </tr>
    </thead>
  );
};

const HierarchicalTable = ({ schema, data, onRowClick, onSelectionChange }) => {
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
    <HierarchicalTableProvider data={data} onSelectionChange={onSelectionChange}>
      <div className="overflow-x-auto">
        <table className="w-full">
          <TableHeader schema={schema} columnWidths={columnWidths} updateWidth={updateWidth} />
          <tbody>
            {data.map(item => (
              <TableRow 
                key={item.id} 
                item={item} 
                schema={schema} 
                onRowClick={onRowClick} 
                columnWidths={columnWidths} 
                updateWidth={updateWidth}
              />
            ))}
          </tbody>
        </table>
      </div>
    </HierarchicalTableProvider>
  );
};

export default HierarchicalTable;