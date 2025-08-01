import React from 'react';
import { useTheme } from '../../contexts/ThemeContext';
import GamePiece from '../game/shared/GamePiece';
import { getThemePieceSVG } from '../../utils/pieceMapping';

/**
 * Debug component to test piece rendering with different data formats
 * This helps isolate the "NO SRC" issue in GamePiece component
 */
const PieceRenderTest = () => {
  const { currentTheme } = useTheme();

  // Test data - various formats that might be received
  const testPieces = [
    // Format 1: Correct object format (what should work)
    { id: 'test1', kind: 'GENERAL', color: 'red', value: 14 },
    { id: 'test2', kind: 'ELEPHANT', color: 'black', value: 9 },
    
    // Format 2: Uppercase color (if parser bug)
    { id: 'test3', kind: 'HORSE', color: 'RED', value: 8 },
    
    // Format 3: Missing properties (potential data corruption)
    { id: 'test4', kind: 'SOLDIER', value: 2 },
    { id: 'test5', color: 'black', value: 5 },
    { id: 'test6' },
    
    // Format 4: Null/undefined (edge cases)
    null,
    undefined,
  ];

  const testThemeAsset = (piece, label) => {
    console.log(`[PieceRenderTest] Testing ${label}:`, {
      piece,
      theme: currentTheme ? { id: currentTheme.id, hasPieceAssets: !!currentTheme.pieceAssets } : null,
      result: getThemePieceSVG(piece, currentTheme)
    });
    
    return getThemePieceSVG(piece, currentTheme);
  };

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f5f5' }}>
      <h2>Piece Render Debug Test</h2>
      
      <div style={{ marginBottom: '20px' }}>
        <h3>Theme Info:</h3>
        <pre>{JSON.stringify({
          themeId: currentTheme?.id,
          themeName: currentTheme?.name,
          hasPieceAssets: !!currentTheme?.pieceAssets,
          pieceAssetsCount: currentTheme?.pieceAssets ? Object.keys(currentTheme.pieceAssets).length : 0,
          firstFewAssets: currentTheme?.pieceAssets ? Object.keys(currentTheme.pieceAssets).slice(0, 5) : []
        }, null, 2)}</pre>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '15px' }}>
        {testPieces.map((piece, index) => {
          const label = `Test ${index + 1}`;
          const asset = testThemeAsset(piece, label);
          
          return (
            <div key={index} style={{ border: '1px solid #ccc', padding: '10px', textAlign: 'center' }}>
              <h4>{label}</h4>
              <div style={{ fontSize: '12px', marginBottom: '10px' }}>
                <pre>{JSON.stringify(piece, null, 1)}</pre>
              </div>
              
              <div style={{ marginBottom: '10px' }}>
                <strong>Asset Result:</strong><br/>
                <code style={{ fontSize: '10px' }}>
                  {asset ? 'Valid SVG URL' : 'NULL/UNDEFINED'}
                </code>
              </div>
              
              {piece && (
                <div style={{ border: '2px solid red' }}>
                  <GamePiece
                    piece={piece}
                    size="medium"
                    showValue={true}
                  />
                </div>
              )}
              
              {!piece && (
                <div style={{ color: 'gray', fontStyle: 'italic' }}>
                  Null/undefined piece
                </div>
              )}
            </div>
          );
        })}
      </div>
      
      <div style={{ marginTop: '30px' }}>
        <h3>Direct Theme Asset Test (Home Page Method):</h3>
        <div style={{ display: 'flex', gap: '20px' }}>
          <div style={{ textAlign: 'center' }}>
            <h4>Direct Asset (Works on Home Page)</h4>
            <img 
              src={currentTheme?.uiElements?.startIcon?.main} 
              alt="Direct theme asset"
              style={{ width: '64px', height: '64px', border: '2px solid green' }}
            />
            <div style={{ fontSize: '12px', marginTop: '5px' }}>
              Asset URL: {currentTheme?.uiElements?.startIcon?.main ? 'Valid' : 'Invalid'}
            </div>
          </div>
          
          <div style={{ textAlign: 'center' }}>
            <h4>Function Call (Fails in Game)</h4>
            <img 
              src={getThemePieceSVG({ kind: 'GENERAL', color: 'red', value: 14 }, currentTheme)} 
              alt="Function result asset"
              style={{ width: '64px', height: '64px', border: '2px solid red' }}
            />
            <div style={{ fontSize: '12px', marginTop: '5px' }}>
              Function Result: {getThemePieceSVG({ kind: 'GENERAL', color: 'red', value: 14 }, currentTheme) ? 'Valid' : 'Invalid'}
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PieceRenderTest;