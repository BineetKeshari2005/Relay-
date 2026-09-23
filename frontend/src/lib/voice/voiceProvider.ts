/**
 * Voice provider abstractions and implementations for Relay Copilot.
 * Supports native Web Speech API and defines the LiveKit boundary interface.
 */

import {
  VoiceEventCallbacks,
  VoiceRecognitionConfig,
  VoiceSynthesisConfig,
} from "./types";

/**
 * Interface for speech-to-text recognition providers.
 */
export interface VoiceRecognitionProvider {
  isSupported(): boolean;
  start(callbacks: VoiceEventCallbacks, config?: VoiceRecognitionConfig): Promise<void>;
  stop(): void;
  abort(): void;
}

/**
 * Interface for text-to-speech synthesis providers.
 */
export interface VoiceSynthesisProvider {
  isSupported(): boolean;
  speak(
    text: string,
    callbacks?: { onStart?: () => void; onEnd?: () => void; onError?: (err: any) => void },
    config?: VoiceSynthesisConfig
  ): void;
  stop(): void;
  pause(): void;
  resume(): void;
  isSpeaking(): boolean;
}

/**
 * Architectural boundary for future LiveKit WebRTC agent streaming.
 * Provides the contract without blocking local execution or exposing secrets.
 */
export interface LiveKitVoiceBoundary {
  connect(roomToken: string, serverUrl: string): Promise<void>;
  disconnect(): Promise<void>;
  isConnected(): boolean;
  sendAudioTrack(stream: MediaStream): Promise<void>;
}

/**
 * Native Web Speech API speech-to-text implementation.
 */
export class WebSpeechRecognitionProvider implements VoiceRecognitionProvider {
  private recognition: any = null;
  private isListening: boolean = false;

  isSupported(): boolean {
    if (typeof window === "undefined") return false;
    return !!(
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition
    );
  }

  async start(
    callbacks: VoiceEventCallbacks,
    config: VoiceRecognitionConfig = {}
  ): Promise<void> {
    if (!this.isSupported()) {
      callbacks.onError?.("Speech recognition is not supported in this browser. Please use Google Chrome, Edge, or Safari.");
      return;
    }

    this.stop();

    const SpeechRecognitionClass =
      (window as any).SpeechRecognition ||
      (window as any).webkitSpeechRecognition;

    this.recognition = new SpeechRecognitionClass();
    this.recognition.continuous = config.continuous ?? false;
    this.recognition.interimResults = config.interimResults ?? true;
    this.recognition.lang = config.lang ?? "en-US";

    this.recognition.onstart = () => {
      this.isListening = true;
      callbacks.onSpeechStart?.();
      callbacks.onStateChange?.("listening");
    };

    this.recognition.onresult = (event: any) => {
      let interimTranscript = "";
      let finalTranscript = "";

      for (let i = event.resultIndex; i < event.results.length; ++i) {
        const result = event.results[i];
        const transcriptChunk = result[0].transcript;
        if (result.isFinal) {
          finalTranscript += transcriptChunk;
        } else {
          interimTranscript += transcriptChunk;
        }
      }

      if (interimTranscript) {
        callbacks.onInterimTranscript?.(interimTranscript);
      }
      if (finalTranscript) {
        callbacks.onFinalTranscript?.(finalTranscript);
      }
    };

    this.recognition.onerror = (event: any) => {
      let msg = "Microphone error";
      if (event.error === "not-allowed") {
        msg = "Microphone access denied. Please allow microphone permissions in browser settings.";
      } else if (event.error === "no-speech") {
        msg = "No speech detected. Please speak closer to the microphone.";
      } else if (event.error === "network") {
        msg = "Network error during speech recognition.";
      } else {
        msg = `Speech error: ${event.error}`;
      }
      callbacks.onError?.(msg);
      callbacks.onStateChange?.("error");
    };

    this.recognition.onend = () => {
      this.isListening = false;
      callbacks.onSpeechEnd?.();
    };

    try {
      this.recognition.start();
    } catch (e: any) {
      callbacks.onError?.(e.message || "Failed to initialize microphone.");
      callbacks.onStateChange?.("error");
    }
  }

  stop(): void {
    if (this.recognition && this.isListening) {
      try {
        this.recognition.stop();
      } catch {
        // Ignore if already stopped
      }
      this.isListening = false;
    }
  }

  abort(): void {
    if (this.recognition) {
      try {
        this.recognition.abort();
      } catch {
        // Ignore
      }
      this.isListening = false;
    }
  }
}

/**
 * Native Web Speech API speech synthesis implementation.
 */
export class WebSpeechSynthesisProvider implements VoiceSynthesisProvider {
  isSupported(): boolean {
    if (typeof window === "undefined") return false;
    return !!window.speechSynthesis;
  }

  speak(
    text: string,
    callbacks?: { onStart?: () => void; onEnd?: () => void; onError?: (err: any) => void },
    config: VoiceSynthesisConfig = {}
  ): void {
    if (!this.isSupported() || !text.trim()) {
      callbacks?.onEnd?.();
      return;
    }

    // Cancel any ongoing speech before starting new utterance
    window.speechSynthesis.cancel();

    const utterance = new SpeechSynthesisUtterance(text.trim());
    utterance.rate = config.rate ?? 1.05; // Slightly brisk for efficient technician guidance
    utterance.pitch = config.pitch ?? 1.0;
    utterance.volume = config.volume ?? 1.0;
    utterance.lang = config.lang ?? "en-US";

    utterance.onstart = () => {
      callbacks?.onStart?.();
    };

    utterance.onend = () => {
      callbacks?.onEnd?.();
    };

    utterance.onerror = (e) => {
      // Ignore user interrupt cancellations
      if (e.error !== "canceled" && e.error !== "interrupted") {
        callbacks?.onError?.(e);
      } else {
        callbacks?.onEnd?.();
      }
    };

    window.speechSynthesis.speak(utterance);
  }

  stop(): void {
    if (this.isSupported()) {
      window.speechSynthesis.cancel();
    }
  }

  pause(): void {
    if (this.isSupported()) {
      window.speechSynthesis.pause();
    }
  }

  resume(): void {
    if (this.isSupported()) {
      window.speechSynthesis.resume();
    }
  }

  isSpeaking(): boolean {
    if (!this.isSupported()) return false;
    return window.speechSynthesis.speaking;
  }
}
