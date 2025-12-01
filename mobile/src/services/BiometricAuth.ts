/**
 * Biometric Authentication Service
 * Provides Face ID / Touch ID / Fingerprint authentication
 */
import ReactNativeBiometrics, { BiometryTypes } from 'react-native-biometrics';
import * as Keychain from 'react-native-keychain';
import { Platform } from 'react-native';

export interface BiometricCapabilities {
  available: boolean;
  biometryType: BiometryTypes | null;
  error?: string;
}

export interface AuthResult {
  success: boolean;
  error?: string;
}

class BiometricAuthService {
  private rnBiometrics: ReactNativeBiometrics;

  constructor() {
    this.rnBiometrics = new ReactNativeBiometrics({
      allowDeviceCredentials: true, // Allow PIN/password fallback
    });
  }

  /**
   * Check if biometric authentication is available
   */
  async isBiometricAvailable(): Promise<BiometricCapabilities> {
    try {
      const { available, biometryType } = await this.rnBiometrics.isSensorAvailable();
      
      return {
        available,
        biometryType: biometryType as BiometryTypes | null,
      };
    } catch (error) {
      return {
        available: false,
        biometryType: null,
        error: error instanceof Error ? error.message : 'Unknown error',
      };
    }
  }

  /**
   * Get user-friendly name for biometric type
   */
  getBiometricTypeName(type: BiometryTypes | null): string {
    switch (type) {
      case BiometryTypes.FaceID:
        return 'Face ID';
      case BiometryTypes.TouchID:
        return 'Touch ID';
      case BiometryTypes.Biometrics:
        return Platform.OS === 'android' ? 'Fingerprint' : 'Biometrics';
      default:
        return 'Biometric Authentication';
    }
  }

  /**
   * Authenticate user with biometrics
   */
  async authenticate(promptMessage?: string): Promise<AuthResult> {
    try {
      const { available } = await this.isBiometricAvailable();
      
      if (!available) {
        return {
          success: false,
          error: 'Biometric authentication not available',
        };
      }

      const { success } = await this.rnBiometrics.simplePrompt({
        promptMessage: promptMessage || 'Authenticate to access CryptoOrchestrator',
        cancelButtonText: 'Cancel',
      });

      return { success };
    } catch (error) {
      return {
        success: false,
        error: error instanceof Error ? error.message : 'Authentication failed',
      };
    }
  }

  /**
   * Store API credentials securely with biometric protection
   */
  async storeCredentials(
    apiKey: string,
    apiSecret: string,
    exchange: string
  ): Promise<boolean> {
    try {
      const service = `crypto_orchestrator_${exchange}`;
      
      await Keychain.setGenericPassword(
        apiKey,
        apiSecret,
        {
          service,
          accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
          accessControl: Keychain.ACCESS_CONTROL.BIOMETRY_CURRENT_SET,
          authenticationType: Keychain.AUTHENTICATION_TYPE.BIOMETRICS,
        }
      );

      return true;
    } catch (error) {
      console.error('Failed to store credentials:', error);
      return false;
    }
  }

  /**
   * Retrieve API credentials with biometric authentication
   */
  async getCredentials(exchange: string): Promise<{
    username: string;
    password: string;
  } | null> {
    try {
      const service = `crypto_orchestrator_${exchange}`;
      
      const credentials = await Keychain.getGenericPassword({
        service,
        authenticationPrompt: {
          title: 'Authenticate',
          subtitle: 'Access your exchange credentials',
          description: 'Use biometrics to unlock',
          cancel: 'Cancel',
        },
      });

      if (credentials) {
        return {
          username: credentials.username,
          password: credentials.password,
        };
      }

      return null;
    } catch (error) {
      console.error('Failed to retrieve credentials:', error);
      return null;
    }
  }

  /**
   * Delete stored credentials
   */
  async deleteCredentials(exchange: string): Promise<boolean> {
    try {
      const service = `crypto_orchestrator_${exchange}`;
      await Keychain.resetGenericPassword({ service });
      return true;
    } catch (error) {
      console.error('Failed to delete credentials:', error);
      return false;
    }
  }

  /**
   * Enable biometric authentication for the app
   */
  async enableBiometricAuth(): Promise<boolean> {
    try {
      const { publicKey } = await this.rnBiometrics.createKeys();
      
      // Store flag indicating biometric auth is enabled
      await Keychain.setGenericPassword(
        'biometric_enabled',
        'true',
        {
          service: 'crypto_orchestrator_settings',
          accessible: Keychain.ACCESSIBLE.WHEN_UNLOCKED_THIS_DEVICE_ONLY,
        }
      );

      return true;
    } catch (error) {
      console.error('Failed to enable biometric auth:', error);
      return false;
    }
  }

  /**
   * Disable biometric authentication
   */
  async disableBiometricAuth(): Promise<boolean> {
    try {
      await this.rnBiometrics.deleteKeys();
      await Keychain.resetGenericPassword({ service: 'crypto_orchestrator_settings' });
      return true;
    } catch (error) {
      console.error('Failed to disable biometric auth:', error);
      return false;
    }
  }

  /**
   * Check if biometric auth is enabled
   */
  async isBiometricAuthEnabled(): Promise<boolean> {
    try {
      const credentials = await Keychain.getGenericPassword({
        service: 'crypto_orchestrator_settings',
      });
      return credentials && credentials.username === 'biometric_enabled';
    } catch {
      return false;
    }
  }

  /**
   * Create biometric signature for API requests
   */
  async createSignature(payload: string): Promise<string | null> {
    try {
      const { success, signature } = await this.rnBiometrics.createSignature({
        promptMessage: 'Authenticate to sign request',
        payload,
      });

      return success && signature ? signature : null;
    } catch (error) {
      console.error('Failed to create signature:', error);
      return null;
    }
  }
}

export const biometricAuth = new BiometricAuthService();
export default biometricAuth;
