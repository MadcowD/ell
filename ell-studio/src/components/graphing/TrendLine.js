import React from 'react';
import { Line } from 'react-chartjs-2';
import { Chart as ChartJS, CategoryScale, LinearScale, LineElement, PointElement, Tooltip as ChartTooltip, Filler } from 'chart.js';

ChartJS.register(CategoryScale, LinearScale, LineElement, PointElement, ChartTooltip, Filler);

const TrendLine = ({ data, hoverIndex, onHover }) => {
  const trend = data[data.length - 1] - data[0];
  const trendColor = trend > 0 ? 'rgba(52, 211, 153, 0.8)' : 'rgba(239, 68, 68, 0.8)';
  const fillColor = trend > 0 ? 'rgba(52, 211, 153, 0.2)' : 'rgba(239, 68, 68, 0.2)';

  const chartData = {
    labels: data.map((_, index) => index + 1),
    datasets: [{
      data,
      borderColor: trendColor,
      backgroundColor: fillColor,
      pointRadius: 0,
      borderWidth: 1,
      tension: 0.4,
      fill: true,
    }],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: { 
      legend: { display: false },
      tooltip: { enabled: false }
    },
    scales: { 
      x: { display: false }, 
      y: { 
        display: false,
        min: Math.min(...data) * 0.95,
        max: Math.max(...data) * 1.05,
      } 
    },
  };

  return (
    <div 
      className="w-full h-5"
      onMouseMove={(e) => {
        const rect = e.currentTarget.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const index = Math.round((x / rect.width) * (data.length - 1));
        onHover(index);
      }}
      onMouseLeave={() => onHover(null)}
    >
      <Line data={chartData} options={options} />
    </div>
  );
};

export default TrendLine;
