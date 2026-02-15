import React from 'react';
import { RouterProvider } from 'react-router-dom';

import { ErrorBoundary } from './ErrorBoundary';
import { router } from './routes';

export function App() {
  return (
    <ErrorBoundary>
      <RouterProvider router={router} />
    </ErrorBoundary>
  );
}
