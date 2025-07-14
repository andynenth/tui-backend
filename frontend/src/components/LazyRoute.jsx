import React, { Suspense } from 'react';
import { LoadingOverlay } from './index';

const LazyRoute = ({
  Component,
  fallback = <LoadingOverlay message="Loading page..." />,
  ...props
}) => {
  return (
    <Suspense fallback={fallback}>
      <Component {...props} />
    </Suspense>
  );
};

export default LazyRoute;
