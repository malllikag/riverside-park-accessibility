import React, { useEffect } from 'react';
import { MapContainer, TileLayer, GeoJSON, Popup, useMap, Marker, Polyline, Tooltip } from 'react-leaflet';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';

// Fix for default Leaflet marker icons in React/Vite
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
    iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
    iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
    shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

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

function MapController({ searchedLocation, nearbyParks }) {
    const map = useMap();

    useEffect(() => {
        if (searchedLocation && nearbyParks && nearbyParks.length > 0) {
            // Create bounds that include the searched location and the nearest park
            const nearestParkCoord = [nearbyParks[0].coordinates[1], nearbyParks[0].coordinates[0]];
            const bounds = L.latLngBounds([
                [searchedLocation.lat, searchedLocation.lng],
                nearestParkCoord
            ]);

            // Expand bounds to include other nearby parks for context
            nearbyParks.slice(1).forEach(park => {
                bounds.extend([park.coordinates[1], park.coordinates[0]]);
            });

            map.fitBounds(bounds, { padding: [50, 50], maxZoom: 16 });
        } else if (searchedLocation) {
            map.flyTo([searchedLocation.lat, searchedLocation.lng], 16, {
                duration: 1.5,
                easeLinearity: 0.25
            });
        }
    }, [searchedLocation, nearbyParks, map]);

    return null;
}

export function Map({ tracts, parks, neighborhoods, showTracts = true, searchedLocation, nearbyParks }) {
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

    const parkStyle = {
        fillColor: '#22c55e',
        weight: 1,
        opacity: 1,
        color: '#166534',
        fillOpacity: 0.5
    };

    const onEachPark = (feature, layer) => {
        const name = feature.properties.name || 'Unnamed Park';
        layer.bindPopup(`
            <div style="font-family: sans-serif; min-width: 120px;">
                <strong style="display: block; margin-bottom: 4px;">${name}</strong>
                <div style="font-size: 14px; color: #166534;">Park Space</div>
            </div>
        `);
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

                <MapController searchedLocation={searchedLocation} nearbyParks={nearbyParks} />

                {searchedLocation && nearbyParks && nearbyParks.length > 0 && (
                    <Polyline
                        positions={[
                            [searchedLocation.lat, searchedLocation.lng],
                            [nearbyParks[0].coordinates[1], nearbyParks[0].coordinates[0]]
                        ]}
                        pathOptions={{
                            color: 'var(--accent)',
                            dashArray: '10, 10',
                            weight: 3,
                            opacity: 0.6
                        }}
                    />
                )}

                {nearbyParks && nearbyParks.map((park, i) => (
                    <Marker
                        key={`nearby-${i}`}
                        position={[park.coordinates[1], park.coordinates[0]]}
                        icon={L.divIcon({
                            className: 'custom-marker',
                            html: `<div style="
                                background: ${i === 0 ? '#fbbf24' : '#22c55e'};
                                width: 14px;
                                height: 14px;
                                border: 3px solid white;
                                border-radius: 50%;
                                box-shadow: 0 0 10px rgba(0,0,0,0.3);
                            "></div>`,
                            iconSize: [14, 14],
                            iconAnchor: [7, 7]
                        })}
                    >
                        <Tooltip permanent={i === 0} direction="top" offset={[0, -10]}>
                            <div style={{ fontSize: '11px', fontWeight: 600 }}>
                                {i === 0 ? '🏆 Largest/Closest: ' : ''}{park.name}
                            </div>
                        </Tooltip>
                    </Marker>
                ))}

                {searchedLocation && (
                    <Marker position={[searchedLocation.lat, searchedLocation.lng]}>
                        <Popup>
                            <div style={{ fontSize: '12px' }}>{searchedLocation.address}</div>
                        </Popup>
                    </Marker>
                )}

                {parks && (
                    <GeoJSON
                        key={`parks-${parks.features.length}`}
                        data={parks}
                        style={parkStyle}
                        onEachFeature={onEachPark}
                        pointToLayer={(feature, latlng) => {
                            return L.circleMarker(latlng, {
                                radius: 6,
                                fillColor: '#22c55e',
                                color: '#166534',
                                weight: 1,
                                opacity: 1,
                                fillOpacity: 0.7
                            });
                        }}
                    />
                )}

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
