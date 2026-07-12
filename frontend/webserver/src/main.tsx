import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { loadDataset } from './data/dataset'
import { loadFigures } from './data/figuresData'

function Screen({ children }: { children: React.ReactNode }) {
  return (
    <div
      style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontFamily: "'IBM Plex Sans', system-ui, sans-serif",
        color: '#4a515e',
        fontSize: '14px',
      }}
    >
      {children}
    </div>
  )
}

function Root() {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    Promise.all([loadDataset(), loadFigures()])
      .then(() => setStatus('ready'))
      .catch(() => setStatus('error'))
  }, [])

  if (status === 'loading') {
    return (
      <Screen>
        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span
            style={{
              width: '8px',
              height: '8px',
              borderRadius: '50%',
              background: '#1a5fb4',
              animation: 'cd4-pulse 1s ease-in-out infinite',
            }}
          />
          Loading CD4 Target Discovery Portal…
        </div>
        <style>{`@keyframes cd4-pulse { 0%, 100% { opacity: .3; } 50% { opacity: 1; } }`}</style>
      </Screen>
    )
  }

  if (status === 'error') {
    return (
      <Screen>
        <div style={{ textAlign: 'center', maxWidth: '420px' }}>
          <div style={{ fontWeight: 600, color: '#8a2f2f', marginBottom: '6px' }}>
            Couldn't load the dataset
          </div>
          <div>real-dataset.json failed to fetch. Refresh to try again.</div>
        </div>
      </Screen>
    )
  }

  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
