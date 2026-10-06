import {useCallback, useEffect, useRef, useState} from 'react';
import './voice.css';

type RecognitionResult = {isFinal: boolean; 0: {transcript: string}};
type RecognitionEvent = {resultIndex: number; results: ArrayLike<RecognitionResult>};
type RecognitionError = {error: string};
type BrowserRecognition = {
  lang: string;
  continuous: boolean;
  interimResults: boolean;
  maxAlternatives: number;
  onresult: ((event: RecognitionEvent) => void) | null;
  onerror: ((event: RecognitionError) => void) | null;
  onend: (() => void) | null;
  start: () => void;
  stop: () => void;
  abort: () => void;
};
type RecognitionConstructor = new () => BrowserRecognition;

declare global {
  interface Window {
    SpeechRecognition?: RecognitionConstructor;
    webkitSpeechRecognition?: RecognitionConstructor;
  }
}

export type VoicePhase = 'idle' | 'listening' | 'processing' | 'preparing' | 'speaking' | 'error';
export type SpokenReply = {id: string; text: string};
export type VoiceControlsProps = {
  /** Send a final transcript to the existing chat flow, or put it in the composer. */
  onTranscript: (text: string) => void | Promise<void>;
  /** The newest completed assistant message; never pass a streaming partial. */
  latestReply?: SpokenReply | null;
  /** Used to avoid auto-reading an old reply when switching conversations. */
  conversationId?: string | null;
  /** Disables recording and transcript delivery while a chat submission is pending. */
  disabled?: boolean;
  language?: string;
  className?: string;
  onVoiceStateChange?: (phase: VoicePhase) => void;
};

function recognitionError(code: string): string {
  switch (code) {
    case 'not-allowed':
    case 'service-not-allowed':
      return 'Microphone permission was denied. Allow microphone access for FRIDAY in your browser.';
    case 'audio-capture':
      return 'No microphone is available. Check your input device and try again.';
    case 'no-speech':
      return 'No speech was detected. Try again when you are ready.';
    case 'network':
      return 'Browser speech recognition could not connect. Check your connection and try again.';
    default:
      return 'Voice recognition stopped. Please try again or type your message.';
  }
}

function readableText(markdown: string): string {
  return markdown
    .replace(/```[\s\S]*?```/g, ' Code block omitted from spoken reply. ')
    .replace(/!\[([^\]]*)\]\([^)]*\)/g, '$1')
    .replace(/\[([^\]]+)\]\([^)]*\)/g, '$1')
    .replace(/(^|\n)\s{0,3}#{1,6}\s+/g, '$1')
    .replace(/[>*_`]/g, '')
    .replace(/\s+/g, ' ')
    .trim();
}

/** Browser voice only: no FRIDAY microphone recording or external voice API. */
export function VoiceControls({
  onTranscript,
  latestReply,
  conversationId,
  disabled = false,
  language = 'en-IN',
  className = '',
  onVoiceStateChange,
}: VoiceControlsProps) {
  const [phase, setPhase] = useState<VoicePhase>('idle');
  const [error, setError] = useState('');
  const [preview, setPreview] = useState('');
  const [autoRead, setAutoRead] = useState(false);
  const [microphoneEpoch, setMicrophoneEpoch] = useState(0);
  const recognitionRef = useRef<BrowserRecognition | null>(null);
  const utteranceRef = useRef<SpeechSynthesisUtterance | null>(null);
  const latestReplyRef = useRef<SpokenReply | null>(latestReply ?? null);
  const previousConversationRef = useRef(conversationId);
  const previousDisabledRef = useRef(disabled);
  const previousAutoReadRef = useRef(false);
  const suppressPendingUntilIdleRef = useRef(false);
  const awaitingReplyRef = useRef<{conversationId: string | null | undefined; previousReplyId: string | null} | null>(null);
  const disabledRef = useRef(disabled);
  const onTranscriptRef = useRef(onTranscript);
  const onVoiceStateChangeRef = useRef(onVoiceStateChange);

  const canListen = typeof window !== 'undefined' && !!(window.SpeechRecognition || window.webkitSpeechRecognition);
  const canSpeak = typeof window !== 'undefined' && 'speechSynthesis' in window && typeof SpeechSynthesisUtterance !== 'undefined';

  useEffect(() => {onTranscriptRef.current = onTranscript;}, [onTranscript]);
  useEffect(() => {onVoiceStateChangeRef.current = onVoiceStateChange;}, [onVoiceStateChange]);
  useEffect(() => {onVoiceStateChangeRef.current?.(phase);}, [phase]);
  useEffect(() => {latestReplyRef.current = latestReply ?? null;}, [latestReply]);
  useEffect(() => {disabledRef.current = disabled;}, [disabled]);

  const stopSpeaking = useCallback(() => {
    utteranceRef.current = null;
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
    setPhase(current => current === 'speaking' || current === 'preparing' ? 'idle' : current);
  }, []);

  const speak = useCallback((value: string) => {
    if (recognitionRef.current) return; // Never play a reply into an active microphone.
    if (!canSpeak) {
      setError('Spoken replies are unavailable in this browser. The text response remains available.');
      setPhase('error');
      return;
    }
    const text = readableText(value);
    if (!text) return;
    window.speechSynthesis.cancel();
    const utterance = new SpeechSynthesisUtterance(text);
    utterance.lang = language;
    utterance.rate = 0.96;
    const voices = window.speechSynthesis.getVoices();
    const preferred = voices.find(voice => voice.lang.toLowerCase() === language.toLowerCase())
      ?? voices.find(voice => voice.lang.toLowerCase().startsWith('en-'));
    if (preferred) utterance.voice = preferred;
    utterance.onstart = () => {if (utteranceRef.current === utterance) setPhase('speaking');};
    utterance.onend = () => {if (utteranceRef.current === utterance) {utteranceRef.current = null; setPhase('idle');}};
    utterance.onerror = () => {
      if (utteranceRef.current === utterance) {
        utteranceRef.current = null;
        setError('This browser could not play the reply. You can still read it in the chat.');
        setPhase('error');
      }
    };
    utteranceRef.current = utterance;
    setError('');
    setPhase('preparing');
    try { window.speechSynthesis.speak(utterance); }
    catch {
      utteranceRef.current = null;
      setError('This browser could not play the reply. You can still read it in the chat.');
      setPhase('error');
    }
  }, [canSpeak, language]);

  // Reading requires a request observed in this conversation. Loading an existing
  // conversation may add an old reply, and must never start speech by itself.
  useEffect(() => {
    let newConversationCreatedDuringRequest = false;
    if (previousConversationRef.current !== conversationId) {
      const previousConversationId = previousConversationRef.current;
      newConversationCreatedDuringRequest = previousConversationId == null && conversationId != null && disabled;
      previousConversationRef.current = conversationId;
      awaitingReplyRef.current = null;
      stopSpeaking();
      // A request that belongs to the previous conversation must not send its
      // late transcript into the newly selected conversation.
      const recognition = recognitionRef.current;
      if (recognition) {
        recognitionRef.current = null;
        recognition.onresult = null;
        recognition.onerror = null;
        recognition.onend = null;
        recognition.abort();
        setMicrophoneEpoch(value => value + 1);
        setPreview('');
        setPhase('idle');
      }
      // Switching between existing chats while another request is busy should
      // not arm auto-read until a new request starts in the selected chat.
      suppressPendingUntilIdleRef.current = previousConversationId != null && conversationId != null && disabled;
    }
    if (!disabled) suppressPendingUntilIdleRef.current = false;
    if (!autoRead) awaitingReplyRef.current = null;
    else if (disabled && !suppressPendingUntilIdleRef.current && (newConversationCreatedDuringRequest || !previousDisabledRef.current || !previousAutoReadRef.current)) {
      awaitingReplyRef.current = {conversationId, previousReplyId: latestReply?.id ?? null};
    }
    previousDisabledRef.current = disabled;
    previousAutoReadRef.current = autoRead;
  }, [autoRead, conversationId, disabled, latestReply?.id, stopSpeaking]);

  useEffect(() => {
    const awaiting = awaitingReplyRef.current;
    if (!autoRead || !awaiting || awaiting.conversationId !== conversationId || !latestReply?.id) return;
    if (latestReply.id === awaiting.previousReplyId || recognitionRef.current) return;
    awaitingReplyRef.current = null;
    speak(latestReply.text);
  }, [autoRead, conversationId, latestReply, microphoneEpoch, speak]);

  const stopListening = useCallback(() => {
    if (!recognitionRef.current) return;
    setPhase('processing');
    try {recognitionRef.current.stop();}
    catch {recognitionRef.current = null; setPhase('idle');}
  }, []);

  const cancelListening = useCallback(() => {
    const recognition = recognitionRef.current;
    if (!recognition) return;
    recognitionRef.current = null;
    recognition.onresult = null;
    recognition.onerror = null;
    recognition.onend = null;
    recognition.abort();
    setMicrophoneEpoch(value => value + 1);
    setPreview('');
    setError('');
    setPhase('idle');
  }, []);

  const startListening = useCallback(() => {
    if (!canListen || disabled || recognitionRef.current) return;
    const Constructor = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!Constructor) return;
    stopSpeaking(); // Prevent FRIDAY's output from entering the microphone.
    const recognition = new Constructor();
    recognitionRef.current = recognition;
    recognition.lang = language;
    recognition.continuous = false;
    recognition.interimResults = true;
    recognition.maxAlternatives = 1;
    let delivered = false;
    let failed = false;
    recognition.onresult = event => {
      let interim = '';
      let final = '';
      for (let i = event.resultIndex; i < event.results.length; i += 1) {
        const result = event.results[i];
        if (result.isFinal) final += result[0].transcript;
        else interim += result[0].transcript;
      }
      setPreview((final || interim).trim());
      if (!final.trim() || delivered) return;
      delivered = true;
      if (disabledRef.current) {
        setError('A request is already running. Please try dictating again after it finishes.');
        setPhase('error');
        try {recognition.stop();} catch {recognitionRef.current = null; setMicrophoneEpoch(value => value + 1);}
        return;
      }
      setPhase('processing');
      try {recognition.stop();} catch {recognitionRef.current = null; setMicrophoneEpoch(value => value + 1);}
      Promise.resolve()
        .then(() => onTranscriptRef.current(final.trim()))
        .catch(() => {setError('The voice message could not be sent. Check your connection or use the text composer.'); setPhase('error');})
        .finally(() => {setPhase(current => current === 'processing' ? 'idle' : current);});
    };
    recognition.onerror = event => {
      if (event.error === 'aborted' || delivered) return;
      failed = true;
      setError(recognitionError(event.error));
      setPhase('error');
    };
    recognition.onend = () => {
      if (recognitionRef.current === recognition) {
        recognitionRef.current = null;
        setMicrophoneEpoch(value => value + 1);
      }
      if (!delivered && !failed) {
        setError('No speech was captured. Try again when you are ready.');
        setPhase('error');
      }
    };
    setPreview('');
    setError('');
    try {
      recognition.start(); // The browser requests microphone permission here.
      setPhase('listening');
    } catch {
      recognitionRef.current = null;
      setError('The microphone could not start. Check browser permissions and try again.');
      setPhase('error');
    }
  }, [canListen, disabled, language, stopSpeaking]);

  useEffect(() => () => {
    const recognition = recognitionRef.current;
    recognitionRef.current = null;
    if (recognition) {
      recognition.onresult = null;
      recognition.onerror = null;
      recognition.onend = null;
      recognition.abort();
    }
    if (utteranceRef.current && typeof window !== 'undefined' && 'speechSynthesis' in window) window.speechSynthesis.cancel();
    utteranceRef.current = null;
  }, []);

  const status = phase === 'listening' ? 'Listening… speak now.'
    : phase === 'processing' ? 'Sending your voice message…'
      : phase === 'preparing' ? 'Preparing spoken reply…'
        : phase === 'speaking' ? 'FRIDAY is speaking.'
        : !canListen && !canSpeak ? 'Voice is unavailable in this browser.'
          : !canListen ? 'Speech input is unavailable in this browser. You can still hear replies or type.'
            : !canSpeak ? 'Spoken replies are unavailable in this browser. You can still dictate or type.'
              : 'Voice is ready when you are.';

  return <section className={`friday-voice ${className}`} aria-label="FRIDAY voice controls" data-voice-phase={phase}>
    <div className="friday-voice-actions">
      <button type="button" className={phase === 'listening' ? 'voice-button active' : 'voice-button'}
        onClick={phase === 'listening' ? stopListening : startListening}
        disabled={!canListen || (disabled && phase !== 'listening') || phase === 'processing'}
        aria-label={phase === 'listening' ? 'Finish speaking to FRIDAY' : 'Talk to FRIDAY'}
        aria-pressed={phase === 'listening'}>
        <span aria-hidden="true">{phase === 'listening' ? '■' : '◉'}</span> {phase === 'listening' ? 'Finish speaking' : 'Talk to FRIDAY'}
      </button>
      {phase === 'listening' && <button type="button" className="voice-button" onClick={cancelListening} aria-label="Cancel voice recording">Cancel</button>}
      {phase === 'speaking' || phase === 'preparing' ?
        <button type="button" className="voice-button" onClick={stopSpeaking} aria-label="Stop FRIDAY speaking">■ Stop voice</button> :
        <button type="button" className="voice-button" onClick={() => speak(latestReplyRef.current?.text ?? 'Hello. This is a voice test. I am ready to listen.')}
          disabled={!canSpeak || phase === 'listening' || phase === 'processing'} aria-label={latestReply?.text ? "Read FRIDAY's latest reply aloud" : 'Test FRIDAY voice playback'}>◖)) {latestReply?.text ? 'Hear reply' : 'Test voice'}</button>}
      {canSpeak && <label className="voice-autoread"><input type="checkbox" checked={autoRead} onChange={event => setAutoRead(event.target.checked)}/> Speak new replies</label>}
    </div>
    <p className="voice-status" role="status">{error || status}{phase === 'listening' && preview ? ` ${preview}` : ''}</p>
    <p className="voice-privacy">Your browser may process microphone audio. FRIDAY saves only the text you send.</p>
  </section>;
}
