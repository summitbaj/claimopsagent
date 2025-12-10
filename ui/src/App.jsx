import { BrowserRouter as Router, Routes, Route, Link } from 'react-router-dom';
import { LayoutDashboard, FileSearch, MessageSquare } from 'lucide-react';
import Dashboard from './pages/Dashboard';
import ClaimView from './pages/ClaimView';
import Copilot from './pages/Copilot';
import { AuthenticatedTemplate, UnauthenticatedTemplate, useIsAuthenticated } from "@azure/msal-react";
import { SignInButton } from "./components/SignInButton";
import { SignOutButton } from "./components/SignOutButton";

function App() {
    const isAuthenticated = useIsAuthenticated();

    return (
        <Router>
            <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
                {/* Sidebar */}
                <aside className="w-64 bg-slate-900 text-white flex flex-col">
                    <div className="p-6 border-b border-slate-800">
                        <h1 className="text-xl font-bold tracking-tight">Claims<span className="text-blue-400">Agent</span></h1>
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
                    <AuthenticatedTemplate>
                        <Routes>
                            <Route path="/" element={<Dashboard />} />
                            <Route path="/claim" element={<ClaimView />} />
                            <Route path="/copilot" element={<Copilot />} />
                        </Routes>
                    </AuthenticatedTemplate>
                    <UnauthenticatedTemplate>
                        <div className="flex h-full items-center justify-center flex-col gap-4">
                            <h2 className="text-2xl font-bold">Please Sign In</h2>
                            <p className="text-slate-500">You need to authenticate with Microsoft to access claims data.</p>
                            <SignInButton />
                        </div>
                    </UnauthenticatedTemplate>
                </main>
            </div>
        </Router>
    );
}

export default App;
