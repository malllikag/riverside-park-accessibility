import React, { useState } from 'react';
import { Map } from './components/Map';
import { Sidebar } from './components/Sidebar';
import { useAccessibilityData } from './hooks/useAccessibilityData';
import { Loader2 } from 'lucide-react';

function App() {
  const { tracts, parks, neighborhoods, stats, loading, error } = useAccessibilityData();
  const [showTracts, setShowTracts] = useState(true);

  if (loading) {
    return (
      <div style={{
        height: '100vh',
        width: '100vw',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: '16px'
      }}>
        <Loader2 className="animate-spin" size={48} color="var(--accent)" />
        <p style={{ color: 'var(--text-secondary)', fontWeight: 500 }}>Loading Riverside Data...</p>
        <style>{`
                    @keyframes spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
                    .animate-spin { animation: spin 1s linear infinite; }
                `}</style>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ height: '100vh', width: '100vw', display: 'flex', alignItems: 'center', justifyContent: 'center', color: 'var(--danger)' }}>
        <p>Error: {error}</p>
      </div>
    );
  }

  return (
    <>
      <Sidebar
        stats={stats}
        neighborhoods={neighborhoods}
        showTracts={showTracts}
        setShowTracts={setShowTracts}
      />
      <main style={{ flex: 1, position: 'relative', height: '100vh' }}>
        <Map
          tracts={tracts}
          parks={parks}
          neighborhoods={neighborhoods}
          showTracts={showTracts}
        />

        {/* Floating Legend */}
        <div className="glass-panel" style={{
          position: 'absolute',
          bottom: '32px',
          right: '32px',
          padding: '16px',
          borderRadius: '12px',
          zIndex: 1000,
          pointerEvents: 'none'
        }}>
          <h3 style={{ fontSize: '0.75rem', fontWeight: 600, marginBottom: '12px' }}>Accessibility Score</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            {[
              { label: '0 - 20', color: '#ffffcc' },
              { label: '20 - 40', color: '#c2e699' },
              { label: '40 - 60', color: '#78c679' },
              { label: '60 - 80', color: '#31a354' },
              { label: '80 - 100', color: '#006837' }
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.75rem' }}>
                <div style={{ width: '12px', height: '12px', borderRadius: '2px', background: item.color }} />
                <span>{item.label}</span>
              </div>
            ))}
          </div>
        </div>
      </main>
    </>
  );
}

export default App;
