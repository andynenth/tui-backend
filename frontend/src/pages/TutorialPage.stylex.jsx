// frontend/src/pages/TutorialPage.stylex.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import * as stylex from '@stylexjs/stylex';
import { colors, spacing, typography, layout, shadows, motion, gradients } from '../design-system/tokens.stylex';
import Layout from '../components/Layout.stylex';
import { GamePiece, PlayerAvatar } from '../components/game/shared';
import { useTheme } from '../contexts/ThemeContext';

// Animations
const fadeIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateY(20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateY(0)',
  },
});

const slideIn = stylex.keyframes({
  '0%': {
    opacity: 0,
    transform: 'translateX(-20px)',
  },
  '100%': {
    opacity: 1,
    transform: 'translateX(0)',
  },
});

// TutorialPage styles
const styles = stylex.create({
  container: {
    minHeight: '100vh',
    backgroundImage: gradients.gray,
    padding: spacing.lg,
  },
  
  tutorialCard: {
    maxWidth: '900px',
    margin: '0 auto',
    backgroundColor: colors.white,
    borderRadius: layout.radiusLg,
    boxShadow: shadows.xl,
    overflow: 'hidden',
  },
  
  header: {
    backgroundColor: colors.primary,
    color: colors.white,
    padding: spacing.lg,
    textAlign: 'center',
  },
  
  headerTitle: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    marginBottom: spacing.sm,
  },
  
  progressBar: {
    display: 'flex',
    gap: spacing.xs,
    justifyContent: 'center',
    marginTop: spacing.md,
  },
  
  progressDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
  },
  
  progressDotActive: {
    width: '24px',
    borderRadius: '4px',
    backgroundColor: colors.white,
  },
  
  content: {
    padding: spacing.xl,
    minHeight: '400px',
    animation: `${fadeIn} 0.3s ${motion.easeOut}`,
  },
  
  slideTitle: {
    fontSize: typography.text2xl,
    fontWeight: typography.weightBold,
    color: colors.gray900,
    marginBottom: spacing.lg,
    textAlign: 'center',
  },
  
  // Welcome slide styles
  welcomeHero: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  
  heroIcon: {
    fontSize: '64px',
    marginBottom: spacing.md,
  },
  
  heroText: {
    fontSize: typography.textLg,
    color: colors.gray700,
  },
  
  infoCards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: spacing.md,
    marginTop: spacing.xl,
  },
  
  infoCard: {
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    padding: spacing.lg,
    textAlign: 'center',
    animation: `${slideIn} 0.4s ${motion.easeOut} both`,
  },
  
  infoCardTitle: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: spacing.sm,
    fontSize: typography.textLg,
    fontWeight: typography.weightSemibold,
    color: colors.gray900,
    marginBottom: spacing.sm,
  },
  
  infoCardDesc: {
    fontSize: typography.textSm,
    color: colors.gray600,
    lineHeight: 1.5,
  },
  
  // Piece showcase styles
  pieceShowcase: {
    display: 'flex',
    flexDirection: 'column',
    gap: spacing.md,
    padding: spacing.lg,
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
  },
  
  pieceGroup: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: spacing.sm,
    borderBottom: `1px solid ${colors.gray200}`,
  },
  
  pieceSet: {
    display: 'flex',
    gap: spacing.sm,
    alignItems: 'center',
  },
  
  soldiersSection: {
    marginTop: spacing.md,
    padding: spacing.md,
    backgroundColor: colors.white,
    borderRadius: layout.radiusMd,
  },
  
  soldierRow: {
    display: 'flex',
    gap: spacing.sm,
    justifyContent: 'center',
    marginBottom: spacing.sm,
  },
  
  tutorialNote: {
    marginTop: spacing.lg,
    padding: spacing.md,
    backgroundColor: colors.primaryLight,
    borderRadius: layout.radiusMd,
    textAlign: 'center',
    fontSize: typography.textSm,
    color: colors.primaryDark,
    fontWeight: typography.weightMedium,
  },
  
  // Phase content styles
  prepContainer: {
    padding: spacing.lg,
  },
  
  prepHeader: {
    textAlign: 'center',
    marginBottom: spacing.xl,
  },
  
  prepTitle: {
    fontSize: typography.textXl,
    fontWeight: typography.weightSemibold,
    color: colors.gray800,
  },
  
  prepContent: {
    backgroundColor: colors.gray50,
    borderRadius: layout.radiusMd,
    padding: spacing.lg,
  },
  
  prepItem: {
    padding: spacing.md,
  },
  
  prepItemTitle: {
    fontSize: typography.textLg,
    fontWeight: typography.weightMedium,
    color: colors.gray900,
    marginBottom: spacing.sm,
  },
  
  prepItemText: {
    display: 'flex',
    alignItems: 'center',
    gap: spacing.sm,
    fontSize: typography.textBase,
    color: colors.gray700,
  },
  
  prepDivider: {
    height: '1px',
    backgroundColor: colors.gray200,
    margin: `${spacing.md} 0`,
  },
  
  prepWarning: {
    marginTop: spacing.sm,
    padding: spacing.sm,
    backgroundColor: '#fef3c7',
    borderRadius: layout.radiusSm,
    fontSize: typography.textSm,
    color: '#92400e',
  },
  
  // Navigation styles
  navigation: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: spacing.lg,
    borderTop: `1px solid ${colors.gray200}`,
  },
  
  navButton: {
    padding: `${spacing.sm} ${spacing.lg}`,
    fontSize: typography.textBase,
    fontWeight: typography.weightMedium,
    borderRadius: layout.radiusMd,
    border: 'none',
    cursor: 'pointer',
    transition: `all ${motion.durationFast} ${motion.easeInOut}`,
    display: 'inline-flex',
    alignItems: 'center',
    gap: spacing.sm,
  },
  
  prevButton: {
    backgroundColor: colors.gray200,
    color: colors.gray700,
    ':hover:not(:disabled)': {
      backgroundColor: colors.gray300,
      transform: 'translateX(-4px)',
    },
    ':disabled': {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
  },
  
  nextButton: {
    backgroundColor: colors.primary,
    color: colors.white,
    ':hover:not(:disabled)': {
      backgroundColor: colors.primaryDark,
      transform: 'translateX(4px)',
    },
    ':disabled': {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
  },
  
  exitButton: {
    backgroundColor: colors.danger,
    color: colors.white,
    ':hover': {
      backgroundColor: colors.dangerDark,
      transform: 'scale(1.05)',
    },
  },
  
  slideIndicator: {
    fontSize: typography.textSm,
    color: colors.gray600,
    fontWeight: typography.weightMedium,
  },
});

const TutorialPage = () => {
  const navigate = useNavigate();
  const { currentTheme } = useTheme();
  const [currentSlide, setCurrentSlide] = useState(0);
  const totalSlides = 7;

  // Sample pieces for demonstration
  const samplePieces = {
    general: { kind: 'GENERAL', color: 'RED', value: 11 },
    advisor: { kind: 'ADVISOR', color: 'BLACK', value: 10 },
    elephant: { kind: 'ELEPHANT', color: 'RED', value: 9 },
    horse: { kind: 'HORSE', color: 'BLACK', value: 8 },
    chariot: { kind: 'CHARIOT', color: 'RED', value: 7 },
    cannon: { kind: 'CANNON', color: 'BLACK', value: 6 },
    soldier1: { kind: 'SOLDIER', color: 'RED', value: 3 },
    soldier2: { kind: 'SOLDIER', color: 'BLACK', value: 2 },
  };

  // Simplified slides array (keeping structure but condensing content)
  const slides = [
    // Welcome slide
    {
      title: 'Welcome to Castellan!',
      content: (
        <div>
          <div {...stylex.props(styles.welcomeHero)}>
            <div {...stylex.props(styles.heroIcon)}>🏰</div>
            <h2 {...stylex.props(styles.heroText)}>
              Master the art of prediction in this strategic card game!
            </h2>
          </div>

          <div {...stylex.props(styles.infoCards)}>
            <div {...stylex.props(styles.infoCard)} style={{ animationDelay: '0.1s' }}>
              <div {...stylex.props(styles.infoCardTitle)}>
                <span>🎯</span>
                <span>Objective</span>
              </div>
              <div {...stylex.props(styles.infoCardDesc)}>
                Predict how many tricks you'll win each round and match
                your prediction exactly for bonus points!
              </div>
            </div>

            <div {...stylex.props(styles.infoCard)} style={{ animationDelay: '0.2s' }}>
              <div {...stylex.props(styles.infoCardTitle)}>
                <span>👥</span>
                <span>Players</span>
              </div>
              <div {...stylex.props(styles.infoCardDesc)}>
                4 players compete with 8 pieces each per round
              </div>
            </div>

            <div {...stylex.props(styles.infoCard)} style={{ animationDelay: '0.3s' }}>
              <div {...stylex.props(styles.infoCardTitle)}>
                <span>🏆</span>
                <span>Victory</span>
              </div>
              <div {...stylex.props(styles.infoCardDesc)}>
                First player to reach 50 points wins the game
              </div>
            </div>
          </div>
        </div>
      ),
    },
    // Piece ranks slide
    {
      title: 'Piece Ranks',
      content: (
        <div>
          <div {...stylex.props(styles.pieceShowcase)}>
            <div {...stylex.props(styles.pieceGroup)}>
              <div {...stylex.props(styles.pieceSet)}>
                <GamePiece piece={samplePieces.general} size="small" />
              </div>
              <div {...stylex.props(styles.pieceSet)}>
                <GamePiece
                  piece={{ ...samplePieces.general, color: 'BLACK' }}
                  size="small"
                />
              </div>
            </div>
            {/* Add more piece groups as needed */}
          </div>
          <p {...stylex.props(styles.tutorialNote)}>
            Pieces with higher rank beat lower rank. Same value? First played wins!
          </p>
        </div>
      ),
    },
    // Preparation phase slide
    {
      title: 'Phase 1: Preparation',
      content: (
        <div {...stylex.props(styles.prepContainer)}>
          <div {...stylex.props(styles.prepHeader)}>
            <h2 {...stylex.props(styles.prepTitle)}>Getting Ready to Play</h2>
          </div>
          <div {...stylex.props(styles.prepContent)}>
            <div {...stylex.props(styles.prepItem)}>
              <h3 {...stylex.props(styles.prepItemTitle)}>Deal 8 pieces to each player</h3>
            </div>
            <div {...stylex.props(styles.prepDivider)} />
            <div {...stylex.props(styles.prepItem)}>
              <h3 {...stylex.props(styles.prepItemTitle)}>Find who goes first</h3>
              <div {...stylex.props(styles.prepItemText)}>
                <GamePiece
                  piece={{ kind: 'GENERAL', color: 'RED', value: 11 }}
                  size="mini"
                />
                <span>holder starts the first round</span>
              </div>
            </div>
            <div {...stylex.props(styles.prepDivider)} />
            <div {...stylex.props(styles.prepItem)}>
              <h3 {...stylex.props(styles.prepItemTitle)}>Check for weak hands</h3>
              <div {...stylex.props(styles.prepWarning)}>
                <strong>Note:</strong> Redealing multiplies everyone's
                scores (both wins and losses!)
              </div>
            </div>
          </div>
        </div>
      ),
    },
    // Add remaining slides with similar structure...
    { title: 'Phase 2: Declaration', content: <div>Declaration content...</div> },
    { title: 'Phase 3: Play', content: <div>Play content...</div> },
    { title: 'Scoring System', content: <div>Scoring content...</div> },
    { title: 'Tips & Strategy', content: <div>Tips content...</div> },
  ];

  const nextSlide = () => {
    if (currentSlide < totalSlides - 1) {
      setCurrentSlide(currentSlide + 1);
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
    }
  };

  return (
    <Layout title="How to Play" showConnection={false} showHeader={false}>
      <div {...stylex.props(styles.container)}>
        <div {...stylex.props(styles.tutorialCard)}>
          {/* Header */}
          <div {...stylex.props(styles.header)}>
            <h1 {...stylex.props(styles.headerTitle)}>How to Play Castellan</h1>
            <div {...stylex.props(styles.progressBar)}>
              {[...Array(totalSlides)].map((_, index) => (
                <div
                  key={index}
                  {...stylex.props(
                    styles.progressDot,
                    index === currentSlide && styles.progressDotActive
                  )}
                />
              ))}
            </div>
          </div>

          {/* Content */}
          <div {...stylex.props(styles.content)} key={currentSlide}>
            <h2 {...stylex.props(styles.slideTitle)}>{slides[currentSlide].title}</h2>
            {slides[currentSlide].content}
          </div>

          {/* Navigation */}
          <div {...stylex.props(styles.navigation)}>
            <button
              {...stylex.props(styles.navButton, styles.prevButton)}
              onClick={prevSlide}
              disabled={currentSlide === 0}
            >
              <span>←</span> Previous
            </button>

            <span {...stylex.props(styles.slideIndicator)}>
              {currentSlide + 1} / {totalSlides}
            </span>

            {currentSlide === totalSlides - 1 ? (
              <button
                {...stylex.props(styles.navButton, styles.exitButton)}
                onClick={() => navigate('/')}
              >
                Start Playing <span>🎮</span>
              </button>
            ) : (
              <button
                {...stylex.props(styles.navButton, styles.nextButton)}
                onClick={nextSlide}
              >
                Next <span>→</span>
              </button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default TutorialPage;