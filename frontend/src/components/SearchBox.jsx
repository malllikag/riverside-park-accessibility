import React, { useState, useEffect, useRef } from 'react';
import { Search as SearchIcon, MapPin, X, Loader2 } from 'lucide-react';

export function SearchBox({ onLocationSelect }) {
    const [query, setQuery] = useState('');
    const [suggestions, setSuggestions] = useState([]);
    const [loading, setLoading] = useState(false);
    const [showSuggestions, setShowSuggestions] = useState(false);
    const containerRef = useRef(null);

    // Close suggestions when clicking outside
    useEffect(() => {
        function handleClickOutside(event) {
            if (containerRef.current && !containerRef.current.contains(event.target)) {
                setShowSuggestions(false);
            }
        }
        document.addEventListener('mousedown', handleClickOutside);
        return () => document.removeEventListener('mousedown', handleClickOutside);
    }, []);

    // Debounced search
    useEffect(() => {
        const timeoutId = setTimeout(() => {
            if (query.length > 3) {
                fetchSuggestions(query);
            } else {
                setSuggestions([]);
            }
        }, 500);
        return () => clearTimeout(timeoutId);
    }, [query]);

    async function fetchSuggestions(searchText) {
        setLoading(true);
        try {
            // Constrain search to Riverside County area for better accuracy
            const url = `https://nominatim.openstreetmap.org/search?format=json&q=${encodeURIComponent(searchText)}&bounded=1&viewbox=-117.7,34.1,-116.5,33.4&countrycodes=us&addressdetails=1&limit=5`;
            const response = await fetch(url, {
                headers: {
                    'Accept-Language': 'en-US,en;q=0.5'
                }
            });
            const data = await response.json();
            setSuggestions(data);
            setShowSuggestions(true);
        } catch (err) {
            console.error('Geocoding error:', err);
        } finally {
            setLoading(false);
        }
    }

    const handleSelect = (item) => {
        setQuery(item.display_name);
        setShowSuggestions(false);
        onLocationSelect({
            lat: parseFloat(item.lat),
            lng: parseFloat(item.lon),
            address: item.display_name
        });
    };

    return (
        <div
            ref={containerRef}
            className="glass-panel"
            style={{
                position: 'fixed',
                top: '16px',
                left: '50%',
                transform: 'translateX(-50%)',
                zIndex: 1100,
                width: 'min(90vw, 500px)',
                borderRadius: '16px',
                padding: '8px',
                boxShadow: 'var(--shadow-lg)',
                display: 'flex',
                flexDirection: 'column',
                gap: '8px'
            }}
        >
            <div style={{ display: 'flex', alignItems: 'center', gap: '12px', padding: '4px 12px' }}>
                <SearchIcon size={20} color="var(--text-muted)" />
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Enter an address (e.g. 5160 Monte Vista Dr)..."
                    style={{
                        flex: 1,
                        background: 'transparent',
                        border: 'none',
                        outline: 'none',
                        color: 'var(--text-primary)',
                        fontSize: '0.925rem',
                        height: '40px'
                    }}
                    onFocus={() => query.length > 3 && setShowSuggestions(true)}
                />
                {query && (
                    <button
                        onClick={() => { setQuery(''); setSuggestions([]); }}
                        style={{ background: 'transparent', border: 'none', cursor: 'pointer', padding: '4px' }}
                    >
                        <X size={18} color="var(--text-muted)" />
                    </button>
                )}
                {loading && <Loader2 size={18} className="animate-spin" color="var(--accent)" />}
            </div>

            {showSuggestions && suggestions.length > 0 && (
                <div style={{
                    borderTop: '1px solid var(--glass-border)',
                    maxHeight: '300px',
                    overflowY: 'auto',
                    padding: '8px 0'
                }}>
                    {suggestions.map((item, idx) => (
                        <div
                            key={item.place_id || idx}
                            onClick={() => handleSelect(item)}
                            style={{
                                padding: '12px 16px',
                                cursor: 'pointer',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '12px',
                                transition: 'background 0.2s',
                                borderRadius: '8px',
                                margin: '0 8px'
                            }}
                            className="suggestion-item"
                        >
                            <MapPin size={16} color="var(--accent)" style={{ flexShrink: 0 }} />
                            <div style={{
                                fontSize: '0.875rem',
                                whiteSpace: 'nowrap',
                                overflow: 'hidden',
                                textOverflow: 'ellipsis',
                                color: 'var(--text-secondary)'
                            }}>
                                {item.display_name}
                            </div>
                        </div>
                    ))}
                    <style>{`
                        .suggestion-item:hover {
                            background: var(--accent-soft);
                        }
                    `}</style>
                </div>
            )}
        </div>
    );
}
