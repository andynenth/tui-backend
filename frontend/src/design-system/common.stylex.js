// Common style utilities for Liap Tui
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, shadows, layout, motion } from './tokens.stylex';

// Flexbox utilities
export const flex = stylex.create({
  row: {
    display: 'flex',
    flexDirection: 'row',
  },
  column: {
    display: 'flex',
    flexDirection: 'column',
  },
  center: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
  },
  between: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  around: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
  },
  evenly: {
    display: 'flex',
    justifyContent: 'space-evenly',
    alignItems: 'center',
  },
  start: {
    display: 'flex',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },
  end: {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },
  wrap: {
    flexWrap: 'wrap',
  },
  nowrap: {
    flexWrap: 'nowrap',
  },
  grow: {
    flexGrow: 1,
  },
  shrink: {
    flexShrink: 1,
  },
  noShrink: {
    flexShrink: 0,
  },
});

// Grid utilities
export const grid = stylex.create({
  cols1: {
    display: 'grid',
    gridTemplateColumns: '1fr',
  },
  cols2: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
  },
  cols3: {
    display: 'grid',
    gridTemplateColumns: 'repeat(3, 1fr)',
  },
  cols4: {
    display: 'grid',
    gridTemplateColumns: 'repeat(4, 1fr)',
  },
  gameLayout: {
    display: 'grid',
    gridTemplateColumns: '1fr 2fr 1fr',
  },
  slots: {
    display: 'grid',
    gridTemplateColumns: 'repeat(2, 1fr)',
  },
  pieces: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(4rem, 1fr))',
  },
});

// Typography utilities
export const text = stylex.create({
  // Sizes
  xs: {
    fontSize: typography.textXs,
    lineHeight: typography.lineHeightNormal,
  },
  sm: {
    fontSize: typography.textSm,
    lineHeight: typography.lineHeightNormal,
  },
  md: {
    fontSize: typography.textMd,
    lineHeight: typography.lineHeightNormal,
  },
  lg: {
    fontSize: typography.textLg,
    lineHeight: typography.lineHeightNormal,
  },
  xl: {
    fontSize: typography.textXl,
    lineHeight: typography.lineHeightNormal,
  },
  '2xl': {
    fontSize: typography.text2xl,
    lineHeight: typography.lineHeightTight,
  },
  '3xl': {
    fontSize: typography.text3xl,
    lineHeight: typography.lineHeightTight,
  },
  '4xl': {
    fontSize: typography.text4xl,
    lineHeight: typography.lineHeightTight,
  },
  
  // Alignment
  left: { textAlign: 'left' },
  center: { textAlign: 'center' },
  right: { textAlign: 'right' },
  justify: { textAlign: 'justify' },
  
  // Weight
  light: { fontWeight: typography.weightLight },
  normal: { fontWeight: typography.weightNormal },
  medium: { fontWeight: typography.weightMedium },
  semibold: { fontWeight: typography.weightSemibold },
  bold: { fontWeight: typography.weightBold },
  
  // Style
  italic: { fontStyle: 'italic' },
  underline: { textDecoration: 'underline' },
  lineThrough: { textDecoration: 'line-through' },
  noUnderline: { textDecoration: 'none' },
  
  // Transform
  uppercase: { textTransform: 'uppercase' },
  lowercase: { textTransform: 'lowercase' },
  capitalize: { textTransform: 'capitalize' },
  normalCase: { textTransform: 'none' },
  
  // Colors
  primary: { color: colors.primary },
  secondary: { color: colors.secondary },
  success: { color: colors.success },
  warning: { color: colors.warning },
  danger: { color: colors.danger },
  muted: { color: colors.textMuted },
  dim: { color: colors.textDim },
  white: { color: colors.textLight },
  dark: { color: colors.textDark },
  
  // Special
  truncate: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
  wrap: {
    whiteSpace: 'normal',
    wordBreak: 'break-word',
  },
  nowrap: {
    whiteSpace: 'nowrap',
  },
});

// Spacing utilities (padding and margin)
export const space = stylex.create({
  // Padding
  p0: { padding: spacing.none },
  pxs: { padding: spacing.xs },
  psm: { padding: spacing.sm },
  pmd: { padding: spacing.md },
  plg: { padding: spacing.lg },
  pxl: { padding: spacing.xl },
  pxxl: { padding: spacing.xxl },
  
  // Padding X
  px0: { paddingLeft: spacing.none, paddingRight: spacing.none },
  pxxs: { paddingLeft: spacing.xs, paddingRight: spacing.xs },
  pxsm: { paddingLeft: spacing.sm, paddingRight: spacing.sm },
  pxmd: { paddingLeft: spacing.md, paddingRight: spacing.md },
  pxlg: { paddingLeft: spacing.lg, paddingRight: spacing.lg },
  pxxl: { paddingLeft: spacing.xl, paddingRight: spacing.xl },
  
  // Padding Y
  py0: { paddingTop: spacing.none, paddingBottom: spacing.none },
  pyxs: { paddingTop: spacing.xs, paddingBottom: spacing.xs },
  pysm: { paddingTop: spacing.sm, paddingBottom: spacing.sm },
  pymd: { paddingTop: spacing.md, paddingBottom: spacing.md },
  pylg: { paddingTop: spacing.lg, paddingBottom: spacing.lg },
  pyxl: { paddingTop: spacing.xl, paddingBottom: spacing.xl },
  
  // Margin
  m0: { margin: spacing.none },
  mxs: { margin: spacing.xs },
  msm: { margin: spacing.sm },
  mmd: { margin: spacing.md },
  mlg: { margin: spacing.lg },
  mxl: { margin: spacing.xl },
  mxxl: { margin: spacing.xxl },
  mAuto: { margin: 'auto' },
  
  // Margin X
  mx0: { marginLeft: spacing.none, marginRight: spacing.none },
  mxxs: { marginLeft: spacing.xs, marginRight: spacing.xs },
  mxsm: { marginLeft: spacing.sm, marginRight: spacing.sm },
  mxmd: { marginLeft: spacing.md, marginRight: spacing.md },
  mxlg: { marginLeft: spacing.lg, marginRight: spacing.lg },
  mxxl: { marginLeft: spacing.xl, marginRight: spacing.xl },
  mxAuto: { marginLeft: 'auto', marginRight: 'auto' },
  
  // Margin Y
  my0: { marginTop: spacing.none, marginBottom: spacing.none },
  myxs: { marginTop: spacing.xs, marginBottom: spacing.xs },
  mysm: { marginTop: spacing.sm, marginBottom: spacing.sm },
  mymd: { marginTop: spacing.md, marginBottom: spacing.md },
  mylg: { marginTop: spacing.lg, marginBottom: spacing.lg },
  myxl: { marginTop: spacing.xl, marginBottom: spacing.xl },
  
  // Gap for flexbox/grid
  gap0: { gap: spacing.none },
  gapxs: { gap: spacing.xs },
  gapsm: { gap: spacing.sm },
  gapmd: { gap: spacing.md },
  gaplg: { gap: spacing.lg },
  gapxl: { gap: spacing.xl },
  gapxxl: { gap: spacing.xxl },
});

// Border utilities
export const border = stylex.create({
  none: {
    border: 'none',
  },
  base: {
    border: `1px solid ${colors.border}`,
  },
  primary: {
    border: `1px solid ${colors.primary}`,
  },
  secondary: {
    border: `1px solid ${colors.secondary}`,
  },
  success: {
    border: `1px solid ${colors.success}`,
  },
  warning: {
    border: `1px solid ${colors.warning}`,
  },
  danger: {
    border: `1px solid ${colors.danger}`,
  },
  thick: {
    borderWidth: '2px',
  },
  dashed: {
    borderStyle: 'dashed',
  },
  dotted: {
    borderStyle: 'dotted',
  },
  rounded: {
    borderRadius: layout.radiusMd,
  },
  roundedSm: {
    borderRadius: layout.radiusSm,
  },
  roundedLg: {
    borderRadius: layout.radiusLg,
  },
  roundedFull: {
    borderRadius: layout.radiusFull,
  },
});

// Shadow utilities
export const shadow = stylex.create({
  none: {
    boxShadow: shadows.none,
  },
  sm: {
    boxShadow: shadows.sm,
  },
  md: {
    boxShadow: shadows.md,
  },
  lg: {
    boxShadow: shadows.lg,
  },
  xl: {
    boxShadow: shadows.xl,
  },
  inner: {
    boxShadow: shadows.inner,
  },
  game: {
    boxShadow: shadows.game,
  },
  piece: {
    boxShadow: shadows.piece,
  },
  glow: {
    boxShadow: shadows.glow,
  },
});

// Position utilities
export const position = stylex.create({
  relative: {
    position: 'relative',
  },
  absolute: {
    position: 'absolute',
  },
  fixed: {
    position: 'fixed',
  },
  sticky: {
    position: 'sticky',
  },
  static: {
    position: 'static',
  },
  inset0: {
    top: 0,
    right: 0,
    bottom: 0,
    left: 0,
  },
  top0: { top: 0 },
  right0: { right: 0 },
  bottom0: { bottom: 0 },
  left0: { left: 0 },
});

// Size utilities
export const size = stylex.create({
  full: {
    width: '100%',
    height: '100%',
  },
  wFull: {
    width: '100%',
  },
  hFull: {
    height: '100%',
  },
  wAuto: {
    width: 'auto',
  },
  hAuto: {
    height: 'auto',
  },
  minWFull: {
    minWidth: '100%',
  },
  minHFull: {
    minHeight: '100%',
  },
  maxWFull: {
    maxWidth: '100%',
  },
  maxHFull: {
    maxHeight: '100%',
  },
  screenW: {
    width: '100vw',
  },
  screenH: {
    height: '100vh',
  },
});

// Visibility utilities
export const visibility = stylex.create({
  visible: {
    visibility: 'visible',
  },
  invisible: {
    visibility: 'hidden',
  },
  hidden: {
    display: 'none',
  },
  block: {
    display: 'block',
  },
  inline: {
    display: 'inline',
  },
  inlineBlock: {
    display: 'inline-block',
  },
  opacity0: {
    opacity: 0,
  },
  opacity50: {
    opacity: 0.5,
  },
  opacity100: {
    opacity: 1,
  },
});

// Cursor utilities
export const cursor = stylex.create({
  pointer: {
    cursor: 'pointer',
  },
  notAllowed: {
    cursor: 'not-allowed',
  },
  wait: {
    cursor: 'wait',
  },
  grab: {
    cursor: 'grab',
  },
  grabbing: {
    cursor: 'grabbing',
  },
  move: {
    cursor: 'move',
  },
  default: {
    cursor: 'default',
  },
});

// Transition utilities
export const transition = stylex.create({
  none: {
    transition: 'none',
  },
  all: {
    transition: motion.transitionBase,
  },
  fast: {
    transition: motion.transitionFast,
  },
  colors: {
    transition: `colors ${motion.durationNormal} ${motion.easeInOut}`,
  },
  transform: {
    transition: `transform ${motion.durationNormal} ${motion.easeInOut}`,
  },
  opacity: {
    transition: `opacity ${motion.durationNormal} ${motion.easeInOut}`,
  },
});

// Overflow utilities
export const overflow = stylex.create({
  visible: {
    overflow: 'visible',
  },
  hidden: {
    overflow: 'hidden',
  },
  scroll: {
    overflow: 'scroll',
  },
  auto: {
    overflow: 'auto',
  },
  xHidden: {
    overflowX: 'hidden',
  },
  yHidden: {
    overflowY: 'hidden',
  },
  xAuto: {
    overflowX: 'auto',
  },
  yAuto: {
    overflowY: 'auto',
  },
});

// Z-index utilities
export const zIndex = stylex.create({
  base: {
    zIndex: layout.zBase,
  },
  dropdown: {
    zIndex: layout.zDropdown,
  },
  sticky: {
    zIndex: layout.zSticky,
  },
  fixed: {
    zIndex: layout.zFixed,
  },
  modalBackdrop: {
    zIndex: layout.zModalBackdrop,
  },
  modal: {
    zIndex: layout.zModal,
  },
  popover: {
    zIndex: layout.zPopover,
  },
  tooltip: {
    zIndex: layout.zTooltip,
  },
  notification: {
    zIndex: layout.zNotification,
  },
  max: {
    zIndex: layout.zMax,
  },
});