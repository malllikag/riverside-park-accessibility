import React from 'react';
import { MapContainer, TileLayer, GeoJSON, Tooltip, Popup } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';

const COLOR_RAMP = [
    { limit: 20, color: '#ffffcc' },
    { limit: 40, color: '#c2e699' },
    { limit: 60, color: '#78c679' },
    { limit: 80, color: '#31a354' },
    { limit: 100, color: '#006837' }
];

const getColor = (score) => {
    if (score === null || score === undefined) return '#dddddd';
    for (const stop of COLOR_RAMP) {
        if (score < stop.limit) return stop.color;
    }
    return '#006837';
};

export function Map({ tracts, neighborhoods, showTracts = true }) {
    const center = [33.9533, -117.3961]; // Riverside center

    const tractStyle = (feature) => ({
        fillColor: getColor(feature.properties.accessibility_score),
        weight: 0.5,
        opacity: 1,
        color: 'white',
        fillOpacity: 0.7
    });

    const neighStyle = (feature) => {
        const isUnderserved = feature.properties.is_underserved;
        return {
            fillColor: getColor(feature.properties.neigh_accessibility_score),
            weight: isUnderserved ? 3 : 1,
            opacity: 1,
            color: isUnderserved ? '#ef4444' : '#334155',
            fillOpacity: 0.6
        };
    };

    const onEachTract = (feature, layer) => {
        const score = Math.round(feature.properties.accessibility_score);
        layer.bindPopup(`
            <div style="font-family: sans-serif; min-width: 120px;">
                <strong style="display: block; margin-bottom: 4px;">Census Tract</strong>
                <div style="font-size: 14px;">Score: <strong>${score}</strong> / 100</div>
            </div>
        `);
    };

    const onEachNeighborhood = (feature, layer) => {
        const name = feature.properties.neighborhood_name;
        const score = Math.round(feature.properties.neigh_accessibility_score);
        layer.bindPopup(`
            <div style="font-family: sans-serif; min-width: 150px;">
                <strong style="display: block; font-size: 16px; margin-bottom: 8px;">${name}</strong>
                <div style="font-size: 14px;">Walkability: <strong>${score}</strong> / 100</div>
            </div>
        `);
    };

    return (
        <div style={{ height: '100%', width: '100%', background: '#f1f5f9' }}>
            <MapContainer
                center={center}
                zoom={12}
                style={{ height: '100%', width: '100%' }}
                zoomControl={false}
            >
                <TileLayer
                    attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors &copy; <a href="https://carto.com/attributions">CARTO</a>'
                    url="https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png"
                />

                {showTracts && tracts && (
                    <GeoJSON
                        key={`tracts-${tracts.features.length}`}
                        data={tracts}
                        style={tractStyle}
                        onEachFeature={onEachTract}
                    />
                )}

                {!showTracts && neighborhoods && (
                    <GeoJSON
                        key={`neighs-${neighborhoods.features.length}`}
                        data={neighborhoods}
                        style={neighStyle}
                        onEachFeature={onEachNeighborhood}
                    />
                )}
            </MapContainer>
        </div>
    );
}
