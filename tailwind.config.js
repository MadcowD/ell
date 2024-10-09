module.exports = {
    darkMode: ['class'],
    content: ['./src/**/*.{js,jsx,ts,tsx}'],
    theme: {
        extend: {
            colors: {
                border: 'hsl(var(--border))',
                input: 'hsl(var(--input))',
                ring: 'hsl(var(--ring))',
                background: 'hsl(var(--background))',
                foreground: 'hsl(var(--foreground))',
                primary: {
                    DEFAULT: 'hsl(var(--primary))',
                    foreground: 'hsl(var(--primary-foreground))'
                },
                secondary: {
                    DEFAULT: 'hsl(var(--secondary))',
                    foreground: 'hsl(var(--secondary-foreground))'
                },
                destructive: {
                    DEFAULT: 'hsl(var(--destructive))',
                    foreground: 'hsl(var(--destructive-foreground))'
                },
                muted: {
                    DEFAULT: 'hsl(var(--muted))',
                    foreground: 'hsl(var(--muted-foreground))'
                },
                accent: {
                    DEFAULT: 'hsl(var(--accent))',
                    foreground: 'hsl(var(--accent-foreground))'
                },
                popover: {
                    DEFAULT: 'hsl(var(--popover))',
                    foreground: 'hsl(var(--popover-foreground))'
                },
                card: {
                    DEFAULT: 'hsl(var(--card))',
                    foreground: 'hsl(var(--card-foreground))'
                }
            },
            keyframes: {
                highlight: {
                    '0%': { backgroundColor: 'rgba(59, 130, 246, 0.5)' },
                    '100%': { backgroundColor: 'rgba(59, 130, 246, 0)' }
                }
            },
            animation: {
                highlight: 'highlight 1s ease-in-out'
            }
        }
    },
    plugins: [
        function ({ addUtilities }) {
            const newUtilities = {
                '.text-shadow': {
                    textShadow: '0 1px 2px rgba(0, 0, 0, 0.2)'
                }
            }
            addUtilities(newUtilities, ['responsive', 'hover'])
        }
    ]
}
