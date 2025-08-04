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

// Text utilities
export const text = stylex.create({
  // Font sizes
  xs: {
    fontSize: typography.textXs,
    lineHeight: typography.lineHeightTight,
  },
  sm: {
    fontSize: typography.textSm,
    lineHeight: typography.lineHeightTight,
  },
  md: {
    fontSize: typography.textMd,
    lineHeight: typography.lineHeightNormal,
  },
  base: {
    fontSize: typography.textBase,
    lineHeight: typography.lineHeightNormal,
  },
  lg: {
    fontSize: typography.textLg,
    lineHeight: typography.lineHeightNormal,
  },
  xl: {
    fontSize: typography.textXl,
    lineHeight: typography.lineHeightRelaxed,
  },
  xxl: {
    fontSize: typography.text2xl,
    lineHeight: typography.lineHeightRelaxed,
  },
  
  // Text alignment
  left: { textAlign: 'left' },
  center: { textAlign: 'center' },
  right: { textAlign: 'right' },
  justify: { textAlign: 'justify' },
  
  // Font weight
  thin: { fontWeight: typography.weightThin },
  normal: { fontWeight: typography.weightNormal },
  medium: { fontWeight: typography.weightMedium },
  semibold: { fontWeight: typography.weightSemibold },
  bold: { fontWeight: typography.weightBold },
  
  // Text transform
  uppercase: { textTransform: 'uppercase' },
  lowercase: { textTransform: 'lowercase' },
  capitalize: { textTransform: 'capitalize' },
  
  // Letter spacing
  tight: { letterSpacing: typography.trackingTight },
  wide: { letterSpacing: typography.trackingWide },
  wider: { letterSpacing: typography.trackingWider },
  
  // Text colors
  primary: { color: colors.textPrimary },
  secondary: { color: colors.textSecondary },
  muted: { color: colors.textMuted },
  light: { color: colors.textLight },
  white: { color: colors.textWhite },
  success: { color: colors.success },
  warning: { color: colors.warning },
  danger: { color: colors.danger },
  
  // Special text styles
  truncate: {
    overflow: 'hidden',
    textOverflow: 'ellipsis',
    whiteSpace: 'nowrap',
  },
});

// Spacing utilities
export const space = stylex.create({
  // Padding all sides
  p0: { padding: spacing.none },
  p1: { padding: spacing.xs },
  p2: { padding: spacing.sm },
  p3: { padding: spacing.md },
  p4: { padding: spacing.lg },
  p5: { padding: spacing.xl },
  p6: { padding: spacing.xxl },
  
  // Padding horizontal
  px0: { paddingLeft: spacing.none, paddingRight: spacing.none },
  px1: { paddingLeft: spacing.xs, paddingRight: spacing.xs },
  px2: { paddingLeft: spacing.sm, paddingRight: spacing.sm },
  px3: { paddingLeft: spacing.md, paddingRight: spacing.md },
  px4: { paddingLeft: spacing.lg, paddingRight: spacing.lg },
  px5: { paddingLeft: spacing.xl, paddingRight: spacing.xl },
  px6: { paddingLeft: spacing.xxl, paddingRight: spacing.xxl },
  
  // Padding vertical
  py0: { paddingTop: spacing.none, paddingBottom: spacing.none },
  py1: { paddingTop: spacing.xs, paddingBottom: spacing.xs },
  py2: { paddingTop: spacing.sm, paddingBottom: spacing.sm },
  py3: { paddingTop: spacing.md, paddingBottom: spacing.md },
  py4: { paddingTop: spacing.lg, paddingBottom: spacing.lg },
  py5: { paddingTop: spacing.xl, paddingBottom: spacing.xl },
  py6: { paddingTop: spacing.xxl, paddingBottom: spacing.xxl },
  
  // Margin all sides
  m0: { margin: spacing.none },
  m1: { margin: spacing.xs },
  m2: { margin: spacing.sm },
  m3: { margin: spacing.md },
  m4: { margin: spacing.lg },
  m5: { margin: spacing.xl },
  m6: { margin: spacing.xxl },
  mAuto: { margin: 'auto' },
  
  // Margin horizontal
  mx0: { marginLeft: spacing.none, marginRight: spacing.none },
  mx1: { marginLeft: spacing.xs, marginRight: spacing.xs },
  mx2: { marginLeft: spacing.sm, marginRight: spacing.sm },
  mx3: { marginLeft: spacing.md, marginRight: spacing.md },
  mx4: { marginLeft: spacing.lg, marginRight: spacing.lg },
  mx5: { marginLeft: spacing.xl, marginRight: spacing.xl },
  mx6: { marginLeft: spacing.xxl, marginRight: spacing.xxl },
  mxAuto: { marginLeft: 'auto', marginRight: 'auto' },
  
  // Margin vertical
  my0: { marginTop: spacing.none, marginBottom: spacing.none },
  my1: { marginTop: spacing.xs, marginBottom: spacing.xs },
  my2: { marginTop: spacing.sm, marginBottom: spacing.sm },
  my3: { marginTop: spacing.md, marginBottom: spacing.md },
  my4: { marginTop: spacing.lg, marginBottom: spacing.lg },
  my5: { marginTop: spacing.xl, marginBottom: spacing.xl },
  my6: { marginTop: spacing.xxl, marginBottom: spacing.xxl },
  
  // Gap for flexbox/grid
  gap0: { gap: spacing.none },
  gap1: { gap: spacing.xs },
  gap2: { gap: spacing.sm },
  gap3: { gap: spacing.md },
  gap4: { gap: spacing.lg },
  gap5: { gap: spacing.xl },
  gap6: { gap: spacing.xxl },
});

// Border utilities
export const border = stylex.create({
  none: { border: 'none' },
  
  // Border all sides
  all: { border: `1px solid ${colors.gray300}` },
  allSm: { border: `1px solid ${colors.gray200}` },
  allMd: { border: `2px solid ${colors.gray300}` },
  
  // Border radius
  rounded: { borderRadius: layout.radiusMd },
  roundedSm: { borderRadius: layout.radiusSm },
  roundedLg: { borderRadius: layout.radiusLg },
  roundedXl: { borderRadius: layout.radiusXl },
  roundedFull: { borderRadius: layout.radiusFull },
  roundedNone: { borderRadius: layout.radiusNone },
  
  // Border colors
  gray: { borderColor: colors.gray300 },
  primary: { borderColor: colors.primary },
  success: { borderColor: colors.success },
  warning: { borderColor: colors.warning },
  danger: { borderColor: colors.danger },
});

// Shadow utilities
export const shadow = stylex.create({
  none: { boxShadow: shadows.none },
  sm: { boxShadow: shadows.sm },
  md: { boxShadow: shadows.md },
  lg: { boxShadow: shadows.lg },
  xl: { boxShadow: shadows.xl },
  
  // Colored shadows
  primary: { boxShadow: shadows.primaryGlow },
  success: { boxShadow: shadows.successGlow },
  warning: { boxShadow: shadows.warningGlow },
  danger: { boxShadow: shadows.dangerGlow },
  
  // Special shadows
  inset: { boxShadow: shadows.insetWhite },
  border: { boxShadow: shadows.border },
});

// Background utilities
export const bg = stylex.create({
  // Solid colors
  white: { backgroundColor: colors.white },
  gray50: { backgroundColor: colors.gray50 },
  gray100: { backgroundColor: colors.gray100 },
  gray200: { backgroundColor: colors.gray200 },
  gray300: { backgroundColor: colors.gray300 },
  gray400: { backgroundColor: colors.gray400 },
  gray500: { backgroundColor: colors.gray500 },
  gray600: { backgroundColor: colors.gray600 },
  gray700: { backgroundColor: colors.gray700 },
  gray800: { backgroundColor: colors.gray800 },
  primary: { backgroundColor: colors.primary },
  success: { backgroundColor: colors.success },
  warning: { backgroundColor: colors.warning },
  danger: { backgroundColor: colors.danger },
  
  // Transparent
  transparent: { backgroundColor: 'transparent' },
});

// Transition utilities
export const transition = stylex.create({
  none: { transition: 'none' },
  all: { transition: `all ${motion.durationBase} ${motion.easeInOut}` },
  fast: { transition: `all ${motion.durationFast} ${motion.easeInOut}` },
  slow: { transition: `all ${motion.durationSlow} ${motion.easeInOut}` },
  
  // Specific transitions
  colors: { transition: `colors ${motion.durationBase} ${motion.easeInOut}` },
  opacity: { transition: `opacity ${motion.durationBase} ${motion.easeInOut}` },
  transform: { transition: `transform ${motion.durationBase} ${motion.easeInOut}` },
});

// Position utilities
export const position = stylex.create({
  relative: { position: 'relative' },
  absolute: { position: 'absolute' },
  fixed: { position: 'fixed' },
  sticky: { position: 'sticky' },
  static: { position: 'static' },
  
  // Position values
  inset0: { top: 0, right: 0, bottom: 0, left: 0 },
  insetX0: { left: 0, right: 0 },
  insetY0: { top: 0, bottom: 0 },
  top0: { top: 0 },
  right0: { right: 0 },
  bottom0: { bottom: 0 },
  left0: { left: 0 },
});

// Size utilities
export const size = stylex.create({
  // Width
  wFull: { width: '100%' },
  wAuto: { width: 'auto' },
  wScreen: { width: '100vw' },
  wMin: { width: 'min-content' },
  wMax: { width: 'max-content' },
  wFit: { width: 'fit-content' },
  
  // Height
  hFull: { height: '100%' },
  hAuto: { height: 'auto' },
  hScreen: { height: '100vh' },
  hMin: { height: 'min-content' },
  hMax: { height: 'max-content' },
  hFit: { height: 'fit-content' },
  
  // Min/Max dimensions
  maxWFull: { maxWidth: '100%' },
  maxHFull: { maxHeight: '100%' },
  minW0: { minWidth: 0 },
  minH0: { minHeight: 0 },
});

// Display utilities
export const display = stylex.create({
  block: { display: 'block' },
  inline: { display: 'inline' },
  inlineBlock: { display: 'inline-block' },
  flex: { display: 'flex' },
  inlineFlex: { display: 'inline-flex' },
  grid: { display: 'grid' },
  none: { display: 'none' },
  hidden: { visibility: 'hidden' },
  visible: { visibility: 'visible' },
});

// Overflow utilities
export const overflow = stylex.create({
  auto: { overflow: 'auto' },
  hidden: { overflow: 'hidden' },
  visible: { overflow: 'visible' },
  scroll: { overflow: 'scroll' },
  xAuto: { overflowX: 'auto' },
  yAuto: { overflowY: 'auto' },
  xHidden: { overflowX: 'hidden' },
  yHidden: { overflowY: 'hidden' },
});

// Cursor utilities
export const cursor = stylex.create({
  auto: { cursor: 'auto' },
  default: { cursor: 'default' },
  pointer: { cursor: 'pointer' },
  wait: { cursor: 'wait' },
  text: { cursor: 'text' },
  move: { cursor: 'move' },
  notAllowed: { cursor: 'not-allowed' },
  grab: { cursor: 'grab' },
  grabbing: { cursor: 'grabbing' },
});

// User select utilities
export const select = stylex.create({
  none: { userSelect: 'none' },
  text: { userSelect: 'text' },
  all: { userSelect: 'all' },
  auto: { userSelect: 'auto' },
});