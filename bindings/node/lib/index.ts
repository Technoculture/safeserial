
/**
 * Data Bridge - Guaranteed Reliable Serial Communication
 * 
 * TypeScript wrapper for the native Node-API addon.
 * Provides a clean, async-friendly API for Electron applications.
 */

import { ReliableDataBridge, DataBridgeOptions } from './reliable';
import { SerialPort } from './native';

// Export the Reliable implementation as the default DataBridge
export { ReliableDataBridge as DataBridge };
export { DataBridgeOptions };

// Export Raw SerialPort for advanced users
export { SerialPort as RawSerialPort };

// Export Resilient wrapper (connection resilience)
// Note: ResilientDataBridge wraps DataBridge. 
// If DataBridge is now Reliable, ResilientDataBridge will hold a ReliableDataBridge.
// This gives us Connection Resilience + Data Reliability.
export { ResilientDataBridge, ResilientOptions, ResilientEvents } from './resilient';
