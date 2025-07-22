import React from 'react';
import settingIcon from '../assets/setting.svg';

const SettingsButton = ({ onClick }) => {
  return (
    <button className="settings-button" onClick={onClick} aria-label="Settings">
      <img src={settingIcon} alt="Settings" className="settings-icon" />
    </button>
  );
};

export default SettingsButton;
