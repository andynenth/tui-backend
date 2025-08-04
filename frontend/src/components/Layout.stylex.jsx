// frontend/src/components/Layout.stylex.jsx

import React from 'react';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows } from '../design-system/tokens.stylex';
import ConnectionIndicator from './ConnectionIndicator';

// Layout styles
const styles = stylex.create({
  container: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
    backgroundColor: '#f8f9fa',
  },
  
  header: {
    backgroundColor: '#ffffff',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
    boxShadow: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
  },
  
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: '1.5rem',
  },
  
  headerInner: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  
  titleSection: {
    display: 'flex',
    alignItems: 'center',
  },
  
  title: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#343a40',
    margin: 0,
  },
  
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1.5rem',
  },
  
  main: {
    flex: 1,
    display: 'flex',
    flexDirection: 'column',
  },
});

const Layout = ({
  children,
  title = 'Liap TUI',
  showConnection = false,
  connectionProps = {},
  showHeader = true,
  headerContent = null,
  className = '',
}) => {
  // Apply container styles
  const containerProps = stylex.props(styles.container);
  
  // During migration, allow combining with existing CSS classes
  const combinedContainerProps = className 
    ? { ...containerProps, className: `${containerProps.className || ''} ${className}`.trim() }
    : containerProps;
  
  return (
    <div {...combinedContainerProps}>
      {/* Header */}
      {showHeader && (
        <header {...stylex.props(styles.header)}>
          <div {...stylex.props(styles.headerContent)}>
            <div {...stylex.props(styles.headerInner)}>
              {/* Title/Logo */}
              <div {...stylex.props(styles.titleSection)}>
                <h1 {...stylex.props(styles.title)}>{title}</h1>
              </div>

              {/* Header content */}
              <div {...stylex.props(styles.headerRight)}>
                {headerContent}

                {/* Connection indicator */}
                {showConnection && (
                  <ConnectionIndicator
                    showDetails={true}
                    {...connectionProps}
                  />
                )}
              </div>
            </div>
          </div>
        </header>
      )}

      {/* Main content */}
      <main {...stylex.props(styles.main)}>{children}</main>
    </div>
  );
};

export default Layout;