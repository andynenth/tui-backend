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
      title: 'Welcome to Liap!',
      content: (
        <div className="tutorial-phase">
          <div className="prep-steps">
            <div className="prep-step">
              <div className="step-number">🎮</div>
              <div className="step-text">
                <strong>What is Liap?</strong>
                <p className="step-detail">A strategic trick-taking game where prediction meets skill. Outsmart your opponents by accurately forecasting your victories!</p>
              </div>
            </div>
            
            <div className="prep-step">
              <div className="step-number">📊</div>
              <div className="step-text">
                <strong>Game Setup</strong>
                <div className="game-setup-details">
                  <div className="setup-row">
                    <span className="setup-icon">👥</span>
                    <span><strong>4 Players</strong> compete each round</span>
                  </div>
                  <div className="setup-row">
                    <span className="setup-icon">🎯</span>
                    <span>First to <strong>50 Points</strong> wins</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="prep-step" style={{background: 'rgba(255, 193, 7, 0.05)', borderColor: 'rgba(255, 193, 7, 0.2)'}}>
              <div className="step-number" style={{background: 'var(--color-warning)', color: 'var(--color-gray-800)'}}>🎯</div>
              <div className="step-text">
                <strong>How to Win</strong>
                <p className="step-detail">Score points by accurately predicting how many tricks (piles) you'll win each round.</p>
                <div className="key-rule">
                  💡 Remember: It's not about winning the most tricks — it's about winning <strong>exactly</strong> what you predict!
                </div>
              </div>
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
          <div className="piece-showcase">
            {/* Generals - 1 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={samplePieces.general} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.general, color: 'BLACK' }} size="small" />
              </div>
            </div>
            
            {/* Advisors - 2 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.advisor, color: 'RED' }} size="small" />
                <GamePiece piece={{ ...samplePieces.advisor, color: 'RED' }} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={samplePieces.advisor} size="small" />
                <GamePiece piece={samplePieces.advisor} size="small" />
              </div>
            </div>
            
            {/* Elephants - 2 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={samplePieces.elephant} size="small" />
                <GamePiece piece={samplePieces.elephant} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.elephant, color: 'BLACK' }} size="small" />
                <GamePiece piece={{ ...samplePieces.elephant, color: 'BLACK' }} size="small" />
              </div>
            </div>
            
            {/* Horses - 2 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.horse, color: 'RED' }} size="small" />
                <GamePiece piece={{ ...samplePieces.horse, color: 'RED' }} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={samplePieces.horse} size="small" />
                <GamePiece piece={samplePieces.horse} size="small" />
              </div>
            </div>
            
            {/* Chariots - 2 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={samplePieces.chariot} size="small" />
                <GamePiece piece={samplePieces.chariot} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.chariot, color: 'BLACK' }} size="small" />
                <GamePiece piece={{ ...samplePieces.chariot, color: 'BLACK' }} size="small" />
              </div>
            </div>
            
            {/* Cannons - 2 each */}
            <div className="piece-group">
              <div className="piece-set">
                <GamePiece piece={{ ...samplePieces.cannon, color: 'RED' }} size="small" />
                <GamePiece piece={{ ...samplePieces.cannon, color: 'RED' }} size="small" />
              </div>
              <div className="piece-set">
                <GamePiece piece={samplePieces.cannon} size="small" />
                <GamePiece piece={samplePieces.cannon} size="small" />
              </div>
            </div>
            
            {/* Soldiers - 5 each, stacked vertically */}
            <div className="soldiers-section">
              <div className="soldier-row">
                <GamePiece piece={{ kind: 'SOLDIER', color: 'RED', value: 5 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'RED', value: 4 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'RED', value: 3 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'RED', value: 2 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'RED', value: 1 }} size="small" />
              </div>
              <div className="soldier-row">
                <GamePiece piece={{ kind: 'SOLDIER', color: 'BLACK', value: 5 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'BLACK', value: 4 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'BLACK', value: 3 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'BLACK', value: 2 }} size="small" />
                <GamePiece piece={{ kind: 'SOLDIER', color: 'BLACK', value: 1 }} size="small" />
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
          <div className="prep-steps">
            <div className="prep-step">
              <div className="step-number">1</div>
              <div className="step-text">
                <strong>Deal Phase</strong>
                <p className="step-detail">Each player receives 8 random pieces from the deck. These are your soldiers for this round.</p>
              </div>
            </div>
            
            <div className="prep-step weak">
              <div className="step-number">2</div>
              <div className="step-text">
                <strong>Check for Weak Hand</strong>
                <div className="weak-definition">
                  <div>If your strongest piece is only <GamePiece piece={{ kind: 'ELEPHANT', color: 'BLACK', value: 9 }} size="mini" /> or lower:</div>
                  <div className="redeal-option">
                    • You may request a redeal<br/>
                    • All players get new hands<br/>
                    • <span className="warning">Warning: Reduces your score multiplier!</span>
                  </div>
                </div>
              </div>
            </div>
            
            <div className="prep-step starter">
              <div className="step-number">3</div>
              <div className="step-text">
                <strong>Starting Player</strong>
                <p className="step-detail">
                  The player holding <GamePiece piece={samplePieces.general} size="mini" /> will lead the first trick and set the pace for the round.
                </p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    // Slide 4: Declaration Phase
    {
      title: 'Phase 2: Declaration',
      content: (
        <div className="tutorial-phase">
          <div className="prep-steps">
            <div className="prep-step">
              <div className="step-number">1</div>
              <div className="step-text">
                <strong>Make Your Prediction</strong>
                <p className="step-detail">Each player declares how many tricks (0-8) they expect to win this round. This is your target score.</p>
              </div>
            </div>
            <div className="prep-step" style={{background: 'rgba(220, 53, 69, 0.05)', borderColor: 'rgba(220, 53, 69, 0.2)'}}>
              <div className="step-number" style={{background: 'var(--color-danger)', color: 'white'}}>!</div>
              <div className="step-text">
                <strong>The Forcing Rule</strong>
                <p className="step-detail">Total declarations cannot equal 8! This guarantees competition - not everyone can achieve their goal.</p>
                <div className="example-box" style={{marginTop: '8px'}}>
                  <strong>Example:</strong> If 3 players declared 2, 2, 3 (total = 7), the last player CANNOT declare 1
                </div>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    // Slide 5: Playing Phase
    {
      title: 'Phase 3: Playing',
      content: (
        <div className="tutorial-phase">
          <div className="prep-steps">
            <div className="prep-step">
              <div className="step-number">1</div>
              <div className="step-text">
                <strong>Leader Plays First</strong>
                <p className="step-detail">The trick leader plays 1-6 pieces. Must be a valid combination (single, pair, three-of-a-kind, or straight).</p>
              </div>
            </div>
            <div className="prep-step">
              <div className="step-number">2</div>
              <div className="step-text">
                <strong>Others Follow</strong>
                <p className="step-detail">Each player must play the same number of pieces. You can play invalid combinations to forfeit the trick.</p>
              </div>
            </div>
            <div className="prep-step">
              <div className="step-number">3</div>
              <div className="step-text">
                <strong>Winner Takes Trick</strong>
                <p className="step-detail">Highest valid play wins all pieces in the trick and leads the next one.</p>
              </div>
            </div>
            <div className="prep-step" style={{background: 'rgba(255, 193, 7, 0.05)', borderColor: 'rgba(255, 193, 7, 0.2)'}}>
              <div className="step-number" style={{background: 'var(--color-warning)', color: 'var(--color-gray-800)'}}>💡</div>
              <div className="step-text">
                <strong>Strategic Forfeit</strong>
                <p className="step-detail">Playing invalid combinations lets you dump unwanted pieces without winning tricks you don't want!</p>
              </div>
            </div>
          </div>
        </div>
      ),
    },
    // Slide 6: Play Types
    {
      title: 'Valid Play Types',
      content: (
        <div className="tutorial-phase">
          <div className="play-types-showcase">
            <div className="play-type-item">
              <div className="play-type-visual">
                <GamePiece piece={samplePieces.cannon} size="small" />
              </div>
              <div className="play-type-info">
                <strong>Single</strong>
                <p className="step-detail">Any one piece</p>
              </div>
            </div>
            
            <div className="play-type-item">
              <div className="play-type-visual">
                <GamePiece piece={samplePieces.horse} size="small" />
                <GamePiece piece={samplePieces.horse} size="small" />
              </div>
              <div className="play-type-info">
                <strong>Pair</strong>
                <p className="step-detail">Two pieces of same type AND same color</p>
              </div>
            </div>
            
            <div className="play-type-item">
              <div className="play-type-visual">
                <GamePiece piece={samplePieces.soldier1} size="small" />
                <GamePiece piece={samplePieces.soldier1} size="small" />
                <GamePiece piece={samplePieces.soldier1} size="small" />
              </div>
              <div className="play-type-info">
                <strong>Three-of-a-kind</strong>
                <p className="step-detail">Three soldiers only (any combination)</p>
              </div>
            </div>
            
            <div className="play-type-item">
              <div className="play-type-visual">
                <GamePiece piece={{ ...samplePieces.cannon, color: 'RED' }} size="small" />
                <GamePiece piece={samplePieces.chariot} size="small" />
                <GamePiece piece={{ ...samplePieces.horse, color: 'RED' }} size="small" />
              </div>
              <div className="play-type-info">
                <strong>Straight</strong>
                <p className="step-detail">Consecutive values (all same color)</p>
              </div>
            </div>
          </div>
          
          <div className="prep-step" style={{background: 'rgba(255, 193, 7, 0.05)', borderColor: 'rgba(255, 193, 7, 0.2)', marginTop: '16px'}}>
            <div className="step-number" style={{background: 'var(--color-warning)', color: 'var(--color-gray-800)'}}>!</div>
            <div className="step-text">
              <strong>Key Rule</strong>
              <p className="step-detail">Only the trick leader needs valid combinations. Others can play any pieces to match the count!</p>
            </div>
          </div>
        </div>
      ),
    },
    // Slide 7: Scoring
    {
      title: 'Scoring System',
      content: (
        <div className="tutorial-phase">
          <div className="prep-steps">
            <div className="prep-step compact">
              <div className="step-number">✓</div>
              <div className="step-text">
                <strong>Hit Your Target</strong>
                <p className="step-detail">Win exactly what you declared = <strong>Tricks + 5 bonus</strong></p>
                <div className="example-inline">
                  Example: Declare 2, win 2 = 2 + 5 = <strong>+7 points</strong>
                </div>
              </div>
            </div>
            
            <div className="prep-step compact" style={{background: 'rgba(220, 53, 69, 0.05)', borderColor: 'rgba(220, 53, 69, 0.2)'}}>
              <div className="step-number" style={{background: 'var(--color-danger)', color: 'white'}}>✗</div>
              <div className="step-text">
                <strong>Miss Your Target</strong>
                <p className="step-detail">Penalty = <strong>-|difference|</strong> between declared and won</p>
                <div className="example-inline">
                  Example: Declare 3, win 1 = -(3-1) = <strong>-2 points</strong>
                </div>
              </div>
            </div>
            
            <div className="prep-step" style={{background: 'rgba(255, 193, 7, 0.05)', borderColor: 'rgba(255, 193, 7, 0.2)'}}>
              <div className="step-number" style={{background: 'var(--color-warning)', color: 'var(--color-gray-800)'}}>💎</div>
              <div className="step-text">
                <strong>Special: The 0/0 Strategy</strong>
                <p className="step-detail">Declaring 0 and winning 0 tricks gives <strong>+3 points</strong>. High risk, but saves you when you have a terrible hand!</p>
              </div>
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