import React from 'react'

const getColorFromVersion = (version) => {
    const hue = (version * 137.508) % 360 // Golden angle approximation
    return `hsl(${hue}, 40%, 70%)` // Base color
}

const VersionBadge = ({ version, hash, className = '', shortVersion = false }) => {
    const baseColor = getColorFromVersion(version)
    const lighterColor = `hsl(${baseColor.match(/\d+/)[0]}, 40%, 75%)` // Slightly lighter
    const textColor = 'text-gray-900' // Dark text for contrast

    return (
        <div
            className={`inline-flex items-center text-xs font-medium rounded-full overflow-hidden ${className}`}
            title={hash ? `Hash: ${hash}` : undefined}>
            <div className={`px-2 py-1 ${textColor}`} style={{ backgroundColor: baseColor }}>
                {shortVersion ? `v${version}` : `Version ${version}`}
            </div>
            {hash && (
                <div className={`px-2 py-1 ${textColor} font-mono`} style={{ backgroundColor: lighterColor }}>
                    {hash.substring(0, 9)}
                </div>
            )}
        </div>
    )
}

export default VersionBadge
