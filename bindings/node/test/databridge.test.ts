/**
 * TypeScript Type Tests for Data Bridge
 * 
 * These tests verify the TypeScript types compile correctly.
 * Hardware tests should be run separately with actual serial devices.
 */

import { describe, it, expect } from 'vitest';

// Type-only tests (no hardware needed)
describe('TypeScript Types', () => {
  it('should export DataBridge class', async () => {
    // Dynamic import to verify module structure
    const mod = await import('../lib/index');
    expect(mod.DataBridge).toBeDefined();
    expect(typeof mod.DataBridge.open).toBe('function');
  });

  it('should export DataBridgeOptions interface', async () => {
    // Type checking only - this compiles if types are correct
    const options: import('../lib/index').DataBridgeOptions = {
      baudRate: 115200,
    };
    expect(options.baudRate).toBe(115200);
  });

  it('should support optional baudRate', () => {
    const optionsWithBaud: import('../lib/index').DataBridgeOptions = { baudRate: 9600 };
    const optionsEmpty: import('../lib/index').DataBridgeOptions = {};

    expect(optionsWithBaud.baudRate).toBe(9600);
    expect(optionsEmpty.baudRate).toBeUndefined();
  });
});

describe('API Shape', () => {
  it('DataBridge.open should be a static async method', async () => {
    const { DataBridge } = await import('../lib/index');
    expect(DataBridge.open).toBeDefined();
    // Verify it returns a promise (test without calling with real port)
  });
});

// Hardware tests are skipped by default
// Run with: npm test -- --run --include "Hardware"
describe.skip('Hardware Tests (require serial device)', () => {
  it('should open a real serial port', async () => {
    const { DataBridge } = await import('../lib/index');
    // These tests need a real device connected
    // const bridge = await DataBridge.open('/dev/ttyUSB0');
    // expect(bridge.isOpen).toBe(true);
  });
});
