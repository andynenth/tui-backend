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
    padding: '1.5rem',
  },
  
  tutorialCard: {
    maxWidth: '900px',
    margin: '0 auto',
    backgroundColor: '#ffffff',
    borderRadius: '0.5rem',
    boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
    overflow: 'hidden',
  },
  
  header: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    padding: '1.5rem',
    textAlign: 'center',
  },
  
  headerTitle: {
    fontSize: '1.5rem',
    fontWeight: '700',
    marginBottom: '0.5rem',
  },
  
  progressBar: {
    display: 'flex',
    gap: '0.25rem',
    justifyContent: 'center',
    marginTop: '1rem',
  },
  
  progressDot: {
    width: '8px',
    height: '8px',
    borderRadius: '50%',
    backgroundColor: 'rgba(255, 255, 255, 0.3)',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
  },
  
  progressDotActive: {
    width: '24px',
    borderRadius: '4px',
    backgroundColor: '#ffffff',
  },
  
  content: {
    padding: '2rem',
    minHeight: '400px',
    animation: `${fadeIn} 0.3s 'cubic-bezier(0, 0, 0.2, 1)'`,
  },
  
  slideTitle: {
    fontSize: '1.5rem',
    fontWeight: '700',
    color: '#212529',
    marginBottom: '1.5rem',
    textAlign: 'center',
  },
  
  // Welcome slide styles
  welcomeHero: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  
  heroIcon: {
    fontSize: '64px',
    marginBottom: '1rem',
  },
  
  heroText: {
    fontSize: '1.125rem',
    color: '#495057',
  },
  
  infoCards: {
    display: 'grid',
    gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
    gap: '1rem',
    marginTop: '2rem',
  },
  
  infoCard: {
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
    padding: '1.5rem',
    textAlign: 'center',
    animation: `${slideIn} 0.4s 'cubic-bezier(0, 0, 0.2, 1)' both`,
  },
  
  infoCardTitle: {
    display: 'flex',
    alignItems: 'center',
    justifyContent: 'center',
    gap: '0.5rem',
    fontSize: '1.125rem',
    fontWeight: '600',
    color: '#212529',
    marginBottom: '0.5rem',
  },
  
  infoCardDesc: {
    fontSize: '0.875rem',
    color: '#6c757d',
    lineHeight: 1.5,
  },
  
  // Piece showcase styles
  pieceShowcase: {
    display: 'flex',
    flexDirection: 'column',
    gap: '1rem',
    padding: '1.5rem',
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
  },
  
  pieceGroup: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
    padding: '0.5rem',
    borderBottomWidth: '1px',
    borderBottomStyle: 'solid',
    borderBottomColor: '#e9ecef',
  },
  
  pieceSet: {
    display: 'flex',
    gap: '0.5rem',
    alignItems: 'center',
  },
  
  soldiersSection: {
    marginTop: '1rem',
    padding: '1rem',
    backgroundColor: '#ffffff',
    borderRadius: '0.375rem',
  },
  
  soldierRow: {
    display: 'flex',
    gap: '0.5rem',
    justifyContent: 'center',
    marginBottom: '0.5rem',
  },
  
  tutorialNote: {
    marginTop: '1.5rem',
    padding: '1rem',
    backgroundColor: '#e7f1ff',
    borderRadius: '0.375rem',
    textAlign: 'center',
    fontSize: '0.875rem',
    color: '#0056b3',
    fontWeight: '500',
  },
  
  // Phase content styles
  prepContainer: {
    padding: '1.5rem',
  },
  
  prepHeader: {
    textAlign: 'center',
    marginBottom: '2rem',
  },
  
  prepTitle: {
    fontSize: '1.25rem',
    fontWeight: '600',
    color: '#343a40',
  },
  
  prepContent: {
    backgroundColor: '#f8f9fa',
    borderRadius: '0.375rem',
    padding: '1.5rem',
  },
  
  prepItem: {
    padding: '1rem',
  },
  
  prepItemTitle: {
    fontSize: '1.125rem',
    fontWeight: '500',
    color: '#212529',
    marginBottom: '0.5rem',
  },
  
  prepItemText: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.5rem',
    fontSize: '1rem',
    color: '#495057',
  },
  
  prepDivider: {
    height: '1px',
    backgroundColor: '#e9ecef',
    margin: `'1rem' 0`,
  },
  
  prepWarning: {
    marginTop: '0.5rem',
    padding: '0.5rem',
    backgroundColor: '#fef3c7',
    borderRadius: '0.125rem',
    fontSize: '0.875rem',
    color: '#92400e',
  },
  
  // Navigation styles
  navigation: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    padding: '1.5rem',
    borderTopWidth: '1px',
    borderTopStyle: 'solid',
    borderTopColor: '#e9ecef',
  },
  
  navButton: {
    padding: `'0.5rem' '1.5rem'`,
    fontSize: '1rem',
    fontWeight: '500',
    borderRadius: '0.375rem',
    border: 'none',
    cursor: 'pointer',
    transition: `all '150ms' 'cubic-bezier(0.4, 0, 0.2, 1)'`,
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.5rem',
  },
  
  prevButton: {
    backgroundColor: '#e9ecef',
    color: '#495057',
    ':hover:not(:disabled)': {
      backgroundColor: '#dee2e6',
      transform: 'translateX(-4px)',
    },
    ':disabled': {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
  },
  
  nextButton: {
    backgroundColor: '#0d6efd',
    color: '#ffffff',
    ':hover:not(:disabled)': {
      backgroundColor: '#0056b3',
      transform: 'translateX(4px)',
    },
    ':disabled': {
      opacity: 0.3,
      cursor: 'not-allowed',
    },
  },
  
  exitButton: {
    backgroundColor: '#dc3545',
    color: '#ffffff',
    ':hover': {
      backgroundColor: '#a71e2a',
      transform: 'scale(1.05)',
    },
  },
  
  slideIndicator: {
    fontSize: '0.875rem',
    color: '#6c757d',
    fontWeight: '500',
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