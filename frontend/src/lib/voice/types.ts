/**
 * Voice domain types and state definitions for Relay Copilot.
 */

export type VoiceState = "idle" | "listening" | "processing" | "speaking" | "error";

export interface VoiceTelemetry {
  recording_duration_ms: number;
  transcription_latency_ms: number;
  tts_latency_ms?: number;
}

export interface VoiceRecognitionConfig {
  continuous?: boolean;
  interimResults?: boolean;
  lang?: string;
}

export interface VoiceSynthesisConfig {
  rate?: number;
  pitch?: number;
  volume?: number;
  lang?: string;
}

export interface VoiceEventCallbacks {
  onInterimTranscript?: (transcript: string) => void;
  onFinalTranscript?: (transcript: string) => void;
  onStateChange?: (state: VoiceState) => void;
  onError?: (errorMessage: string) => void;
  onSpeechStart?: () => void;
  onSpeechEnd?: () => void;
}
