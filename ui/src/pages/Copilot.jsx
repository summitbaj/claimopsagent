import { useState } from 'react';
import axios from 'axios';
import { Send, Bot } from 'lucide-react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

const API_URL = 'http://localhost:8000';

export default function Copilot() {
    const { instance, accounts } = useMsal();
    const [query, setQuery] = useState('');
    const [messages, setMessages] = useState([
        { role: 'system', content: 'Hello! I am your Claims Copilot. Ask me anything about billing SOPs or coding rules.' }
    ]);
    const [loading, setLoading] = useState(false);

    const handleSend = async (e) => {
        e.preventDefault();
        if (!query.trim()) return;

        const newQuery = query;
        setMessages(prev => [...prev, { role: 'user', content: newQuery }]);
        setQuery('');
        setLoading(true);

        try {
            const request = {
                ...loginRequest,
                account: accounts[0]
            };
            let token;
            try {
                const response = await instance.acquireTokenSilent(request);
                token = response.accessToken;
            } catch (e) {
                const response = await instance.acquireTokenPopup(request);
                token = response.accessToken;
            }

            const res = await axios.post(
                `${API_URL}/guide`,
                { query: newQuery },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setMessages(prev => [...prev, { role: 'system', content: res.data.guidance }]);
        } catch (err) {
            setMessages(prev => [...prev, { role: 'system', content: 'Sorry, I encountered an error retrieving that information.' }]);
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="flex flex-col h-[calc(100vh-4rem)] max-w-3xl mx-auto">
            <h2 className="text-3xl font-bold mb-6">SOP Copilot</h2>

            {/* Chat Area */}
            <div className="flex-1 overflow-y-auto space-y-4 mb-6 pr-2">
                {messages.map((msg, i) => (
                    <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center shrink-0 ${msg.role === 'user' ? 'bg-blue-600 text-white' : 'bg-slate-200 text-slate-600'}`}>
                            {msg.role === 'user' ? 'Me' : <Bot size={18} />}
                        </div>
                        <div className={`p-4 rounded-2xl max-w-[80%] ${msg.role === 'user' ? 'bg-blue-600 text-white rounded-tr-none' : 'bg-white border border-slate-200 shadow-sm rounded-tl-none'}`}>
                            <p className="whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                        </div>
                    </div>
                ))}
                {loading && (
                    <div className="flex gap-4">
                        <div className="w-8 h-8 rounded-full bg-slate-200 flex items-center justify-center shrink-0">
                            <Bot size={18} />
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
                    placeholder="Ask a question about billing rules..."
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
