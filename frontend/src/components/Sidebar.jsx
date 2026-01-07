import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Map as MapIcon, Info, AlertTriangle, Database } from 'lucide-react';

export function Sidebar({ stats, neighborhoods, showTracts, setShowTracts }) {
    // Prepare chart data from neighborhoods - Top 5 Highest
    const chartData = neighborhoods?.features.map(f => ({
        name: f.properties.neighborhood_name,
        score: Math.round(f.properties.neigh_accessibility_score)
    })).sort((a, b) => b.score - a.score).slice(0, 5) || [];

    return (
        <aside className="glass-panel" style={{
            width: 'var(--sidebar-width)',
            height: '100%',
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '32px',
            zIndex: 1000,
            boxShadow: 'var(--shadow-lg)'
        }}>
            <header>
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', marginBottom: '8px' }}>
                    <MapIcon size={24} color="var(--accent)" />
                    <h1 style={{ fontSize: '1.25rem', fontWeight: 700 }}>Riverside Parks</h1>
                </div>
                <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                    Accessibility Analysis Dashboard
                </p>
            </header>

            <section>
                <h2 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
                    Global Metrics
                </h2>
                <div style={{ display: 'grid', gridTemplateColumns: '1fr', gap: '12px' }}>
                    <div className="glass-panel" style={{ padding: '16px', borderRadius: '12px' }}>
                        <div style={{ color: 'var(--text-muted)', fontSize: '0.75rem', marginBottom: '4px' }}>Total Neighborhoods Analyzed</div>
                        <div style={{ fontSize: '1.5rem', fontWeight: 700 }}>{stats?.total_neighborhoods || '...'}</div>
                    </div>
                </div>
            </section>

            <section>
                <h2 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
                    Map Layers
                </h2>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                    <button
                        onClick={() => setShowTracts(true)}
                        style={{
                            padding: '12px',
                            borderRadius: '8px',
                            border: 'none',
                            background: showTracts ? 'var(--accent)' : 'var(--accent-soft)',
                            color: showTracts ? 'white' : 'var(--accent)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                        }}
                    >
                        <Database size={18} />
                        Census Tracts
                    </button>
                    <button
                        onClick={() => setShowTracts(false)}
                        style={{
                            padding: '12px',
                            borderRadius: '8px',
                            border: 'none',
                            background: !showTracts ? 'var(--accent)' : 'var(--accent-soft)',
                            color: !showTracts ? 'white' : 'var(--accent)',
                            fontWeight: 600,
                            cursor: 'pointer',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            transition: 'all 0.2s'
                        }}
                    >
                        <AlertTriangle size={18} />
                        Neighborhood Focus
                    </button>
                </div>
            </section>

            <section style={{ flex: 1, minHeight: 0, display: 'flex', flexDirection: 'column' }}>
                <h2 style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '16px' }}>
                    Top 5 Neighborhoods (Walkability)
                </h2>
                <div style={{ flex: 1 }}>
                    <ResponsiveContainer width="100%" height="100%">
                        <BarChart data={chartData} layout="vertical">
                            <XAxis type="number" hide />
                            <YAxis dataKey="name" type="category" width={80} fontSize={10} tick={{ fill: 'var(--text-secondary)' }} />
                            <Tooltip
                                contentStyle={{ background: 'var(--bg-sidebar)', border: '1px solid var(--glass-border)', borderRadius: '8px' }}
                                itemStyle={{ color: 'var(--text-primary)' }}
                            />
                            <Bar dataKey="score" fill="var(--accent)" radius={[0, 4, 4, 0]} />
                        </BarChart>
                    </ResponsiveContainer>
                </div>
            </section>

            <footer style={{ paddingTop: '16px', borderTop: '1px solid var(--glass-border)', color: 'var(--text-muted)', fontSize: '0.75rem' }}>
                Data source: OpenStreetMap & US Census Bureau
            </footer>
        </aside>
    );
}
