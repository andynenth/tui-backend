// frontend/src/components/shared/TruncatedName.stylex.jsx

import React from 'react';
import PropTypes from 'prop-types';
import * as stylex from '@stylexjs/stylex';

// TruncatedName styles
const styles = stylex.create({
  name: {
    display: 'inline-block',
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
});

const TruncatedName = ({ name, maxLength = 8, className = ' }) => {
  const displayName =
    name.length > maxLength ? `${name.substring(0, maxLength - 1)}…` : name;

  // Apply name styles
  const nameProps = stylex.props(styles.name);
  
  // During migration, allow combining with existing CSS classes
  const combinedNameProps = className 
    ? { ...nameProps, className: `${nameProps.className || ''} ${className}`.trim() }
    : nameProps;

  return (
    <span {...combinedNameProps} title={name}>
      {displayName}
    </span>
  );
};

TruncatedName.propTypes = {
  name: PropTypes.string.isRequired,
  maxLength: PropTypes.number,
  className: PropTypes.string,
};

export default TruncatedName;