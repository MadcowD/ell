import React, { useMemo, useRef, useEffect, useState, useCallback } from 'react';
import {  FiChevronDown, FiArrowUp, FiArrowDown, FiChevronLeft, FiChevronRight, FiChevronsLeft, FiChevronsRight } from 'react-icons/fi';
import { HierarchicalTableProvider, useHierarchicalTable } from './HierarchicalTableContext';
import { Checkbox } from "components/common/Checkbox"
import { debounce } from 'lodash';

// Update the SmoothLine component
const SmoothLine = ({ index, startX, startY, endX: endXPreprocess, special, endY, color, animated, opacity, offset }) => {
  const endX = endXPreprocess;

  const endYAdjustment = !animated ? 0 : -5
  const midX = startX - offset;

  const path = `
    M ${startX} ${startY}
    C ${midX} ${startY}, ${midX} ${startY}, ${midX} ${(startY + endY) / 2}
    S ${midX} ${endY}, ${endX + endYAdjustment} ${endY}
  `;
  const duration = '1s';
  const randomId = useMemo(() => Math.random().toString(36).substring(7), []);

  return (
    <g>
      <path
        d={path}
        stroke={color}
        fill="none"
        strokeWidth="1"
        strokeDasharray={animated ? "5,5" : "none"}
        className={`transition-all duration-${duration} ease-in-out ${animated ? "animated-dash" : ""}`}
        opacity={opacity}
      />
      {animated && (
        <>
          <path
            d={path}
            stroke={color}
            fill="none"
            strokeWidth="2"
            strokeDasharray="5,5"
            className={`animated-dash-overlay transition-opacity duration-${duration} ease-in-out`}
            opacity={opacity}
          />
          <marker
            id={`arrowhead-${randomId}`}
            markerWidth="6"
            markerHeight="4"
            refX="0"
            refY="2"
            orient="auto"
          >
            <polygon points="0 0, 6 2, 0 4" fill={color} />
          </marker>
          <path
            d={path}
            stroke={color}
            fill="none"
            strokeWidth="1.5"
            markerEnd={`url(#arrowhead-${randomId})`}
            className={`animated-dash transition-opacity duration-${duration} ease-in-out`}
            opacity={opacity}
          />
        </>
      )}
    </g>
  );
};



const TableRow = ({ item, schema, level = 0, onRowClick, columnWidths, updateWidth, rowClassName, setRowRef, links, linkColumn, showHierarchical, statusColumn }) => {
  const { expandedRows, selectedRows, toggleRow, toggleSelection, isItemSelected, setHoveredRow, sortedData, hoveredRow } = useHierarchicalTable();
  const hasChildren = item.children && item.children.length > 0;
  const isExpanded = expandedRows[item.id];
  const isSelected = isItemSelected(item);
  const [isNew, setIsNew] = useState(true);

  const customRowClassName = rowClassName ? rowClassName(item) : '';

  useEffect(() => {
    if (isNew) {
      const timer = setTimeout(() => setIsNew(false), 200);
      return () => clearTimeout(timer);
    }
  }, [isNew]);

  const primaryColumnRef = useRef(null);
  
  useEffect(() => {
    if (!primaryColumnRef.current) return;

    const table = primaryColumnRef.current.closest('table');
    let tableRect = table.getBoundingClientRect();

    const updatePosition = () => {
      requestAnimationFrame(() => {
        if (!primaryColumnRef.current) return;
        const rowRect = primaryColumnRef.current.getBoundingClientRect();
        const relativeX = rowRect.left - tableRect.left;
        const relativeY = rowRect.top - tableRect.top + rowRect.height / 2;
        setRowRef(item.id, { id: item.id, x: relativeX, y: relativeY, visible: true });
      });
    };

    const debouncedUpdatePosition = debounce(updatePosition, 100);

    // Shared ResizeObserver
    const resizeObserver = new ResizeObserver(() => {
      tableRect = table.getBoundingClientRect(); // Update tableRect
      debouncedUpdatePosition();
    });

    // Observe only the table
    resizeObserver.observe(table);

    // Initial position update
    updatePosition();

    // Clean up
    return () => {
      setRowRef(item.id, {visible: false});
      resizeObserver.disconnect();
      debouncedUpdatePosition.cancel();
    };
  }, [item.id, setRowRef]);

  return (
    <React.Fragment>
      <tr
        className={`border-b border-gray-800 hover:bg-gray-800/30 cursor-pointer transition-all duration-500 ease-in-out 
          ${isSelected ? 'bg-blue-900/30' : ''} 
          ${customRowClassName}
          ${isNew ? 'animate-fade-in bg-green-900/30' : ''}`}
        onClick={() => {
          if (onRowClick) onRowClick(item, toggleRow);
        }}
        onMouseEnter={() => setHoveredRow(item.id)}
        onMouseLeave={() => setHoveredRow(null)}
      >
        <td className="py-3 px-4 w-12">
          <Checkbox
            checked={isSelected}
            onCheckedChange={(checked) => toggleSelection(item, checked)}
            onClick={(e) => e.stopPropagation()}
          />
        </td>
        <td className={`py-3 ${showHierarchical ? 'px-4 w-12' : 'px-2 w-8'} relative`}>
          {showHierarchical ? (
            <div className="flex items-center" style={{ paddingLeft: `${level * 20}px` }}>
              {hasChildren && (
                <span onClick={(e) => { e.stopPropagation(); toggleRow(item.id); }}>
                  {isExpanded ? <FiChevronDown className="text-gray-400 text-base" /> : <FiChevronRight className="text-gray-400 text-base" />}
                </span>
              )}
            </div>
          ) : statusColumn?.render ? (
            <div className="flex justify-center">
              {statusColumn.render(item)}
            </div>
          ) : null}
        </td>
        {schema.columns.map((column, index) => {
          const content = column.render ? column.render(item, index, { 
            expanded: isExpanded,
            isHovered: hoveredRow === item.id 
          }) : item[column.key];
          const maxWidth = column.maxWidth || Infinity;
          return (
            <React.Fragment key={index}>
              <td 
                className={`py-3 px-4 whitespace-nowrap overflow-hidden text-ellipsis ${column.className || ''}`}
                style={{ 
                  ...column.style,
                  maxWidth: maxWidth !== Infinity ? `${maxWidth}px` : undefined,
                  width: `${Math.min(columnWidths[column.key] || 0, maxWidth)}px`,
                }}
             
                title={typeof content === 'string' ? content : ''}
              >
                <div style={{
                  marginLeft: column.key === 'name' ? `${level * 20 + 16}px` : 0,
                  width: column.key === 'name' ? '100%' : 'auto'
                }}>
                <div ref={column.key === linkColumn ? primaryColumnRef : null}>
                  {content}
                </div>
                </div>
              </td>
            </React.Fragment>
          );
        })}
      </tr>
      {hasChildren && isExpanded && item.children.map(child => (
        <TableRow key={child.id} item={child} schema={schema} level={level + 1} onRowClick={onRowClick} columnWidths={columnWidths} updateWidth={updateWidth} rowClassName={rowClassName} setRowRef={setRowRef} links={links} linkColumn={linkColumn} showHierarchical={showHierarchical} statusColumn={statusColumn} />
      ))}
    </React.Fragment>
  );
};

const TableHeader = ({ schema, columnWidths, updateWidth, showHierarchical, statusColumn }) => {
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
        <th className={`py-2 ${showHierarchical ? 'px-4 w-12' : 'px-2 w-8'}`}>
          {showHierarchical ? (
            <FiChevronRight className="text-gray-400 text-base" />
          ) : (
            statusColumn?.header || ''
          )}
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

const TableBody = ({ schema, onRowClick, columnWidths, updateWidth, rowClassName, setRowRef, links, linkColumn, showHierarchical, statusColumn }) => {
  const { sortedData } = useHierarchicalTable();
  const [, forceUpdate] = useState({});

  useEffect(() => {
    forceUpdate({});
  }, [sortedData]);

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
          setRowRef={setRowRef}
          links={links}
          linkColumn={linkColumn}
          showHierarchical={showHierarchical}
          statusColumn={statusColumn}
        />
      ))}
    </tbody>
  );
};

const PaginationControls = ({ currentPage, totalPages, onPageChange, pageSize, totalItems }) => {
  // const startItem = currentPage * pageSize + 1;
  // const endItem = Math.min((currentPage + 1) * pageSize, totalItems);

  return (
    <div className="flex justify-between items-center mt-4 text-sm">
      <div className="text-gray-400">
        {/* Showing {startItem} to {endItem} of {totalItems} items */}
      </div>
      <div className="flex items-center">
        <button
          onClick={() => onPageChange(0)}
          disabled={currentPage === 0}
          className="p-2 rounded-md text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          title="First Page"
        >
          <FiChevronsLeft />
        </button>
        <button
          onClick={() => onPageChange(currentPage - 1)}
          disabled={currentPage === 0}
          className="p-2 rounded-md text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed ml-2"
          title="Previous Page"
        >
          <FiChevronLeft />
        </button>
        <span className="mx-4 text-gray-400">
          Page {currentPage + 1}
        </span>
        <button
          onClick={() => onPageChange(currentPage + 1)}
          disabled={currentPage === totalPages - 1}
          className="p-2 rounded-md text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed mr-2"
          title="Next Page"
        >
          <FiChevronRight />
        </button>
        <button
          onClick={() => onPageChange(totalPages - 1)}
          disabled={currentPage === totalPages - 1}
          className="p-2 rounded-md text-gray-400 hover:bg-gray-800 disabled:opacity-50 disabled:cursor-not-allowed"
          title="Last Page"
        >
          <FiChevronsRight />
        </button>
      </div>
    </div>
  );
};

const HierarchicalTable = ({ 
  schema, 
  data, 
  onRowClick, 
  onSelectionChange, 
  initialSortConfig, 
  rowClassName, 
  currentPage, 
  onPageChange, 
  pageSize, 
  totalItems, 
  omitColumns, 
  expandAll, 
  links, 
  expandedLinkColumn, 
  collapsedLinkColumn, 
  showHierarchical = true, 
  statusColumn = null,
  hierarchicalSort = false
}) => {
  const [columnWidths, setColumnWidths] = useState({});
  const [isExpanded, setIsExpanded] = useState(false);
  const [rowRefs, setRowRefs] = useState({});


  const updateWidth = (key, width, maxWidth) => {
    setColumnWidths(prev => ({
      ...prev,
      [key]: Math.min(Math.max(prev[key] || 0, width), maxWidth)
    }));
  };

  const tableRef = useRef(null);
  const [tableOffset, setTableOffset] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (tableRef.current) {
      const rect = tableRef.current.getBoundingClientRect();
      setTableOffset({ x: rect.left, y: rect.top });
    }
  }, []);

  const setRowRef = useCallback((id, ref) => {
    setRowRefs(prev => {
      if (JSON.stringify(prev[id]) === JSON.stringify(ref)) {
        return prev;
      }
      return { ...prev, [id]: ref };
    });
  }, []);

  useEffect(() => {
    const initialWidths = {};
    schema.columns.forEach(column => {
      initialWidths[column.key] = 0;
    });
    setColumnWidths(initialWidths);
  }, [schema]);

  const totalPages = Math.ceil(totalItems / pageSize);

  // Filter columns if no rows are expanded and omitColumns is provided

  const filteredSchema = useMemo(() => {
    if (omitColumns && !isExpanded) {
      return {
        ...schema,
        columns: schema.columns.filter(column => !omitColumns.includes(column.key))
      };
    }
    return schema;
  }, [schema, omitColumns, isExpanded]);

  const linkColumn = !isExpanded && omitColumns ? collapsedLinkColumn : expandedLinkColumn;


  return (
    <HierarchicalTableProvider 
      data={data} 
      schema={schema} 
      onSelectionChange={onSelectionChange}
      initialSortConfig={initialSortConfig}
      setIsExpanded={setIsExpanded}
      expandAll={expandAll}
      hierarchicalSort={hierarchicalSort}
    >
      <div className="overflow-x-auto hide-scrollbar relative" ref={tableRef}>
        <table className="w-full">
          <TableHeader 
            schema={filteredSchema} 
            columnWidths={columnWidths} 
            updateWidth={updateWidth}
            showHierarchical={showHierarchical}
            statusColumn={statusColumn}
          />
          <TableBody 
            schema={filteredSchema} 
            onRowClick={onRowClick} 
            columnWidths={columnWidths} 
            updateWidth={updateWidth}
            rowClassName={rowClassName}
            setRowRef={setRowRef}
            links={links}
            linkColumn={linkColumn}
            showHierarchical={showHierarchical}
            statusColumn={statusColumn}
          />
        </table>
        { links && 
        <svg
          className="absolute top-0 left-0 w-full h-full pointer-events-none"
          style={{ overflow: 'visible' }}
        >
          <LinkLines 
            links={links} 
            rowRefs={rowRefs} 
            tableOffset={tableOffset}
            />
          </svg>
        }
      </div>
      {onPageChange && (
        <PaginationControls
          currentPage={currentPage}
          totalPages={totalPages}
          onPageChange={onPageChange}
          pageSize={pageSize}
          totalItems={totalItems}
        />
      )}
    </HierarchicalTableProvider>
  );
};
const LinkLines = ({ links, rowRefs, tableOffset }) => {
  const { hoveredRow, expandedRows } = useHierarchicalTable();
  // Memoize the grouping and sorting of links
  const groupedLinks = useMemo(() => {
    const grouped = links?.reduce((acc, link) => {
      if (!acc[link.from]) acc[link.from] = [];
      // Check for uniqueness of the link
      const isUnique = !acc[link.from].some(existingLink => 
        existingLink.from === link.from && existingLink.to === link.to
      );
      
      if (isUnique) {
        acc[link.from].push(link);
      } else {
        console.warn(`Duplicate link found: from ${link.from} to ${link.to}`);
      }
      return acc;
    }, {});

    // Sort each group by distance
    Object.values(grouped).forEach(group => {
      group.sort((a, b) => {
        const distA = Math.abs(rowRefs[a.to]?.y - rowRefs[a.from]?.y);
        const distB = Math.abs(rowRefs[b.to]?.y - rowRefs[b.from]?.y);
        return distA - distB;
      });
    });

    return grouped;
  }, [links, rowRefs]);

  

  return links?.map((link, index) => {
    const startRow = rowRefs[link.from];
    const endRow = rowRefs[link.to];

    // Only render the link if both rows are expanded
    if (startRow && endRow && startRow?.visible && endRow?.visible) {
      const isHighlighted = hoveredRow === link.from || 
                            hoveredRow === link.to;
      const offset = (groupedLinks[link.from].indexOf(link)+ 4) * 3; // Multiply by 20 for spacing
      const color = isHighlighted
        ? (hoveredRow === link.from ? '#f97316' : '#3b82f6')  // Orange if going from, Blue if coming to
        : '#4a5568';


      // opacity at 11 outgoing links is 0.3
      // 0.5 at one 
      // 0.5/11 = 0.3 scaled so that 
      const opacity =0.7*Math.exp(-0.05033*(groupedLinks[link.from].length -1))
      
      return (
        <SmoothLine
          key={index}
          startX={startRow.x}
          startY={startRow.y}
          endX={endRow.x}
          endY={endRow.y}
          color={color}
          animated={isHighlighted}
          opacity={isHighlighted ? 1 : opacity}
          offset={offset}
        />
      );
    }
    
    return null;
  });
};

export default HierarchicalTable;