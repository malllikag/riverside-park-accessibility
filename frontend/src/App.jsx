import React, { useState } from 'react';
import { Map } from './components/Map';
import { Sidebar } from './components/Sidebar';
import { SearchBox } from './components/SearchBox';
import { useAccessibilityData } from './hooks/useAccessibilityData';
import { Loader2, Menu, X, Info } from 'lucide-react';
import * as turf from '@turf/turf';

function App() {
  const { tracts, parks, neighborhoods, stats, loading, error } = useAccessibilityData();
  const [showTracts, setShowTracts] = useState(true);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [searchedLocation, setSearchedLocation] = useState(null);
  const [searchResult, setSearchResult] = useState(null);

  const handleLocationSelect = (loc) => {
    setSearchedLocation(loc);
    setIsSidebarOpen(false); // Close sidebar to show map result

    if (!tracts) return;

    // Point in Polygon check
    const point = turf.point([loc.lng, loc.lat]);
    let foundTract = null;

    for (const tract of tracts.features) {
      if (turf.booleanPointInPolygon(point, tract)) {
        foundTract = tract;
        break;
      }
    }

    if (foundTract) {
      setSearchResult({
        score: Math.round(foundTract.properties.accessibility_score),
        isWalkable: foundTract.properties.accessibility_score >= 50,
        address: loc.address
      });
    } else {
      setSearchResult({
        error: "Location is outside Riverside County analysis area.",
        address: loc.address
      });
    }
  };

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
      <div
        className={`sidebar-overlay ${isSidebarOpen ? 'open' : ''}`}
        onClick={() => setIsSidebarOpen(false)}
      />

      <SearchBox onLocationSelect={handleLocationSelect} />

      <Sidebar
        stats={stats}
        neighborhoods={neighborhoods}
        showTracts={showTracts}
        setShowTracts={setShowTracts}
        isOpen={isSidebarOpen}
        onClose={() => setIsSidebarOpen(false)}
      />

      <main style={{ flex: 1, position: 'relative', height: '100vh', width: '100%' }}>
        {/* Search Result Overlay */}
        {searchResult && (
          <div className="glass-panel" style={{
            position: 'absolute',
            top: '84px',
            left: '50%',
            transform: 'translateX(-50%)',
            zIndex: 1050,
            padding: '16px',
            borderRadius: '16px',
            width: 'min(90vw, 400px)',
            display: 'flex',
            alignItems: 'center',
            gap: '16px',
            animation: 'slideDown 0.3s ease-out'
          }}>
            <style>{`
              @keyframes slideDown { from { transform: translate(-50%, -20px); opacity: 0; } to { transform: translate(-50%, 0); opacity: 1; } }
            `}</style>

            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '10px',
              background: 'var(--accent-soft)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: 'var(--accent)',
              flexShrink: 0
            }}>
              <Info size={20} />
            </div>

            <div style={{ flex: 1, minWidth: 0 }}>
              <div style={{
                fontWeight: 600,
                fontSize: '0.875rem',
                marginBottom: '2px',
                whiteSpace: 'nowrap',
                overflow: 'hidden',
                textOverflow: 'ellipsis'
              }}>
                {searchResult.address.split(',')[0]}
              </div>
              <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                {searchResult.error ? searchResult.error : `Accessibility Score: ${searchResult.score}/100`}
              </div>
            </div>

            <button
              onClick={() => { setSearchResult(null); setSearchedLocation(null); }}
              style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px' }}
            >
              <X size={18} color="var(--text-muted)" />
            </button>
          </div>
        )}

        <Map
          tracts={tracts}
          parks={parks}
          neighborhoods={neighborhoods}
          showTracts={showTracts}
          searchedLocation={searchedLocation}
        />

        {/* Floating Legend */}
        <div className="glass-panel" style={{
          position: 'absolute',
          bottom: 'max(32px, env(safe-area-inset-bottom))',
          right: 'max(32px, env(safe-area-inset-right))',
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
