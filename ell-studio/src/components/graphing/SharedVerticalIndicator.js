import React, { useState, useEffect } from 'react';

const formatNumber = (value) => {
  if (typeof value === 'number') {
    if (Math.abs(value) < 1) {
      return value.toFixed(4);
    } else if (Math.abs(value) < 100) {
      return value.toFixed(2);
    } else {
      return value.toFixed(0);
    }
  }
  return value;
};

export const SharedVerticalIndicator = ({ visible, position, labels, datasets, activeIndex, chartHeight }) => {
  const [animatedPosition, setAnimatedPosition] = useState(position);

  useEffect(() => {
    if (visible) {
      setAnimatedPosition(position);
    }
  }, [visible, position]);

  if (!visible || activeIndex === null) return null;

  // Use the color of the first dataset, or default to black if no datasets
  const lineColor = datasets.length > 0 ? datasets[0].borderColor : 'rgba(0,0,0,0.7)';
  return (
    <>
      <div
        style={{
          position: 'absolute',
          left: `${animatedPosition.x}px`,
          top: '0',
          width: '1px',
          height: `${chartHeight-20}px`,
          background: lineColor,
          pointerEvents: 'none',
          transition: 'left 0.2s ease-out',
          opacity: visible ? .7 : 0,
          zIndex: 1,
        }}
      />
    </>
  );
};

export const useSharedVerticalIndicator = (chartRef, activeIndicatorIndex, sharedIndicatorY, clearActiveIndicator) => {
  const [indicatorLocation, setIndicatorLocation] = useState({ visible: false, position: { x: 0, y: 0 } });
  const [chartHeight, setChartHeight] = useState(0);

  useEffect(() => {
    const chart = chartRef.current;
    if (!chart) return;

    const updateSharedVerticalIndicator = () => {
      if (!chart || !chart.canvas) return;

      if (activeIndicatorIndex !== null && activeIndicatorIndex >= 0 && activeIndicatorIndex < chart.data.labels.length) {
        const meta = chart.getDatasetMeta(0);
        if (!meta || !meta.data || activeIndicatorIndex >= meta.data.length) return;

        const activeElement = meta.data[activeIndicatorIndex];
        
        setIndicatorLocation({ visible: true, position: { x: activeElement.x, y: sharedIndicatorY } });
        setChartHeight(chart.height);
      } else {
        setIndicatorLocation(prev => ({ ...prev, visible: false }));
      }
    };

    updateSharedVerticalIndicator();

    const handleMouseLeave = () => {
      clearActiveIndicator();
    };

    chart.canvas.addEventListener('mouseleave', handleMouseLeave);

    return () => {
      if (chart.canvas) {
        chart.canvas.removeEventListener('mouseleave', handleMouseLeave);
      }
    };
  }, [activeIndicatorIndex, sharedIndicatorY, clearActiveIndicator, chartRef]);

  return { ...indicatorLocation, chartHeight };
};
