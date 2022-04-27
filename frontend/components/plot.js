import React from 'react';
import plotly from 'plotly.js/dist/plotly';
import createPlotComponent from 'react-plotly.js/factory';

const Plot = createPlotComponent(plotly);

export default function DynamicPlot(props) {
  return (
    <Plot {...props} />
  )
}
