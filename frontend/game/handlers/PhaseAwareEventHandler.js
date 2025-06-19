// frontend/game/handlers/PhaseAwareEventHandler.js

/**
 * Phase-aware event handler that validates all incoming events
 * against current phase before processing
 */
export class PhaseAwareEventHandler {
  constructor(gameEventHandler, phaseManager, stateManager) {
    this.gameEventHandler = gameEventHandler;
    this.phaseManager = phaseManager;
    this.stateManager = stateManager;
    
    // Define which events are allowed in each phase
    this.phaseEventMap = {
      waiting: [
        'player_joined',
        'player_left',
        'room_state_update',
        'game_starting'
      ],
      
      redeal: [
        'redeal_phase_started',
        'redeal_prompt',
        'redeal_decision_made',
        'redeal_complete',
        'redeal_phase_complete',
        'new_hand_dealt'
      ],
      
      declaration: [
        'declaration_phase_started',
        'declare',
        'declaration_turn',
        'all_declared',
        'declaration_summary'
      ],
      
      turn: [
        'turn_phase_started',
        'turn_start',
        'play',
        'turn_play_made',
        'turn_resolved',
        'turn_summary',
        'round_complete'
      ],
      
      scoring: [
        'scoring_phase_started',
        'round_scores',
        'total_scores',
        'game_end',
        'next_round_starting'
      ]
    };
    
    // Events that can happen in any phase
    this.globalEvents = [
      'error',
      'connection_lost',
      'connection_restored',
      'player_disconnected',
      'player_reconnected',
      'chat_message',
      'server_announcement'
    ];
    
    // Event queue for out-of-phase events
    this.eventQueue = new Map();
    
    // Violation tracking for debugging
    this.violations = [];
    
    this.setupInterceptor();
  }
  
  /**
   * Set up event interceptor to validate all events
   */
  setupInterceptor() {
    // Store original event handler methods
    const originalHandlers = new Map();
    
    // Get all handler methods from gameEventHandler
    const handlerMethods = Object.getOwnPropertyNames(
      Object.getPrototypeOf(this.gameEventHandler)
    ).filter(name => name.startsWith('handle'));
    
    // Wrap each handler with phase validation
    handlerMethods.forEach(methodName => {
      const originalMethod = this.gameEventHandler[methodName];
      if (typeof originalMethod === 'function') {
        originalHandlers.set(methodName, originalMethod);
        
        // Create wrapped version
        this.gameEventHandler[methodName] = (data) => {
          return this.validateAndHandle(methodName, originalMethod, data);
        };
      }
    });
    
    console.log('✅ Phase-aware event interceptor installed');
  }
  
  /**
   * Validate event against current phase before handling
   */
  validateAndHandle(handlerName, originalHandler, data) {
    // Extract event name from handler name (e.g., handleDeclare -> declare)
    const eventName = this.getEventNameFromHandler(handlerName);
    const currentPhase = this.phaseManager.getCurrentPhaseName();
    
    // Check if event is allowed
    if (this.isEventAllowed(eventName, currentPhase)) {
      console.log(`✅ Event '${eventName}' allowed in phase '${currentPhase}'`);
      return originalHandler.call(this.gameEventHandler, data);
    } else {
      // Log violation
      this.logViolation(eventName, currentPhase, data);
      
      // Check if we should queue the event
      if (this.shouldQueueEvent(eventName, currentPhase)) {
        this.queueEvent(eventName, data);
        console.log(`📦 Event '${eventName}' queued for later processing`);
      } else {
        console.warn(
          `🚫 Event '${eventName}' rejected - not allowed in phase '${currentPhase}'`
        );
      }
      
      return null;
    }
  }
  
  /**
   * Check if an event is allowed in current phase
   */
  isEventAllowed(eventName, phaseName) {
    // Global events are always allowed
    if (this.globalEvents.includes(eventName)) {
      return true;
    }
    
    // Check phase-specific events
    const allowedEvents = this.phaseEventMap[phaseName] || [];
    return allowedEvents.includes(eventName);
  }
  
  /**
   * Determine if event should be queued for later
   */
  shouldQueueEvent(eventName, currentPhase) {
    // Don't queue events that are too early
    // For example, don't queue turn events during redeal phase
    const eventPhase = this.getEventPhase(eventName);
    const phaseOrder = ['waiting', 'redeal', 'declaration', 'turn', 'scoring'];
    
    const currentIndex = phaseOrder.indexOf(currentPhase);
    const eventIndex = phaseOrder.indexOf(eventPhase);
    
    // Only queue if event is for a future phase (not too far ahead)
    return eventIndex > currentIndex && eventIndex <= currentIndex + 1;
  }
  
  /**
   * Queue event for processing when appropriate phase is reached
   */
  queueEvent(eventName, data) {
    const targetPhase = this.getEventPhase(eventName);
    
    if (!this.eventQueue.has(targetPhase)) {
      this.eventQueue.set(targetPhase, []);
    }
    
    this.eventQueue.get(targetPhase).push({
      eventName,
      data,
      timestamp: Date.now()
    });
  }
  
  /**
   * Process queued events when entering a new phase
   */
  processQueuedEvents(phaseName) {
    const queuedEvents = this.eventQueue.get(phaseName) || [];
    
    if (queuedEvents.length > 0) {
      console.log(`📤 Processing ${queuedEvents.length} queued events for phase '${phaseName}'`);
      
      queuedEvents.forEach(({ eventName, data, timestamp }) => {
        // Skip stale events (older than 30 seconds)
        if (Date.now() - timestamp > 30000) {
          console.log(`⏭️ Skipping stale event '${eventName}'`);
          return;
        }
        
        // Find and call the appropriate handler
        const handlerName = this.getHandlerNameFromEvent(eventName);
        const handler = this.gameEventHandler[handlerName];
        
        if (handler) {
          console.log(`▶️ Processing queued event '${eventName}'`);
          handler.call(this.gameEventHandler, data);
        }
      });
      
      // Clear the queue for this phase
      this.eventQueue.delete(phaseName);
    }
  }
  
  /**
   * Log phase violation for debugging
   */
  logViolation(eventName, currentPhase, data) {
    const violation = {
      eventName,
      currentPhase,
      timestamp: Date.now(),
      player: data.player || 'unknown',
      isBot: data.is_bot || false
    };
    
    this.violations.push(violation);
    
    // Keep only last 50 violations
    if (this.violations.length > 50) {
      this.violations.shift();
    }
    
    console.warn('📛 Phase violation:', violation);
  }
  
  /**
   * Get event name from handler method name
   */
  getEventNameFromHandler(handlerName) {
    // handleDeclare -> declare
    // handleTurnResolved -> turn_resolved
    const name = handlerName.replace('handle', '');
    return name.charAt(0).toLowerCase() + 
           name.slice(1).replace(/([A-Z])/g, '_$1').toLowerCase();
  }
  
  /**
   * Get handler name from event name
   */
  getHandlerNameFromEvent(eventName) {
    // declare -> handleDeclare
    // turn_resolved -> handleTurnResolved
    const parts = eventName.split('_');
    const capitalized = parts.map(part => 
      part.charAt(0).toUpperCase() + part.slice(1)
    ).join('');
    
    return 'handle' + capitalized;
  }
  
  /**
   * Determine which phase an event belongs to
   */
  getEventPhase(eventName) {
    for (const [phase, events] of Object.entries(this.phaseEventMap)) {
      if (events.includes(eventName)) {
        return phase;
      }
    }
    return null;
  }
  
  /**
   * Get violation report for debugging
   */
  getViolationReport() {
    const report = {
      totalViolations: this.violations.length,
      violationsByPhase: {},
      violationsByEvent: {},
      botViolations: 0
    };
    
    this.violations.forEach(v => {
      // By phase
      report.violationsByPhase[v.currentPhase] = 
        (report.violationsByPhase[v.currentPhase] || 0) + 1;
      
      // By event
      report.violationsByEvent[v.eventName] = 
        (report.violationsByEvent[v.eventName] || 0) + 1;
      
      // Bot violations
      if (v.isBot) {
        report.botViolations++;
      }
    });
    
    return report;
  }
  
  /**
   * Clear all queued events
   */
  clearEventQueues() {
    this.eventQueue.clear();
    console.log('🗑️ Cleared all event queues');
  }
  
  /**
   * Hook for phase transitions
   */
  onPhaseTransition(fromPhase, toPhase) {
    console.log(`🔄 Phase transition: ${fromPhase} → ${toPhase}`);
    
    // Process any queued events for the new phase
    this.processQueuedEvents(toPhase);
    
    // Clear old queued events (older phases)
    const phaseOrder = ['waiting', 'redeal', 'declaration', 'turn', 'scoring'];
    const newPhaseIndex = phaseOrder.indexOf(toPhase);
    
    phaseOrder.forEach((phase, index) => {
      if (index < newPhaseIndex) {
        this.eventQueue.delete(phase);
      }
    });
  }
}

// Integration with GameEventHandler
export function installPhaseValidator(gameEventHandler, phaseManager, stateManager) {
  const validator = new PhaseAwareEventHandler(
    gameEventHandler, 
    phaseManager, 
    stateManager
  );
  
  // Listen for phase changes
  phaseManager.on('phaseChanged', ({ from, to }) => {
    validator.onPhaseTransition(from, to);
  });
  
  return validator;
}