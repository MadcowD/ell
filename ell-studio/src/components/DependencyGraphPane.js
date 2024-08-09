import React from 'react';
import { FiChevronRight } from 'react-icons/fi';
import { Link } from 'react-router-dom';
import {DependencyGraph} from './depgraph/DependencyGraph';

// When changing pages we need to rerender this component (or create a new graph)
const DependencyGraphPane = ({ lmp, uses }) => {
  const lmps = [lmp, ...uses];
console.log(uses)
  return (
   <DependencyGraph lmps={lmps} />
  );
};

export default DependencyGraphPane;