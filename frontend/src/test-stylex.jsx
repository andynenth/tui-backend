import React from 'react';
import ButtonStyleX from './components/Button.stylex';

// Test component to verify StyleX integration
export function TestStyleX() {
  return (
    <div style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
      <h2>StyleX Button Test</h2>
      
      <div style={{ display: 'flex', gap: '12px', flexWrap: 'wrap' }}>
        <ButtonStyleX variant="primary">Primary</ButtonStyleX>
        <ButtonStyleX variant="secondary">Secondary</ButtonStyleX>
        <ButtonStyleX variant="success">Success</ButtonStyleX>
        <ButtonStyleX variant="danger">Danger</ButtonStyleX>
        <ButtonStyleX variant="ghost">Ghost</ButtonStyleX>
        <ButtonStyleX variant="outline">Outline</ButtonStyleX>
      </div>
      
      <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
        <ButtonStyleX size="sm">Small</ButtonStyleX>
        <ButtonStyleX size="md">Medium</ButtonStyleX>
        <ButtonStyleX size="lg">Large</ButtonStyleX>
      </div>
      
      <div style={{ display: 'flex', gap: '12px' }}>
        <ButtonStyleX loading loadingText="Processing...">Loading</ButtonStyleX>
        <ButtonStyleX disabled>Disabled</ButtonStyleX>
      </div>
      
      <ButtonStyleX fullWidth>Full Width Button</ButtonStyleX>
    </div>
  );
}