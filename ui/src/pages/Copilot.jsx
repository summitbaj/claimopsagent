import { useState } from 'react';
import axios from 'axios';
import { Send, Bot, Settings, Brain, FileText } from 'lucide-react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import SettingsPanel from '../components/SettingsPanel';
import {
    BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
    XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';

const API_URL = 'http://localhost:8000';

const COLORS = ['#3b82f6', '#ef4444', '#10b981', '#f59e0b', '#8b5cf6', '#ec4899'];

export default function Copilot() {
    const { instance, accounts } = useMsal();
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([
        {
            role: 'system',
            content: 'Hello! I am your Claims Intelligence Agent. I can help you with:\n• Billing procedures and SOPs\n• Claim analysis and predictions\n• Analytics and reporting\n\nClick the settings icon to upload knowledge sources!',
            type: 'text'
        }
    ]);
    const [loading, setLoading] = useState(false);
    const [showSettings, setShowSettings] = useState(false);

    const getToken = async () => {
        const request = {
            ...loginRequest,
            account: accounts[0]
        };
        try {
            const response = await instance.acquireTokenSilent(request);
            return response.accessToken;
        } catch (e) {
            const response = await instance.acquireTokenPopup(request);
            return response.accessToken;
        }
    };

    const handleSend = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const newQuery = query;
        setMessages(prev => [...prev, { role: 'user', content: newQuery, type: 'text' }]);
        setQuery('');
        setLoading(true);

        try {
            const token = await getToken();
            const history = messages.map(m => ({ role: m.role, content: m.content }));

            const res = await axios.post(
                `${API_URL}/chat`,
                { query: newQuery, history },
                { headers: { Authorization: `Bearer ${token}` } }
            );

            const response = res.data;

            // Build message with thinking steps if available
            let messageContent = {
                role: 'system',
                content: response.content,
                type: response.response_type,
                thinking: response.thinking_steps,
                chartData: response.chart_data,
                sources: response.sources,
                metadata: response.metadata
            };

            setMessages(prev => [...prev, messageContent]);
        } catch (err) {
            console.error('Chat error:', err);
            setMessages(prev => [...prev, {
                role: 'system',
                content: `Error: ${err.response?.data?.detail || err.message}`,
                type: 'text'
            }]);
        } finally {
            setLoading(false);
        }
    };

    const renderChart = (chartData) => {
        if (!chartData) return null;

        const { type, title, data } = chartData;

        if (type === 'pie') {
            const pieData = Object.entries(data).map(([name, value]) => ({ name, value }));
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <PieChart>
                        <Pie
                            data={pieData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                            outerRadius={80}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {pieData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            );
        } else if (type === 'bar') {
            const barData = data.payers?.map((payer, i) => ({
                name: payer.length > 20 ? payer.substring(0, 20) + '...' : payer,
                value: data.failure_rates[i]
            })) || [];
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={barData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="name" angle={-45} textAnchor="end" height={100} />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Bar dataKey="value" fill="#3b82f6" name="Failure Rate %" />
                    </BarChart>
                </ResponsiveContainer>
            );
        } else if (type === 'line') {
            const lineData = data.months?.map((month, i) => ({
                month,
                count: data.counts[i]
            })) || [];
            return (
                <ResponsiveContainer width="100%" height={300}>
                    <LineChart data={lineData}>
                        <CartesianGrid strokeDasharray="3 3" />
                        <XAxis dataKey="month" />
                        <YAxis />
                        <Tooltip />
                        <Legend />
                        <Line type="monotone" dataKey="count" stroke="#3b82f6" strokeWidth={2} />
                    </LineChart>
                </ResponsiveContainer>
            );
        }

        return null;
    };

    const renderMessage = (msg, i) => {
        const isUser = msg.role === 'user';

        return (
            <div key={i} className={`flex gap-4 ${isUser ? 'flex-row-reverse' : ''}`}>
                <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${isUser ? 'bg-blue-600 text-white' : 'bg-gradient-to-br from-slate-700 to-slate-900 text-white'}`}>
                    {isUser ? 'Me' : <Brain size={18} />}
                </div>
                <div className={`max-w-[80%] ${isUser ? '' : 'space-y-3'}`}>
                    {/* Thinking Steps */}
                    {!isUser && msg.thinking && msg.thinking.length > 0 && (
                        <details className="bg-slate-50 border border-slate-200 rounded-lg p-3 text-sm">
                            <summary className="cursor-pointer text-slate-600 font-medium">
                                💭 Chain of Thought
                            </summary>
                            <div className="mt-2 space-y-2">
                                {msg.thinking.map((step, idx) => (
                                    <div key={idx} className="border-l-2 border-blue-500 pl-3">
                                        <div className="font-semibold text-slate-700">{step.step}</div>
                                        <div className="text-slate-600">{step.conclusion}</div>
                                    </div>
                                ))}
                            </div>
                        </details>
                    )}

                    {/* Main Content */}
                    <div className={`p-4 rounded-2xl ${isUser ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border border-slate-200 shadow-sm rounded-tl-none'}`}>
                        <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>

                        {/* Chart */}
                        {!isUser && msg.chartData && (
                            <div className="mt-4 pt-4 border-t border-slate-200">
                                <h4 className="font-semibold mb-2 text-slate-700">{msg.chartData.title}</h4>
                                {renderChart(msg.chartData)}
                            </div>
                        )}

                        {/* Sources */}
                        {!isUser && msg.sources && msg.sources.length > 0 && (
                            <div className="mt-3 pt-3 border-t border-slate-200">
                                <div className="text-xs text-slate-500 space-y-1">
                                    <div className="font-semibold">📚 Sources:</div>
                                    {msg.sources.map((source, idx) => (
                                        <div key={idx} className="flex items-center gap-2">
                                            <FileText size={12} />
                                            <span>{source.source} (Slide {source.slide_number})</span>
                                        </div>
                                    ))}
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </div>
        );
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] max-w-4xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-3xl font-bold">Claims Intelligence Agent</h2>
                <button
                    onClick={() => setShowSettings(true)}
                    className="p-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors"
                    title="Knowledge Base Settings"
                >
                    <Settings size={22} />
                </button>
            </div>

            {/* Settings Panel Modal */}
            <SettingsPanel isOpen={showSettings} onClose={() => setShowSettings(false)} />

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
                {messages.map(renderMessage)}
                {loading && (
                    <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center shrink-0 text-white">
                            <Brain size={18} />
                        </div>
                        <div className="bg-white border border-slate-200 p-4 rounded-2xl rounded-tl-none">
                            <div className="flex gap-1">
                                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce"></span>
                                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-75"></span>
                                <span className="w-2 h-2 bg-slate-400 rounded-full animate-bounce delay-150"></span>
                            </div>
                        </div>
                    </div>
                )}
            </div>

            {/* Input Area */}
            <form onSubmit={handleSend} className="relative">
                <input
                    type="text"
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    placeholder="Ask about billing rules, analyze a claim, or request a report..."
                    className="w-full p-4 pr-16 bg-white border border-slate-300 rounded-xl shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
                <button
                    type="submit"
                    disabled={loading || !query.trim()}
                    className="absolute right-2 top-2 bottom-2 bg-slate-900 text-white px-4 rounded-lg hover:bg-slate-800 disabled:opacity-50 transition-colors"
                >
                    <Send size={18} />
                </button>
            </form>
        </div>
    );
}
