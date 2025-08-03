# Xiangqi Piece SVG Assets

This directory contains SVG representations of all xiangqi (Chinese chess) pieces, designed to replace Chinese character text rendering.

## File Organization

### Naming Convention

All files follow the exact naming convention from `backend/engine/constants.py`:

- `PIECE_TYPE_COLOR.svg`
- Examples: `GENERAL_RED.svg`, `CHARIOT_BLACK.svg`

### Complete Piece Set

- ✅ **GENERAL_RED.svg** - 帥 (Red General)
- ✅ **GENERAL_BLACK.svg** - 將 (Black General)
- ✅ **ADVISOR_RED.svg** - 仕 (Red Advisor)
- ✅ **ADVISOR_BLACK.svg** - 士 (Black Advisor)
- ✅ **ELEPHANT_RED.svg** - 相 (Red Elephant)
- ✅ **ELEPHANT_BLACK.svg** - 象 (Black Elephant)
- ✅ **CHARIOT_RED.svg** - 俥 (Red Chariot)
- ✅ **CHARIOT_BLACK.svg** - 車 (Black Chariot)
- ✅ **HORSE_RED.svg** - 傌 (Red Horse)
- ✅ **HORSE_BLACK.svg** - 馬 (Black Horse)
- ✅ **CANNON_RED.svg** - 炮 (Red Cannon)
- ✅ **CANNON_BLACK.svg** - 砲 (Black Cannon)
- ✅ **SOLDIER_RED.svg** - 兵 (Red Soldier)
- ✅ **SOLDIER_BLACK.svg** - 卒 (Black Soldier)

## Technical Specifications

### SVG Properties

- **Format**: Scalable Vector Graphics (SVG)
- **Colors**:
  - Red pieces: `#dc3545` (exact match to project CSS)
  - Black pieces: `#495057` (exact match to project CSS)
- **Font**: SimSun/宋体 serif (matches current character rendering)
- **Background**: Transparent
- **Size**: Vector (scalable to any resolution)

### File Structure

```
frontend/src/assets/pieces/
├── index.js              # Import/export utilities
├── README.md             # This documentation
├── GENERAL_RED.svg       # Individual SVG files...
├── GENERAL_BLACK.svg
├── ...
└── SOLDIER_BLACK.svg
```

## Usage

### Import Individual Pieces

```javascript
import { GENERAL_RED, CHARIOT_BLACK } from './assets/pieces';
```

### Import All Pieces

```javascript
import * as PieceAssets from './assets/pieces';
```

### Dynamic Access

```javascript
import { getPieceAsset } from './assets/pieces';

const pieceType = 'GENERAL_RED';
const svgAsset = getPieceAsset(pieceType);
```

### React Component Usage

```jsx
import { GENERAL_RED } from './assets/pieces';

function GamePiece({ pieceType }) {
  return <img src={GENERAL_RED} alt="Red General" className="game-piece" />;
}
```

## Migration from Chinese Characters

These SVG assets can replace the current Chinese character rendering in:

- `frontend/src/components/game/shared/GamePiece.jsx`
- `frontend/src/utils/pieceMapping.js`

### Benefits of SVG Migration

1. **No font dependencies** - eliminates SimSun/宋体 requirements
2. **Perfect scaling** - crisp at all sizes from 34px to 68px+
3. **Consistent rendering** - identical appearance across platforms
4. **Better performance** - no font loading delays
5. **Easier styling** - CSS can be applied directly to SVG

### Migration Steps

1. Update `GamePiece.jsx` to use SVG imports instead of text
2. Modify `pieceMapping.js` to map piece types to SVG assets
3. Remove Chinese font loading from CSS
4. Test all piece sizes and interactive states

## File Origins

Generated from Chinese characters using exact project styling:

- Source: `/pieces-svg/xiangqi-[character]-[color].svg`
- Converted to constants naming convention
- Organized in frontend assets structure

## Maintenance

When adding new pieces or modifying existing ones:

1. Follow the `PIECE_TYPE_COLOR.svg` naming convention
2. Update `index.js` with new imports/exports
3. Update this README.md with new pieces
4. Ensure colors match project constants (#dc3545 for red, #495057 for black)
