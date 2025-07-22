// frontend/src/pages/TutorialPage.jsx

import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Layout } from '../components';
import { GamePiece, PlayerAvatar } from '../components/game/shared';
import { useTheme } from '../contexts/ThemeContext';

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

  const slides = [
    // Slide 1: Welcome
    {
      title: '🎉 Welcome to Liap',
      content: (
        <div className="tutorial-welcome">
          <p className="tutorial-tagline">
            A game of wit, risk, and prediction
          </p>
          <p className="tutorial-intro">
            Liap is a strategic trick-taking card game where every round challenges your ability to predict and outplay your opponents.
          </p>
          <div className="tutorial-info-cards">
            <div className="info-card">
              <span className="info-icon">👥</span>
              <span className="info-label">Players:</span>
              <span className="info-value">4</span>
            </div>
            <div className="info-card">
              <span className="info-icon">🎯</span>
              <span className="info-label">Goal:</span>
              <span className="info-value">Be the first to reach 50 points</span>
            </div>
            <div className="info-card">
              <span className="info-icon">🃏</span>
              <span className="info-label">How to Win:</span>
              <span className="info-value">Predict how many tricks you'll win each round — then make it happen!</span>
            </div>
          </div>
        </div>
      ),
    },
    // Slide 2: Know Your Army
    {
      title: 'Know Your Army',
      content: (
        <div className="tutorial-pieces">
          <div className="piece-grid">
            <div className="piece-row">
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={samplePieces.general} size="small" />
                  <GamePiece piece={{ ...samplePieces.general, color: 'BLACK' }} size="small" />
                </div>
                <span className="piece-name">General</span>
                <span className="piece-value">11 points</span>
              </div>
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={{ ...samplePieces.advisor, color: 'RED' }} size="small" />
                  <GamePiece piece={samplePieces.advisor} size="small" />
                </div>
                <span className="piece-name">Advisor</span>
                <span className="piece-value">10 points</span>
              </div>
            </div>
            <div className="piece-row">
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={samplePieces.elephant} size="small" />
                  <GamePiece piece={{ ...samplePieces.elephant, color: 'BLACK' }} size="small" />
                </div>
                <span className="piece-name">Elephant</span>
                <span className="piece-value">9 points</span>
              </div>
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={{ ...samplePieces.horse, color: 'RED' }} size="small" />
                  <GamePiece piece={samplePieces.horse} size="small" />
                </div>
                <span className="piece-name">Horse</span>
                <span className="piece-value">8 points</span>
              </div>
            </div>
            <div className="piece-row">
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={samplePieces.chariot} size="small" />
                  <GamePiece piece={{ ...samplePieces.chariot, color: 'BLACK' }} size="small" />
                </div>
                <span className="piece-name">Chariot</span>
                <span className="piece-value">7 points</span>
              </div>
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={{ ...samplePieces.cannon, color: 'RED' }} size="small" />
                  <GamePiece piece={samplePieces.cannon} size="small" />
                </div>
                <span className="piece-name">Cannon</span>
                <span className="piece-value">6 points</span>
              </div>
            </div>
            <div className="piece-row">
              <div className="piece-item">
                <div className="piece-display">
                  <GamePiece piece={samplePieces.soldier1} size="small" />
                  <GamePiece piece={samplePieces.soldier2} size="small" />
                </div>
                <span className="piece-name">Soldiers</span>
                <span className="piece-value">1-5 points</span>
              </div>
            </div>
          </div>
          <p className="tutorial-note">
            Higher value pieces beat lower ones. Same value? First played wins!
          </p>
        </div>
      ),
    },
    // Slide 3: Preparation Phase
    {
      title: 'Phase 1: Preparation',
      content: (
        <div className="tutorial-phase">
          <div className="phase-steps">
            <div className="phase-step">
              <div className="step-icon">🃏</div>
              <div className="step-content">
                <h4>Deal 8 Pieces</h4>
                <p>Each player receives 8 random pieces</p>
              </div>
            </div>
            <div className="phase-step">
              <div className="step-icon">🔍</div>
              <div className="step-content">
                <h4>Check Your Hand</h4>
                <p>Weak hand = no piece &gt; 9 points</p>
              </div>
            </div>
            <div className="phase-step">
              <div className="step-icon">🔄</div>
              <div className="step-content">
                <h4>Redeal Option</h4>
                <p>Request new deal (costs multiplier)</p>
              </div>
            </div>
          </div>
          <div className="phase-note">
            <strong>Note:</strong> The player with the Red General starts the round!
          </div>
        </div>
      ),
    },
    // Slide 4: Declaration Phase
    {
      title: 'Phase 2: Declaration',
      content: (
        <div className="tutorial-phase">
          <div className="phase-steps">
            <div className="phase-step">
              <div className="step-icon">🎯</div>
              <div className="step-content">
                <h4>Declare 0-8 Piles</h4>
                <p>Predict how many you'll win</p>
              </div>
            </div>
            <div className="phase-step">
              <div className="step-icon">⚠️</div>
              <div className="step-content">
                <h4>Important Rule</h4>
                <p>Total declarations ≠ 8 (forces competition)</p>
              </div>
            </div>
          </div>
          <div className="example-box">
            <strong>Example:</strong><br />
            If 3 players declared 2, 2, 3 (total=7)<br />
            The last player CANNOT declare 1
          </div>
        </div>
      ),
    },
    // Slide 5: Playing Phase
    {
      title: 'Phase 3: Playing',
      content: (
        <div className="tutorial-phase">
          <div className="phase-steps">
            <div className="phase-step">
              <div className="step-icon">⚔️</div>
              <div className="step-content">
                <h4>Take Turns Playing</h4>
                <p>Starter plays 1-6 pieces (must be valid)</p>
              </div>
            </div>
            <div className="phase-step">
              <div className="step-icon">🎴</div>
              <div className="step-content">
                <h4>Others Must Match</h4>
                <p>Play same number (can forfeit with invalid)</p>
              </div>
            </div>
            <div className="phase-step">
              <div className="step-icon">🏆</div>
              <div className="step-content">
                <h4>Winner Takes All</h4>
                <p>Highest wins pile, starts next turn</p>
              </div>
            </div>
          </div>
          <div className="phase-note">
            <strong>Forfeit Strategy:</strong> Non-starters can play invalid combinations to dump unwanted pieces!
          </div>
        </div>
      ),
    },
    // Slide 6: Play Types
    {
      title: 'Valid Play Types',
      content: (
        <div className="tutorial-play-types">
          <div className="play-type-grid">
            <div className="play-type">
              <div className="play-pieces">
                <GamePiece piece={samplePieces.cannon} size="mini" />
              </div>
              <span>Single</span>
            </div>
            <div className="play-type">
              <div className="play-pieces">
                <GamePiece piece={samplePieces.horse} size="mini" />
                <GamePiece piece={samplePieces.horse} size="mini" />
              </div>
              <span>Pair</span>
            </div>
            <div className="play-type">
              <div className="play-pieces">
                <GamePiece piece={samplePieces.soldier1} size="mini" />
                <GamePiece piece={samplePieces.soldier1} size="mini" />
                <GamePiece piece={samplePieces.soldier1} size="mini" />
              </div>
              <span>Three-of-a-kind</span>
            </div>
            <div className="play-type">
              <div className="play-pieces">
                <GamePiece piece={samplePieces.cannon} size="mini" />
                <GamePiece piece={samplePieces.chariot} size="mini" />
                <GamePiece piece={samplePieces.horse} size="mini" />
              </div>
              <span>Straight</span>
            </div>
          </div>
          <div className="play-type-notes">
            <p><strong>Remember:</strong></p>
            <ul>
              <li>Pair = same name & color</li>
              <li>Three-of-a-kind = 3 soldiers only</li>
              <li>Straight = consecutive ranks</li>
              <li>4-6 pieces have extended variations</li>
            </ul>
            <p className="note-small">Only the starter must play valid combinations!</p>
          </div>
        </div>
      ),
    },
    // Slide 7: Scoring
    {
      title: 'Scoring System',
      content: (
        <div className="tutorial-scoring">
          <div className="scoring-example">
            <h4>Example: Perfect Hit</h4>
            <div className="scoring-row">
              <span>Declared:</span>
              <span className="value">2 piles</span>
            </div>
            <div className="scoring-row">
              <span>Actually won:</span>
              <span className="value">2 piles ✓</span>
            </div>
            <div className="scoring-row total">
              <span>Score:</span>
              <span className="value success">2 + 5 = +7</span>
            </div>
          </div>
          
          <div className="scoring-cards">
            <div className="scoring-card special">
              <div className="card-icon">💎</div>
              <strong>0/0 = +3 pts</strong>
              <small>Risky but rewarding!</small>
            </div>
            <div className="scoring-card penalty">
              <strong>Miss = -|diff|</strong>
              <small>Declare 3, win 1 = -2</small>
            </div>
          </div>
        </div>
      ),
    },
  ];

  const updateSlide = () => {
    // Update any UI elements if needed
  };

  const nextSlide = () => {
    if (currentSlide < totalSlides - 1) {
      setCurrentSlide(currentSlide + 1);
      updateSlide();
    }
  };

  const prevSlide = () => {
    if (currentSlide > 0) {
      setCurrentSlide(currentSlide - 1);
      updateSlide();
    }
  };

  const goToSlide = (index) => {
    setCurrentSlide(index);
    updateSlide();
  };

  const skipTutorial = () => {
    navigate('/');
  };

  const finishTutorial = () => {
    navigate('/');
  };

  return (
    <Layout 
      title="How to Play" 
      showConnection={false}
      showHeader={false}
    >
      <div 
        className="min-h-screen flex items-center justify-center"
        style={{ background: 'var(--gradient-gray)' }}
      >
        <div className="tp-gameContainer">
          {/* Tutorial Header with dynamic slide title */}
          <div className="tp-tutorialHeader">
            {/* Back Button */}
            <button 
              className="tp-backButton" 
              onClick={() => navigate('/')}
              title="Back to Start"
            >
              <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M19 12H5M12 19l-7-7 7-7"/>
              </svg>
            </button>
            <h1 className="tp-tutorialTitle">{slides[currentSlide].title}</h1>
          </div>
          
          {/* Tutorial Content */}
          <div className="tp-tutorialContent">
            <div className="tp-slideContainer">
              {slides.map((slide, index) => (
                <div 
                  key={index}
                  className={`tp-slide ${index === currentSlide ? 'active' : ''}`}
                  style={{ transform: `translateX(${(index - currentSlide) * 100}%)` }}
                >
                  <div className="tp-slideContent">
                    {slide.content}
                  </div>
                </div>
              ))}
            </div>

            {/* Navigation Dots */}
            <div className="tp-navDots">
              {slides.map((_, index) => (
                <div 
                  key={index}
                  className={`tp-dot ${index === currentSlide ? 'active' : ''}`}
                  onClick={() => goToSlide(index)}
                />
              ))}
            </div>
          </div>

          {/* Footer Navigation */}
          <div className="tp-footer">
            <button 
              className="tp-navArrow"
              onClick={prevSlide}
              disabled={currentSlide === 0}
              title="Previous"
            >
              <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M15 18l-6-6 6-6"/>
              </svg>
            </button>
            
            <div className="tp-slideCounter">
              {currentSlide + 1} / {totalSlides}
            </div>
            
            {currentSlide === totalSlides - 1 ? (
              <button 
                className="btn btn-primary btn-sm"
                onClick={finishTutorial}
              >
                Start Playing
              </button>
            ) : (
              <button 
                className="tp-navArrow"
                onClick={nextSlide}
                title="Next"
              >
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <path d="M9 18l6-6-6-6"/>
                </svg>
              </button>
            )}
            
            {currentSlide < totalSlides - 1 && (
              <button className="tp-skipButton" onClick={skipTutorial}>
                Skip tutorial
              </button>
            )}
          </div>
        </div>
      </div>
    </Layout>
  );
};

export default TutorialPage;