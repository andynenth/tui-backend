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
    backgroundColor: colors.gray50,
  },
  
  header: {
    backgroundColor: colors.white,
    borderBottom: `1px solid ${colors.gray200}`,
    boxShadow: shadows.sm,
  },
  
  headerContent: {
    maxWidth: '1200px',
    margin: '0 auto',
    padding: spacing.lg,
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
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray800,
    margin: 0,
  },
  
  headerRight: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.lg,
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