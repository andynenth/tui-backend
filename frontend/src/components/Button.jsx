import React, { memo } from 'react';

const Button = memo(({ 
  children, 
  variant = 'primary', 
  size = 'md',
  disabled = false, 
  loading = false,
  onClick,
  className = '',
  type = 'button',
  loadingText = 'Loading...',
  icon = null,
  fullWidth = false,
  ...props 
}) => {
  const baseClasses = `
    inline-flex items-center justify-center font-medium rounded-md transform-gpu
    transition-all duration-300 ease-out focus:outline-none focus:ring-2 focus:ring-offset-2
    hover:scale-105 active:scale-95 hover:shadow-lg
    disabled:opacity-50 disabled:cursor-not-allowed disabled:pointer-events-none
    disabled:hover:scale-100 disabled:hover:shadow-none
  `;
  
  const variantClasses = {
    primary: 'bg-gradient-to-r from-blue-600 to-blue-700 text-white hover:from-blue-700 hover:to-blue-800 focus:ring-blue-500 shadow-blue-500/25',
    secondary: 'bg-gradient-to-r from-gray-200 to-gray-300 text-gray-900 hover:from-gray-300 hover:to-gray-400 focus:ring-gray-500 shadow-gray-400/25', 
    success: 'bg-gradient-to-r from-green-600 to-green-700 text-white hover:from-green-700 hover:to-green-800 focus:ring-green-500 shadow-green-500/25',
    danger: 'bg-gradient-to-r from-red-600 to-red-700 text-white hover:from-red-700 hover:to-red-800 focus:ring-red-500 shadow-red-500/25',
    ghost: 'bg-transparent text-gray-700 hover:bg-gray-100 hover:shadow-gray-300/50 focus:ring-gray-500 border border-gray-300',
    outline: 'bg-transparent border-2 border-blue-600 text-blue-600 hover:bg-blue-50 hover:border-blue-700 focus:ring-blue-500'
  };

  const sizeClasses = {
    sm: 'px-3 py-1.5 text-sm',
    md: 'px-4 py-2 text-base',
    lg: 'px-6 py-3 text-lg'
  };

  const classes = [
    baseClasses,
    variantClasses[variant],
    sizeClasses[size],
    fullWidth && 'w-full',
    className
  ].filter(Boolean).join(' ');

  const handleClick = (e) => {
    if (disabled || loading) return;
    onClick?.(e);
  };

  return (
    <button
      type={type}
      className={classes}
      disabled={disabled || loading}
      onClick={handleClick}
      {...props}
    >
      {loading ? (
        <div className="flex items-center space-x-2">
          <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
          <span>{loadingText}</span>
        </div>
      ) : (
        <div className="flex items-center space-x-2">
          {icon && <span className="w-4 h-4">{icon}</span>}
          <span>{children}</span>
        </div>
      )}
    </button>
  );
});

Button.displayName = 'Button';

export default Button;