import { Chart as ChartJS } from 'chart.js';

// Add this new function to fade the color
const fadeColor = (color, opacity) => {
  if (color.startsWith('#')) {
    // Convert hex to RGB
    const r = parseInt(color.slice(1, 3), 16);
    const g = parseInt(color.slice(3, 5), 16);
    const b = parseInt(color.slice(5, 7), 16);
    return `rgba(${r}, ${g}, ${b}, ${opacity})`;
  } else if (color.startsWith('rgb')) {
    // If it's already RGB or RGBA, just change the opacity
    const rgb = color.match(/\d+/g);
    return `rgba(${rgb[0]}, ${rgb[1]}, ${rgb[2]}, ${opacity})`;
  }
  // If color format is not recognized, return the original color
  return color;
};

const drawErrorBar = (ctx, x, y, errorLow, errorHigh, color, width) => {
  ctx.save();
  ctx.strokeStyle = fadeColor(color, 0.3);
  ctx.lineWidth = width;

  // Draw vertical line
  ctx.beginPath();
  ctx.moveTo(x, y - errorHigh);
  ctx.lineTo(x, y + errorLow);
  ctx.stroke();

  // Draw horizontal caps
  const capLength = 5;
  ctx.beginPath();
  ctx.moveTo(x - capLength, y - errorHigh);
  ctx.lineTo(x + capLength, y - errorHigh);
  ctx.moveTo(x - capLength, y + errorLow);
  ctx.lineTo(x + capLength, y + errorLow);
  ctx.stroke();

  ctx.restore();
};

const ErrorBarPlugin = {
  id: 'errorBar',
  beforeInit(chart) {
    chart.errorBarData = {};
  },
  afterDatasetsDraw(chart, args, options) {
    const { ctx } = chart;
    
    if (!options.draw) {
      return;
    }

    chart.data.datasets.forEach((dataset, datasetIndex) => {
      if (dataset.errorBars) {
        const meta = chart.getDatasetMeta(datasetIndex);

        dataset.data.forEach((datapoint, index) => {
          if (dataset.errorBars[index] !== undefined) {
            const { x, y } = meta.data[index].getCenterPoint();
            
            let errorLow, errorHigh;
            if (typeof dataset.errorBars[index] === 'object') {
              errorLow = dataset.errorBars[index].low;
              errorHigh = dataset.errorBars[index].high;
            } else {
              errorLow = datapoint - dataset.errorBars[index];
              errorHigh = datapoint + dataset.errorBars[index];
            }
            
            // Store error bar data for tooltip access
            if (!chart.errorBarData[datasetIndex]) {
              chart.errorBarData[datasetIndex] = [];
            }
            chart.errorBarData[datasetIndex][index] = { low: errorLow, high: errorHigh };

            // Convert to pixel values for drawing
            const errorLowPx = Math.abs(chart.scales.y.getPixelForValue(datapoint) - 
                                        chart.scales.y.getPixelForValue(errorLow));
            const errorHighPx = Math.abs(chart.scales.y.getPixelForValue(datapoint) - 
                                         chart.scales.y.getPixelForValue(errorHigh));
            
            drawErrorBar(ctx, x, y, errorLowPx, errorHighPx, dataset.borderColor, dataset.borderWidth || 1);
          }
        });
      }
    });
  }
};

export default ErrorBarPlugin;

// Register the plugin
ChartJS.register(ErrorBarPlugin);
