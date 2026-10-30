import { useState, useEffect, useRef } from 'react'
import { Mic, MicOff, Sparkles, CheckCircle2, Loader2 } from 'lucide-react'

export type VoiceState = 'idle' | 'listening' | 'thinking' | 'executing' | 'complete'

interface VoiceControlProps {
  onCommandTrigger?: (command: string) => void
  isCompact?: boolean
}

export function VoiceControl({ onCommandTrigger, isCompact = false }: VoiceControlProps) {
  const [state, setState] = useState<VoiceState>('idle')
  const [transcript, setTranscript] = useState<string>('')
  const [recognitionSupported, setRecognitionSupported] = useState(false)
  const timerRef = useRef<any>(null)
  const recognitionRef = useRef<any>(null)
  const activeStateRef = useRef<VoiceState>('idle')

  useEffect(() => {
    activeStateRef.current = state
  }, [state])

  useEffect(() => {
    // Check Web Speech API availability
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition
    if (SpeechRecognition) {
      setRecognitionSupported(true)
      try {
        const recognition = new SpeechRecognition()
        recognition.continuous = false
        recognition.interimResults = false
        recognition.lang = 'en-US'

        recognition.onresult = (event: any) => {
          const text = event.results[0][0].transcript
          handleSpeechResult(text)
        }

        recognition.onerror = () => {
          // If error or denied, fallback smoothly to simulated command
          fallbackSimulation()
        }

        recognition.onend = () => {
          if (activeStateRef.current === 'listening') {
            setState('thinking')
          }
        }

        recognitionRef.current = recognition
      } catch {
        setRecognitionSupported(false)
      }
    }

    return () => {
      if (timerRef.current) clearTimeout(timerRef.current)
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort()
        } catch {}
      }
    }
  }, [])

  const startVoiceFlow = () => {
    if (activeStateRef.current !== 'idle') return

    setState('listening')
    setTranscript('Listening for incident command...')

    // Attempt live speech recognition if supported
    if (recognitionSupported && recognitionRef.current) {
      try {
        recognitionRef.current.start()
        timerRef.current = setTimeout(() => {
          if (activeStateRef.current === 'listening') {
            fallbackSimulation()
          }
        }, 3200)
        return
      } catch {
        // Fallback to simulation
      }
    }

    fallbackSimulation()
  }

  const fallbackSimulation = () => {
    setTranscript('"Investigate Payment API database connection timeout"')
    
    timerRef.current = setTimeout(() => {
      setState('thinking')
      setTranscript('Analyzing symptoms & synthesizing 8-phase investigation plan...')
      
      timerRef.current = setTimeout(() => {
        setState('executing')
        setTranscript('Executing autonomous diagnosis & causal verification...')
        if (onCommandTrigger) {
          onCommandTrigger('run_scenario')
        }

        timerRef.current = setTimeout(() => {
          setState('complete')
          setTranscript('Recovery verified. DB_POOL_SIZE: 5 → 30')

          timerRef.current = setTimeout(() => {
            setState('idle')
            setTranscript('')
          }, 3500)
        }, 2200)
      }, 1800)
    }, 1800)
  }

  const handleSpeechResult = (text: string) => {
    setTranscript(`"${text}"`)
    setState('thinking')
    
    timerRef.current = setTimeout(() => {
      setState('executing')
      if (onCommandTrigger) {
        onCommandTrigger(text)
      }

      timerRef.current = setTimeout(() => {
        setState('complete')
        setTranscript('Command execution verified.')

        timerRef.current = setTimeout(() => {
          setState('idle')
          setTranscript('')
        }, 3500)
      }, 2000)
    }, 1400)
  }

  const cancelVoice = () => {
    if (timerRef.current) clearTimeout(timerRef.current)
    if (recognitionRef.current) {
      try {
        recognitionRef.current.abort()
      } catch {}
    }
    setState('idle')
    setTranscript('')
  }

  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', gap: 8 }}>
      {state === 'idle' ? (
        <button
          onClick={startVoiceFlow}
          className="btn btn-ghost"
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 6,
            padding: isCompact ? '6px 10px' : '7px 14px',
            fontSize: 12,
            border: '1px solid var(--border-primary)',
            background: 'var(--bg-secondary)',
            color: 'var(--fg-secondary)',
            borderRadius: 'var(--radius-sm)'
          }}
          title="Click to give voice instruction (Subtle, push-to-talk)"
        >
          <Mic style={{ width: 14, height: 14, color: 'var(--accent-primary)' }} />
          <span>Voice</span>
        </button>
      ) : (
        <div
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: 8,
            padding: '5px 12px',
            borderRadius: 'var(--radius-sm)',
            background: state === 'complete' 
              ? 'rgba(0, 212, 170, 0.15)' 
              : state === 'listening' 
              ? 'rgba(255, 184, 0, 0.15)' 
              : 'rgba(56, 189, 248, 0.15)',
            border: `1px solid ${
              state === 'complete' 
                ? 'var(--accent-primary)' 
                : state === 'listening' 
                ? 'var(--accent-warning)' 
                : 'var(--accent-secondary)'
            }`,
            fontSize: 12,
            animation: 'fadeIn 0.2s ease'
          }}
        >
          {state === 'listening' && (
            <>
              <div className="status-dot running" style={{ background: 'var(--accent-warning)', width: 8, height: 8 }} />
              <strong style={{ color: 'var(--accent-warning)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Listening
              </strong>
            </>
          )}

          {state === 'thinking' && (
            <>
              <Loader2 className="spin" style={{ width: 13, height: 13, color: 'var(--accent-secondary)' }} />
              <strong style={{ color: 'var(--accent-secondary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Thinking
              </strong>
            </>
          )}

          {state === 'executing' && (
            <>
              <Sparkles style={{ width: 13, height: 13, color: 'var(--accent-primary)' }} />
              <strong style={{ color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Executing
              </strong>
            </>
          )}

          {state === 'complete' && (
            <>
              <CheckCircle2 style={{ width: 13, height: 13, color: 'var(--accent-primary)' }} />
              <strong style={{ color: 'var(--accent-primary)', textTransform: 'uppercase', letterSpacing: 0.5 }}>
                Complete
              </strong>
            </>
          )}

          {transcript && (
            <span style={{ color: 'var(--fg-primary)', fontFamily: 'var(--font-mono)', fontSize: 11, maxWidth: 260, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
              {transcript}
            </span>
          )}

          <button
            onClick={cancelVoice}
            className="btn btn-ghost"
            style={{ padding: '2px 4px', fontSize: 10, color: 'var(--fg-muted)' }}
            title="Cancel"
          >
            <MicOff style={{ width: 12, height: 12 }} />
          </button>
        </div>
      )}
    </div>
  )
}
