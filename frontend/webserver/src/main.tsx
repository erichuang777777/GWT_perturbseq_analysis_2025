import { StrictMode, useEffect, useState } from 'react'
import { createRoot } from 'react-dom/client'
import './index.css'
import App from './App.tsx'
import { loadDataset } from './data/dataset'
import { FullScreen, LoadingPulse, ErrorNotice } from './components/ui/ScreenState'

function Root() {
  const [status, setStatus] = useState<'loading' | 'ready' | 'error'>('loading')

  useEffect(() => {
    loadDataset()
      .then(() => setStatus('ready'))
      .catch(() => setStatus('error'))
  }, [])

  if (status === 'loading') {
    return (
      <FullScreen>
        <LoadingPulse label="Loading CD4 Target Discovery Portal…" />
      </FullScreen>
    )
  }

  if (status === 'error') {
    return (
      <FullScreen>
        <ErrorNotice title="Couldn't load the dataset" detail="real-dataset.json failed to fetch. Refresh to try again." />
      </FullScreen>
    )
  }

  return <App />
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <Root />
  </StrictMode>,
)
