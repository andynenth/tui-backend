import React from 'react';
import PropTypes from 'prop-types';

const TruncatedName = ({ name, maxLength = 8, className = '' }) => {
  const displayName =
    name.length > maxLength ? `${name.substring(0, maxLength - 1)}…` : name;

  return (
    <span className={`truncated-name ${className}`} title={name}>
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
