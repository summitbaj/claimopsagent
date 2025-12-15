import { BrowserRouter as Router, Routes, Route, Link, useNavigate } from 'react-router-dom';
import { LayoutDashboard, FileSearch, MessageSquare, Menu, X } from 'lucide-react';
import { useEffect, useState } from 'react';
import Dashboard from './pages/Dashboard';
import ClaimView from './pages/ClaimView';
import Copilot from './pages/Copilot';
import { AuthenticatedTemplate, UnauthenticatedTemplate, useIsAuthenticated } from "@azure/msal-react";
import { SignInButton } from "./components/SignInButton";
import { SignOutButton } from "./components/SignOutButton";

const AuthCallback = () => {
    const isAuthenticated = useIsAuthenticated();
    const navigate = useNavigate();

    useEffect(() => {
        if (isAuthenticated) {
            navigate("/");
        }
    }, [isAuthenticated, navigate]);

    return <div className="p-8">Processing authentication...</div>;
};

function App() {
    const [sidebarOpen, setSidebarOpen] = useState(false);

    return (
        <Router>
            <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
                {/* Collapsed Sidebar - Icons Only */}
                <aside className={`${sidebarOpen ? 'hidden' : 'flex'} w-16 bg-slate-900 text-white flex-col z-10`}>
                    <div className="p-4 border-b border-slate-800 flex justify-center">
                        <button onClick={() => setSidebarOpen(true)} className="text-white hover:text-blue-400 transition-colors">
                            <Menu size={24} />
                        </button>
                    </div>

                    <nav className="flex-1 p-2 space-y-2">
                        <Link to="/" className="flex items-center justify-center p-3 rounded-lg hover:bg-slate-800 transition-colors" title="Dashboard">
                            <LayoutDashboard size={22} />
                        </Link>
                        <Link to="/claim" className="flex items-center justify-center p-3 rounded-lg hover:bg-slate-800 transition-colors" title="Claim View">
                            <FileSearch size={22} />
                        </Link>
                        <Link to="/copilot" className="flex items-center justify-center p-3 rounded-lg hover:bg-slate-800 transition-colors" title="Copilot">
                            <MessageSquare size={22} />
                        </Link>
                    </nav>
                </aside>

                {/* Expanded Sidebar */}
                <aside className={`${sidebarOpen ? 'flex' : 'hidden'} w-64 bg-slate-900 text-white flex-col z-20`}>
                    <div className="p-6 border-b border-slate-800 flex items-center justify-between">
                        <h1 className="text-xl font-bold tracking-tight">Claims<span className="text-blue-400">Agent</span></h1>
                        <button onClick={() => setSidebarOpen(false)} className="text-white hover:text-slate-400 transition-colors">
                            <X size={20} />
                        </button>
                    </div>

                    <nav className="flex-1 p-4 space-y-2">
                        <Link to="/" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors">
                            <LayoutDashboard size={20} /> Dashboard
                        </Link>
                        <Link to="/claim" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors">
                            <FileSearch size={20} /> Claim View
                        </Link>
                        <Link to="/copilot" className="flex items-center gap-3 px-4 py-3 rounded-lg hover:bg-slate-800 transition-colors">
                            <MessageSquare size={20} /> Copilot
                        </Link>
                    </nav>

                    <div className="p-4 border-t border-slate-800">
                        <UnauthenticatedTemplate>
                            <div className="text-center">
                                <p className="text-xs text-slate-400 mb-2">Sign in to access Dataverse</p>
                                <SignInButton />
                            </div>
                        </UnauthenticatedTemplate>
                        <AuthenticatedTemplate>
                            <div className="flex justify-between items-center">
                                <span className="text-sm font-medium text-slate-300">Connected</span>
                                <SignOutButton />
                            </div>
                        </AuthenticatedTemplate>
                    </div>
                </aside>

                {/* Main Content */}
                <main className="flex-1 overflow-y-auto p-8">
                    <Routes>
                        <Route path="/auth/callback" element={<AuthCallback />} />

                        <Route path="/" element={
                            <AuthenticatedTemplate>
                                <Dashboard />
                            </AuthenticatedTemplate>
                        } />
                        <Route path="/claim" element={
                            <AuthenticatedTemplate>
                                <ClaimView />
                            </AuthenticatedTemplate>
                        } />
                        <Route path="/copilot" element={
                            <AuthenticatedTemplate>
                                <Copilot />
                            </AuthenticatedTemplate>
                        } />
                    </Routes>

                    <UnauthenticatedTemplate>
                        <Routes>
                            <Route path="/auth/callback" element={<></>} />
                            <Route path="*" element={
                                <div className="flex h-full items-center justify-center flex-col gap-4 mt-20">
                                    <h2 className="text-2xl font-bold">Please Sign In</h2>
                                    <p className="text-slate-500">You need to authenticate with Microsoft to access claims data.</p>
                                    <SignInButton />
                                </div>
                            } />
                        </Routes>
                    </UnauthenticatedTemplate>
                </main>
            </div>
        </Router>
    );
}

export default App;
