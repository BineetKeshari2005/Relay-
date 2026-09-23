"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import {
  VoiceState,
  VoiceTelemetry,
} from "./types";
import {
  WebSpeechRecognitionProvider,
  WebSpeechSynthesisProvider,
  VoiceRecognitionProvider,
  VoiceSynthesisProvider,
} from "./voiceProvider";

interface UseVoiceCopilotOptions {
  onTranscriptReady?: (transcript: string) => void;
  autoSpeakResponse?: boolean;
}

export function useVoiceCopilot(options: UseVoiceCopilotOptions = {}) {
  const [voiceState, setVoiceState] = useState<VoiceState>("idle");
  const [interimTranscript, setInterimTranscript] = useState<string>("");
  const [finalTranscript, setFinalTranscript] = useState<string>("");
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [telemetry, setTelemetry] = useState<VoiceTelemetry>({
    recording_duration_ms: 0,
    transcription_latency_ms: 0,
  });

  const recognitionRef = useRef<VoiceRecognitionProvider | null>(null);
  const synthesisRef = useRef<VoiceSynthesisProvider | null>(null);
  const recordingStartRef = useRef<number>(0);
  const latestTranscriptRef = useRef<string>("");

  useEffect(() => {
    recognitionRef.current = new WebSpeechRecognitionProvider();
    synthesisRef.current = new WebSpeechSynthesisProvider();

    return () => {
      recognitionRef.current?.stop();
      synthesisRef.current?.stop();
    };
  }, []);

  const isRecognitionSupported = useCallback(() => {
    return recognitionRef.current?.isSupported() ?? false;
  }, []);

  const isSynthesisSupported = useCallback(() => {
    return synthesisRef.current?.isSupported() ?? false;
  }, []);

  const startListening = useCallback(async () => {
    if (!recognitionRef.current) return;

    // If currently speaking, stop first
    synthesisRef.current?.stop();

    setErrorMessage(null);
    setInterimTranscript("");
    setFinalTranscript("");
    latestTranscriptRef.current = "";
    recordingStartRef.current = performance.now();
    setVoiceState("listening");

    await recognitionRef.current.start({
      onSpeechStart: () => {
        setVoiceState("listening");
      },
      onInterimTranscript: (text) => {
        setInterimTranscript(text);
      },
      onFinalTranscript: (text) => {
        latestTranscriptRef.current = text;
        setFinalTranscript(text);
        setInterimTranscript("");
      },
      onError: (err) => {
        setErrorMessage(err);
        setVoiceState("error");
      },
      onSpeechEnd: () => {
        const duration = Math.round(performance.now() - recordingStartRef.current);
        setTelemetry((prev) => ({
          ...prev,
          recording_duration_ms: duration,
        }));

        const resultText = latestTranscriptRef.current.trim();
        if (resultText) {
          setVoiceState("processing");
          if (options.onTranscriptReady) {
            options.onTranscriptReady(resultText);
          }
        } else {
          setVoiceState("idle");
        }
      },
      onStateChange: (state) => {
        setVoiceState(state);
      },
    });
  }, [options]);

  const stopListening = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
    }
  }, []);

  const speak = useCallback(
    (text: string, onEnd?: () => void) => {
      if (!synthesisRef.current || !text.trim()) return;

      const startTime = performance.now();
      setVoiceState("speaking");

      synthesisRef.current.speak(
        text,
        {
          onStart: () => {
            setVoiceState("speaking");
            const ttsLatency = Math.round(performance.now() - startTime);
            setTelemetry((prev) => ({ ...prev, tts_latency_ms: ttsLatency }));
          },
          onEnd: () => {
            setVoiceState("idle");
            onEnd?.();
          },
          onError: () => {
            setVoiceState("idle");
            onEnd?.();
          },
        },
        { rate: 1.05 }
      );
    },
    []
  );

  const stopSpeaking = useCallback(() => {
    if (synthesisRef.current) {
      synthesisRef.current.stop();
      setVoiceState("idle");
    }
  }, []);

  return {
    voiceState,
    setVoiceState,
    interimTranscript,
    finalTranscript,
    errorMessage,
    telemetry,
    isRecognitionSupported: isRecognitionSupported(),
    isSynthesisSupported: isSynthesisSupported(),
    startListening,
    stopListening,
    speak,
    stopSpeaking,
  };
}
