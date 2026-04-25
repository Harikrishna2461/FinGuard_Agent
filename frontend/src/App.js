import React, { useEffect, useMemo, useState } from 'react';
import './App.css';

function App() {
  const [shellDoc, setShellDoc] = useState('');
  const [error, setError] = useState('');

  const apiBase = useMemo(() => {
    const configured = (process.env.REACT_APP_API_BASE_URL || '/api').trim();
    const normalized = configured.replace(/\/$/, '') || '/api';
    if (normalized === '/api' || normalized.endsWith('/api')) {
      return normalized;
    }
    return `${normalized}/api`;
  }, []);

  useEffect(() => {
    let active = true;

    async function loadShell() {
      try {
        const response = await fetch(
          `${process.env.PUBLIC_URL}/frontend-shell-template.html`
        );
        if (!response.ok) {
          throw new Error(`Failed to load UI template (${response.status})`);
        }

        const template = await response.text();
        const runtimeShell = template.replace(
          /const API = ['"]\/api['"];/,
          `const API = ${JSON.stringify(apiBase)};`
        );

        if (active) {
          setShellDoc(runtimeShell);
        }
      } catch (loadError) {
        if (active) {
          setError(loadError.message || 'Unable to load the frontend shell.');
        }
      }
    }

    loadShell();

    return () => {
      active = false;
    };
  }, [apiBase]);

  if (error) {
    return (
      <div className="shell-status shell-status-error">
        <h1>FinGuard frontend failed to start</h1>
        <p>{error}</p>
      </div>
    );
  }

  if (!shellDoc) {
    return (
      <div className="shell-status">
        <h1>Loading FinGuard</h1>
        <p>Preparing the analyst workspace inside the React app.</p>
      </div>
    );
  }

  return (
    <div className="shell-app">
      <iframe
        className="shell-frame"
        srcDoc={shellDoc}
        title="FinGuard frontend"
      />
    </div>
  );
}

export default App;
