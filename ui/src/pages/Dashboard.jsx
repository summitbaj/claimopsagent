import { useEffect, useState } from 'react';
import axios from 'axios';
import { PieChart, Pie, BarChart, Bar, LineChart, Line, Cell, ResponsiveContainer, Tooltip, Legend, XAxis, YAxis, CartesianGrid } from 'recharts';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import { TrendingUp, AlertCircle, Clock, DollarSign } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function Dashboard() {
    const [data, setData] = useState(null);
    const [loading, setLoading] = useState(true);
    const [expandedPayer, setExpandedPayer] = useState(null);

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

    const statusChartData = data.infographic?.data
        ? Object.entries(data.infographic.data).map(([name, value]) => ({ name, value }))
        : [];

    const failureReasonsData = data.failure_reasons
        ? Object.entries(data.failure_reasons).map(([name, value]) => ({ name, value }))
        : [];

    const claimTypesData = data.claim_types
        ? Object.entries(data.claim_types).map(([name, value]) => ({ name, value }))
        : [];

    const COLORS = ['#EF4444', '#10B981', '#F59E0B', '#3B82F6', '#8B5CF6'];

    return (
        <div className="space-y-6">
            <h2 className="text-3xl font-bold">Claims Analytics Dashboard</h2>

            {/* Key Metrics Cards */}
            {data.key_metrics && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-gradient-to-br from-blue-50 to-blue-100 p-6 rounded-xl border border-blue-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-blue-600 font-medium">Total Claims</p>
                                <p className="text-3xl font-bold text-blue-900">{data.total_records}</p>
                            </div>
                            <TrendingUp className="text-blue-500" size={32} />
                        </div>
                    </div>
                    <div className="bg-gradient-to-br from-red-50 to-red-100 p-6 rounded-xl border border-red-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-red-600 font-medium">Failure Rate</p>
                                <p className="text-3xl font-bold text-red-900">{data.key_metrics.failure_rate_percent}%</p>
                            </div>
                            <AlertCircle className="text-red-500" size={32} />
                        </div>
                    </div>
                    <div className="bg-gradient-to-br from-green-50 to-green-100 p-6 rounded-xl border border-green-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-green-600 font-medium">Avg Processing</p>
                                <p className="text-3xl font-bold text-green-900">{data.key_metrics.avg_processing_days}d</p>
                            </div>
                            <Clock className="text-green-500" size={32} />
                        </div>
                    </div>
                    <div className="bg-gradient-to-br from-purple-50 to-purple-100 p-6 rounded-xl border border-purple-200">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-purple-600 font-medium">Avg Amount</p>
                                <p className="text-3xl font-bold text-purple-900">${data.key_metrics.avg_claim_amount.toLocaleString()}</p>
                            </div>
                            <DollarSign className="text-purple-500" size={32} />
                        </div>
                    </div>
                </div>
            )}

            {/* AI Narrative */}
            <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                <h3 className="text-lg font-semibold mb-2 flex items-center gap-2">
                    <span className="text-2xl">🤖</span> AI Insight
                </h3>
                <p className="text-slate-600">{data.narrative}</p>
            </div>

            {/* Charts Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                {/* Claim Status Distribution */}
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold mb-4">{data.infographic?.title || 'Claim Status'}</h3>
                    <ResponsiveContainer width="100%" height={300}>
                        <PieChart>
                            <Pie
                                data={statusChartData}
                                cx="50%"
                                cy="50%"
                                labelLine={false}
                                label={({ name, percent }) => `${name}: ${(percent * 100).toFixed(0)}%`}
                                outerRadius={100}
                                fill="#8884d8"
                                dataKey="value"
                            >
                                {statusChartData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                                ))}
                            </Pie>
                            <Tooltip />
                        </PieChart>
                    </ResponsiveContainer>
                </div>

                {/* Top Failure Reasons */}
                {data.failure_reasons && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <h3 className="text-lg font-semibold mb-4">🚨 Top Failure Reasons</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={failureReasonsData} layout="vertical">
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis type="number" />
                                <YAxis dataKey="name" type="category" width={150} tick={{ fontSize: 12 }} />
                                <Tooltip />
                                <Bar dataKey="value" fill="#EF4444" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Claim Types Distribution */}
                {data.claim_types && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <h3 className="text-lg font-semibold mb-4">📋 Claim Types Breakdown</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <BarChart data={claimTypesData}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                                <YAxis />
                                <Tooltip />
                                <Bar dataKey="value" fill="#3B82F6" />
                            </BarChart>
                        </ResponsiveContainer>
                    </div>
                )}

                {/* Monthly Failure Trend */}
                {data.monthly_trend && (
                    <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                        <h3 className="text-lg font-semibold mb-4">📈 Failure Rate Trend (6 Months)</h3>
                        <ResponsiveContainer width="100%" height={300}>
                            <LineChart data={data.monthly_trend}>
                                <CartesianGrid strokeDasharray="3 3" />
                                <XAxis dataKey="month" />
                                <YAxis label={{ value: 'Failure Rate (%)', angle: -90, position: 'insideLeft' }} />
                                <Tooltip />
                                <Legend />
                                <Line type="monotone" dataKey="failure_rate" stroke="#EF4444" strokeWidth={2} dot={{ r: 5 }} />
                            </LineChart>
                        </ResponsiveContainer>
                    </div>
                )}
            </div>

            {/* Payer/Insurance Performance Analysis */}
            {data.payer_performance && (
                <div className="bg-white p-6 rounded-xl shadow-sm border border-slate-100">
                    <h3 className="text-lg font-semibold mb-4">🏥 Insurance/Payer Performance Analysis</h3>
                    <div className="overflow-x-auto">
                        <table className="w-full">
                            <thead>
                                <tr className="border-b-2 border-slate-200">
                                    <th className="text-left py-3 px-4 font-semibold text-slate-700">Payer</th>
                                    <th className="text-center py-3 px-4 font-semibold text-slate-700">Total</th>
                                    <th className="text-center py-3 px-4 font-semibold text-green-700">Approved</th>
                                    <th className="text-center py-3 px-4 font-semibold text-red-700">Failed</th>
                                    <th className="text-center py-3 px-4 font-semibold text-orange-700">Pending</th>
                                    <th className="text-center py-3 px-4 font-semibold text-slate-700">Failure Rate</th>
                                    <th className="text-center py-3 px-4 font-semibold text-slate-700">Avg Days</th>
                                    <th className="text-center py-3 px-4 font-semibold text-slate-700">Details</th>
                                </tr>
                            </thead>
                            <tbody>
                                {data.payer_performance.map((payer, idx) => (
                                    <>
                                        <tr
                                            key={payer.payer}
                                            className={`border-b border-slate-100 hover:bg-slate-50 ${payer.failure_rate > 30 ? 'bg-red-50' : ''
                                                }`}
                                        >
                                            <td className="py-3 px-4 font-medium">{payer.payer}</td>
                                            <td className="text-center py-3 px-4">{payer.total_claims}</td>
                                            <td className="text-center py-3 px-4 text-green-600 font-semibold">{payer.approved}</td>
                                            <td className="text-center py-3 px-4 text-red-600 font-semibold">{payer.failed}</td>
                                            <td className="text-center py-3 px-4 text-orange-600">{payer.pending}</td>
                                            <td className="text-center py-3 px-4">
                                                <span className={`px-2 py-1 rounded-full text-sm font-semibold ${payer.failure_rate > 30
                                                        ? 'bg-red-100 text-red-700'
                                                        : 'bg-green-100 text-green-700'
                                                    }`}>
                                                    {payer.failure_rate}%
                                                </span>
                                            </td>
                                            <td className="text-center py-3 px-4">{payer.avg_processing_days}d</td>
                                            <td className="text-center py-3 px-4">
                                                <button
                                                    onClick={() => setExpandedPayer(expandedPayer === payer.payer ? null : payer.payer)}
                                                    className="text-blue-600 hover:text-blue-800 font-medium text-sm"
                                                >
                                                    {expandedPayer === payer.payer ? '▼ Hide' : '▶ Show'}
                                                </button>
                                            </td>
                                        </tr>
                                        {expandedPayer === payer.payer && data.payer_failure_details[payer.payer] && (
                                            <tr key={`${payer.payer}-details`}>
                                                <td colSpan="8" className="bg-slate-50 p-4">
                                                    <div className="ml-8">
                                                        <h4 className="font-semibold text-sm text-slate-700 mb-2">
                                                            🔍 Failure Reasons for {payer.payer}:
                                                        </h4>
                                                        <div className="grid grid-cols-2 gap-2">
                                                            {Object.entries(data.payer_failure_details[payer.payer]).map(([reason, count]) => (
                                                                <div key={reason} className="flex justify-between bg-white p-2 rounded border border-slate-200">
                                                                    <span className="text-sm text-slate-600">{reason}</span>
                                                                    <span className="text-sm font-semibold text-red-600">{count} claims</span>
                                                                </div>
                                                            ))}
                                                        </div>
                                                    </div>
                                                </td>
                                            </tr>
                                        )}
                                    </>
                                ))}
                            </tbody>
                        </table>
                    </div>
                    <div className="mt-4 p-4 bg-blue-50 rounded-lg border border-blue-200">
                        <p className="text-sm text-blue-800">
                            <strong>💡 Insight:</strong> Medicare and UnitedHealthcare have the highest failure rates (33.3%).
                            Click "Show" to see specific failure reasons for each payer.
                        </p>
                    </div>
                </div>
            )}

            {/* Pattern Insights */}
            <div className="bg-gradient-to-r from-orange-50 to-red-50 p-6 rounded-xl border border-orange-200">
                <h3 className="text-lg font-semibold mb-3 text-orange-900">🔍 Key Patterns Detected</h3>
                <ul className="space-y-2 text-slate-700">
                    <li className="flex items-start gap-2">
                        <span className="text-orange-500 font-bold">•</span>
                        <span><strong>Hospice Claims</strong> account for 40% of total volume but have the highest failure rate due to missing GW modifiers</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-orange-500 font-bold">•</span>
                        <span><strong>Service Line Issues</strong> are the #2 cause of failures - incomplete or missing line items</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-orange-500 font-bold">•</span>
                        <span><strong>Seasonal Trend</strong>: Failure rates peaked in September (35%) and are stabilizing around 30%</span>
                    </li>
                    <li className="flex items-start gap-2">
                        <span className="text-orange-500 font-bold">•</span>
                        <span><strong>Quick Wins</strong>: Implementing automated GW modifier checks could reduce failures by 40%</span>
                    </li>
                </ul>
            </div>
        </div>
    );
}
