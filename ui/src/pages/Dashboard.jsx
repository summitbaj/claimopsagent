import { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, Cell, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

const API_URL = 'http://localhost:8000';

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);

    const { instance, accounts } = useMsal();

    useEffect(() => {
        const fetchData = async () => {
            const request = {
                ...loginRequest,
                account: accounts[0]
            };
            try {
                let token;
                try {
                    const response = await instance.acquireTokenSilent(request);
                    token = response.accessToken;
                } catch (e) {
                    const response = await instance.acquireTokenPopup(request);
                    token = response.accessToken;
                }

                const res = await axios.get(`${API_URL}/analyze`, {
                    headers: { Authorization: `Bearer ${token}` }
                });
                setData(res.data);
            } catch (err) {
                console.error(err);
            } finally {
                setLoading(false);
            }
        };

        fetchData();
    }, [instance, accounts]);

    if (loading) return <div className="p-8">Loading Analytics...</div>;
    if (!data) return <div className="p-8 text-red-500">Failed to load data. Ensure backend is running.</div>;

    const chartData = data.infographic?.data
        ? Object.entries(data.infographic.data).map(([name, value]) => ({ name, value }))
        : [];

    const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042'];

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold">Claims Analytics</h2>

            {/* Narrative Card */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold mb-2">AI Insight</h3>
                <p className="text-slate-600">{data.narrative}</p>
            </div>

            {/* Chart Card */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100 h-96">
                <h3 className="text-lg font-semibold mb-4">{data.infographic?.title || 'Overview'}</h3>
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={chartData}
                            cx="50%"
                            cy="50%"
                            labelLine={false}
                            outerRadius={120}
                            fill="#8884d8"
                            dataKey="value"
                        >
                            {chartData.map((entry, index) => (
                                <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                            ))}
                        </Pie>
                        <Tooltip />
                        <Legend />
                    </PieChart>
                </ResponsiveContainer>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div className="bg-blue-50 p-6 rounded-xl border border-blue-100">
                    <p className="text-sm text-blue-600 font-medium">Total Claims</p>
                    <p className="text-3xl font-bold text-blue-900">{data.total_records}</p>
                </div>
            </div>
        </div>
    );
}
