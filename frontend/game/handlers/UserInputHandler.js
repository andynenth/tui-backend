// frontend/game/handlers/UserInputHandler.js
/**
 * Centralized user input handling
 * Manages keyboard, mouse, and touch inputs for the game
 *
 * Responsibilities:
 * - Input event registration
 * - Input validation
 * - Input routing to phases
 * - Input queue management
 * - Shortcut handling
 */
export class UserInputHandler {
  constructor(phaseManager, uiRenderer) {
    this.phaseManager = phaseManager;
    this.uiRenderer = uiRenderer;

    // Input state
    this.isEnabled = true;
    this.inputQueue = [];
    this.shortcuts = new Map();

    // Input mode
    this.currentInputMode = null; // 'text', 'selection', 'confirmation', 'redeal', 'declaration'
    this.currentInputCallback = null;

    // Key state tracking
    this.keysPressed = new Set();

    // Bind methods
    this.handleKeyDown = this.handleKeyDown.bind(this);
    this.handleKeyUp = this.handleKeyUp.bind(this);
    this.handleClick = this.handleClick.bind(this);
  }

  /**
   * Initialize input handlers
   */
  initialize() {
    // Keyboard events
    window.addEventListener("keydown", this.handleKeyDown);
    window.addEventListener("keyup", this.handleKeyUp);

    // Register default shortcuts
    this.registerDefaultShortcuts();

    console.log("🎮 Input handler initialized");
  }

  /**
   * Register default keyboard shortcuts
   */
  registerDefaultShortcuts() {
    // Quick actions
    this.registerShortcut("Enter", () => {
      if (
        this.currentInputMode === "text" ||
        this.currentInputMode === "declaration"
      ) {
        this.submitTextInput();
      }
    });

    this.registerShortcut("Escape", () => {
      if (this.currentInputMode) {
        this.cancelCurrentInput();
      }
    });

    // Number keys for quick selection
    for (let i = 0; i <= 9; i++) {
      this.registerShortcut(i.toString(), () => {
        if (
          this.currentInputMode === "selection" ||
          this.currentInputMode === "redeal" ||
          this.currentInputMode === "declaration"
        ) {
          this.handleNumberSelection(i);
        }
      });
    }

    // Y/N keys for redeal phase
    this.registerShortcut("y", () => {
      if (this.currentInputMode === "redeal") {
        this.handleRedealShortcut("Yes");
      }
    });

    this.registerShortcut("n", () => {
      if (this.currentInputMode === "redeal") {
        this.handleRedealShortcut("No");
      }
    });

    this.registerShortcut("Y", () => {
      if (this.currentInputMode === "redeal") {
        this.handleRedealShortcut("Yes");
      }
    });

    this.registerShortcut("N", () => {
      if (this.currentInputMode === "redeal") {
        this.handleRedealShortcut("No");
      }
    });

    // Debug shortcuts
    this.registerShortcut("Ctrl+D", () => {
      this.showDebugInfo();
    });
  }

  /**
   * Register a keyboard shortcut
   */
  registerShortcut(key, callback) {
    this.shortcuts.set(key, callback);
  }

  /**
   * Handle keydown events
   */
  handleKeyDown(event) {
    if (!this.isEnabled) return;

    // Track key state
    this.keysPressed.add(event.key);

    // Check for shortcuts
    const shortcutKey = this.getShortcutKey(event);
    if (this.shortcuts.has(shortcutKey)) {
      event.preventDefault();
      this.shortcuts.get(shortcutKey)();
      return;
    }

    // Let text input handle it
    if (
      this.currentInputMode === "text" ||
      this.currentInputMode === "declaration"
    ) {
      return;
    }

    // Phase validation before routing
    const currentPhase = this.phaseManager.getCurrentPhaseName();

    // Don't process game inputs during waiting or scoring phases
    if (currentPhase === "waiting" || currentPhase === "scoring") {
      console.log(`Input blocked during ${currentPhase} phase`);
      return;
    }

    // Route to current phase
    this.phaseManager.handleUserInput({
      type: "keydown",
      key: event.key,
      ctrlKey: event.ctrlKey,
      shiftKey: event.shiftKey,
    });
  }

  /**
   * Handle keyup events
   */
  handleKeyUp(event) {
    this.keysPressed.delete(event.key);
  }

  /**
   * Get shortcut key string
   */
  getShortcutKey(event) {
    let key = event.key;

    if (event.ctrlKey) key = "Ctrl+" + key;
    if (event.shiftKey) key = "Shift+" + key;
    if (event.altKey) key = "Alt+" + key;

    return key;
  }

  /**
   * Handle click events
   */
  handleClick(event) {
    if (!this.isEnabled) return;

    // Route to current phase
    this.phaseManager.handleUserInput({
      type: "click",
      x: event.clientX,
      y: event.clientY,
      target: event.target,
    });
  }

  // ===== INPUT MODES =====

  /**
   * Request text input from user
   */
  async requestTextInput(prompt, validator) {
    return new Promise((resolve) => {
      this.currentInputMode = "text";
      this.currentInputCallback = resolve;

      // Show input UI
      this.uiRenderer.showInput(prompt, validator).then((value) => {
        this.currentInputMode = null;
        this.currentInputCallback = null;
        resolve(value);
      });
    });
  }

  async requestRedealDecision(prompt = "Request redeal?") {
    // Check if we're in redeal phase
    const currentPhase = this.phaseManager.getCurrentPhaseName();
    if (currentPhase !== "redeal") {
      console.warn("Redeal decision requested outside redeal phase");
      return null;
    }

    return new Promise((resolve) => {
      this.currentInputMode = "redeal";
      this.currentInputCallback = resolve;

      // Show redeal input UI
      this.uiRenderer.showRedealInput(["Yes", "No"], (choice) => {
        this.currentInputMode = null;
        this.currentInputCallback = null;
        resolve(choice);
      });
    });
  }

  async requestDeclaration(prompt, validOptions) {
    // Check if we're in declaration phase
    const currentPhase = this.phaseManager.getCurrentPhaseName();
    if (currentPhase !== "declaration") {
      console.warn("Declaration requested outside declaration phase");
      return null;
    }

    return new Promise((resolve) => {
      this.currentInputMode = "declaration";
      this.currentInputCallback = resolve;

      // Show declaration input UI
      this.uiRenderer.showDeclarationInput(validOptions, (value) => {
        this.currentInputMode = null;
        this.currentInputCallback = null;
        resolve(value);
      });
    });
  }

  /**
   * Request selection from user (e.g., card indices)
   */
  async requestSelection(prompt, options, multiSelect = false) {
    return new Promise((resolve) => {
      this.currentInputMode = "selection";
      this.currentInputCallback = resolve;
      this.selectedItems = multiSelect ? [] : null;

      // Show selection UI
      this.uiRenderer.showSelection(
        prompt,
        options,
        multiSelect,
        (selection) => {
          this.currentInputMode = null;
          this.currentInputCallback = null;
          resolve(selection);
        }
      );
    });
  }

  /**
   * Request confirmation from user
   */
  async requestConfirmation(message, options = ["Yes", "No"]) {
    return new Promise((resolve) => {
      this.currentInputMode = "confirmation";
      this.currentInputCallback = resolve;

      // Show confirmation UI
      this.uiRenderer.showConfirmation(message, options, (choice) => {
        this.currentInputMode = null;
        this.currentInputCallback = null;
        resolve(choice === options[0]); // True if first option selected
      });
    });
  }

  // ===== INPUT HELPERS =====

  /**
   * Submit current text input
   */
  submitTextInput() {
    if (
      this.currentInputMode === "text" ||
      this.currentInputMode === "declaration"
    ) {
      // Trigger submit on the input component
      this.uiRenderer.submitCurrentInput();
    }
  }

  /**
   * Handle redeal keyboard shortcuts (Y/N)
   */
  handleRedealShortcut(choice) {
    if (this.currentInputMode === "redeal" && this.currentInputCallback) {
      const callback = this.currentInputCallback;
      this.currentInputMode = null;
      this.currentInputCallback = null;

      // Hide input UI
      this.uiRenderer.hideInput();

      console.log(`⌨️ Shortcut: ${choice}`);
      callback(choice);
    }
  }

  /**
   * Cancel current input
   */
  cancelCurrentInput() {
    if (this.currentInputCallback) {
      this.currentInputMode = null;
      const callback = this.currentInputCallback;
      this.currentInputCallback = null;

      // Hide any input UI
      this.uiRenderer.hideInput();

      // Resolve with null/empty
      callback(null);
    }
  }

  /**
   * Handle number key selection
   */
  handleNumberSelection(number) {
    if (this.currentInputMode === "selection") {
      // Notify the selection UI
      this.uiRenderer.selectByNumber(number);
    } else if (this.currentInputMode === "redeal") {
      // For redeal: 1=Yes, 2=No
      if (number === 1) {
        this.handleRedealShortcut("Yes");
      } else if (number === 2) {
        this.handleRedealShortcut("No");
      }
    } else if (this.currentInputMode === "declaration") {
      // For declaration: direct number input
      this.uiRenderer.selectByNumber(number);
    }
  }

  // ===== QUEUE MANAGEMENT =====

  /**
   * Queue an input for later processing
   */
  queueInput(input) {
    this.inputQueue.push({
      ...input,
      timestamp: Date.now(),
    });

    // Process queue if not busy
    this.processInputQueue();
  }

  /**
   * Process queued inputs
   */
  async processInputQueue() {
    if (this.inputQueue.length === 0) return;
    if (this.currentInputMode) return; // Busy with current input

    const input = this.inputQueue.shift();

    // Check if input is still valid (not too old)
    const age = Date.now() - input.timestamp;
    if (age > 5000) {
      // Discard old input
      return this.processInputQueue();
    }

    // Process the input
    await this.phaseManager.handleUserInput(input);

    // Continue processing queue
    this.processInputQueue();
  }

  // ===== STATE MANAGEMENT =====

  /**
   * Enable input handling
   */
  enable() {
    this.isEnabled = true;
    console.log("🎮 Input enabled");
  }

  /**
   * Disable input handling
   */
  disable() {
    this.isEnabled = false;
    this.cancelCurrentInput();
    console.log("🎮 Input disabled");
  }

  /**
   * Check if a key is currently pressed
   */
  isKeyPressed(key) {
    return this.keysPressed.has(key);
  }

  /**
   * Check if any modifier key is pressed
   */
  hasModifierKey() {
    return (
      this.isKeyPressed("Control") ||
      this.isKeyPressed("Shift") ||
      this.isKeyPressed("Alt")
    );
  }

  /**
   * Get current input mode
   */
  getCurrentInputMode() {
    return this.currentInputMode;
  }

  /**
   * Check if currently waiting for input
   */
  isWaitingForInput() {
    return this.currentInputMode !== null;
  }

  // ===== DEBUG =====

  /**
   * Show debug information
   */
  showDebugInfo() {
    console.log("🎮 Input Handler Debug Info:");
    console.log("- Enabled:", this.isEnabled);
    console.log("- Current Mode:", this.currentInputMode);
    console.log("- Keys Pressed:", Array.from(this.keysPressed));
    console.log("- Input Queue:", this.inputQueue.length);
    console.log("- Shortcuts:", Array.from(this.shortcuts.keys()));
    console.log("- Waiting for Input:", this.isWaitingForInput());
  }

  // ===== CLEANUP =====

  /**
   * Clean up event listeners
   */
  destroy() {
    window.removeEventListener("keydown", this.handleKeyDown);
    window.removeEventListener("keyup", this.handleKeyUp);

    this.shortcuts.clear();
    this.inputQueue = [];
    this.keysPressed.clear();

    console.log("🎮 Input handler destroyed");
  }
}
