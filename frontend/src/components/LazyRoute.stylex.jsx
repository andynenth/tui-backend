// frontend/src/components/LazyRoute.stylex.jsx

import React, { Suspense } from 'react';
import LoadingOverlay from './LoadingOverlay.stylex';

/**
 * LazyRoute Component
 *
 * Wrapper for lazy-loaded route components with loading fallback
 */
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