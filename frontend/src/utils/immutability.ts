/**
 * Deep freeze utility for ensuring immutability
 */
export function deepFreeze<T>(obj: T): Readonly<T> {
  // Primitive types and null/undefined are already immutable
  if (obj === null || obj === undefined || typeof obj !== 'object') {
    return obj;
  }

  // Handle arrays
  if (Array.isArray(obj)) {
    return Object.freeze(obj.map(item => deepFreeze(item))) as Readonly<T>;
  }

  // Handle objects
  const frozen: any = {};
  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      frozen[key] = deepFreeze(obj[key]);
    }
  }

  return Object.freeze(frozen) as Readonly<T>;
}

/**
 * Create an immutable update of an object
 */
export function updateImmutable<T extends object>(
  original: T,
  updates: Partial<T>
): Readonly<T> {
  return deepFreeze({ ...original, ...updates });
}

/**
 * Type guard to check if value is frozen
 */
export function isFrozen(obj: any): boolean {
  if (obj === null || obj === undefined || typeof obj !== 'object') {
    return true;
  }

  if (!Object.isFrozen(obj)) {
    return false;
  }

  if (Array.isArray(obj)) {
    return obj.every(item => isFrozen(item));
  }

  for (const key in obj) {
    if (Object.prototype.hasOwnProperty.call(obj, key)) {
      if (!isFrozen(obj[key])) {
        return false;
      }
    }
  }

  return true;
}
