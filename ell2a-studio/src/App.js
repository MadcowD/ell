import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import React, { useEffect } from 'react';
import { Toaster, toast } from 'react-hot-toast';
import { Route, BrowserRouter as Router, Routes } from 'react-router-dom';
import Sidebar from './components/Sidebar';
import { ThemeProvider } from './contexts/ThemeContext';
import { useWebSocketConnection } from './hooks/useBackend';
import Home from './pages/Home';
import Invocations from './pages/Invocations';
import LMP from './pages/LMP';
import './styles/globals.css';
import './styles/sourceCode.css';

const WebSocketConnectionProvider = ({ children }) => {
    const { isConnected } = useWebSocketConnection()

    React.useEffect(() => {
        if (isConnected) {
            toast.success('Store connected', {
                duration: 1000
            })
        } else {
            toast('Connecting to store...', {
                icon: '🔄',
                duration: 500
            })
        }
    }, [isConnected])

    return (
        <>
            {children}
            <Toaster position="top-right" />
        </>
    )
}

// Create a client
const queryClient = new QueryClient()

function App() {
    useEffect(() => {
        const checkVersion = async () => {
            try {
                const response = await fetch('https://version.agentbase.space/ell2a-ai/studio')
                const latestVersion = await response.text()

                const currentVersion = process.env.REACT_APP_ELL2A_VERSION // Assuming you have the current version in an environment variable
                console.log('Current version:', currentVersion)
                console.log('Latest version:', latestVersion)
                if (currentVersion !== latestVersion) {
                    toast(
                        <div className="flex flex-col space-y-2">
                            <span className="font-semibold">New version available: {latestVersion}</span>
                            <span>To update, run:</span>
                            <code className="bg-gray-700 p-1 rounded-md">pip install --upgrade ell2a-ai</code>
                        </div>,
                        {
                            icon: '🚀',
                            duration: 15000,
                            position: 'top-right',
                            style: {
                                borderRadius: '12px',
                                padding: '16px',
                                background: '#333',
                                color: '#fff'
                            }
                        }
                    )
                }
            } catch (error) {
                console.error('Failed to check version', error)
                toast.error('Failed to check version', {
                    duration: 3000
                })
            }
        }

        checkVersion()
    }, [])

    return (
        <QueryClientProvider client={queryClient}>
            <ThemeProvider>
                <WebSocketConnectionProvider>
                    <Router>
                        <div className="flex min-h-screen max-h-screen bg-gray-900 text-gray-100">
                            <Sidebar />
                            <div className="flex-1 flex flex-col max-h-screen overflow-hidden">
                                <main className="flex-1 max-h-screen overflow-auto hide-scrollbar">
                                    <Routes>
                                        <Route path="/" element={<Home />} />
                                        <Route path="/lmp/:name/:id?" element={<LMP />} />
                                        <Route path="/invocations" element={<Invocations />} />
                                    </Routes>
                                </main>
                            </div>
                        </div>
                    </Router>
                </WebSocketConnectionProvider>
            </ThemeProvider>
        </QueryClientProvider>
    )
}

export default App
