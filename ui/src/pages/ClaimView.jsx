import { useState } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle, ArrowRight } from 'lucide-react';
import clsx from 'clsx';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

const API_URL = 'http://localhost:8000';

export default function ClaimView() {
    const [claimId, setClaimId] = useState('');
    const [prediction, setPrediction] = useState(null);
    const [correction, setCorrection] = useState(null);
    const [loading, setLoading] = useState(false);

    const { instance, accounts } = useMsal();

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

    const handlePredict = async () => {
        setLoading(true);
        setPrediction(null);
        setCorrection(null);
        try {
            const token = await getToken();
            const res = await axios.post(
                `${API_URL}/predict`,
                { claim_id: claimId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setPrediction(res.data);
        } catch (err) {
            alert('Prediction failed: ' + (err.response?.data?.detail || err.message));
        } finally {
            setLoading(false);
        }
    };

    const handleCorrect = async () => {
        try {
            const token = await getToken();
            const res = await axios.post(
                `${API_URL}/correct`,
                { claim_id: claimId },
                { headers: { Authorization: `Bearer ${token}` } }
            );
            setCorrection(res.data);
        } catch (err) {
            alert('Correction failed');
        }
    };

    return (
        <div className="max-w-4xl mx-auto space-y-8">
            <div>
                <h2 className="text-3xl font-bold mb-2">Claim Analysis</h2>
                <p className="text-slate-500">Predict outcomes and apply auto-corrections.</p>
            </div>

            {/* Input Section */}
            <div className="flex gap-4">
                <input
                    type="text"
                    value={claimId}
                    onChange={(e) => setClaimId(e.target.value)}
                    placeholder="Enter Claim ID (e.g. H-10023)"
                    className="flex-1 p-3 border rounded-lg shadow-sm focus:ring-2 focus:ring-blue-500 outline-none"
                />
                <button
                    onClick={handlePredict}
                    disabled={loading || !claimId}
                    className="bg-blue-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50"
                >
                    {loading ? 'Analyzing...' : 'Analyze Claim'}
                </button>
            </div>

            {/* Prediction Results */}
            {prediction && (
                <div className="grid gap-6 animate-in fade-in slide-in-from-bottom-4">
                    <div className={clsx(
                        "p-6 rounded-xl border-l-4 shadow-sm",
                        prediction.prediction === 'FAIL' ? "bg-red-50 border-red-500" : "bg-green-50 border-green-500"
                    )}>
                        <div className="flex items-center gap-3 mb-4">
                            {prediction.prediction === 'FAIL' ? <AlertCircle className="text-red-500" size={32} /> : <CheckCircle className="text-green-500" size={32} />}
                            <div>
                                <h3 className="text-xl font-bold text-slate-900">Prediction: {prediction.prediction}</h3>
                                <p className="text-slate-600">Confidence: {(prediction.confidence_score * 100).toFixed(1)}%</p>
                            </div>
                        </div>

                        {prediction.top_reasons?.length > 0 && (
                            <div className="mt-4">
                                <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500 mb-2">Risk Factors</h4>
                                <ul className="list-disc list-inside space-y-1 text-slate-700">
                                    {prediction.top_reasons.map((r, i) => <li key={i}>{r}</li>)}
                                </ul>
                            </div>
                        )}
                    </div>

                    {/* Correction Action */}
                    {prediction.prediction === 'FAIL' && (
                        <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                            <div>
                                <h3 className="font-semibold text-lg">Auto-Correction Available</h3>
                                <p className="text-slate-500 text-sm">Apply known rules to fix specific issues found in this claim.</p>
                            </div>
                            <button
                                onClick={handleCorrect}
                                className="flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-lg hover:bg-slate-800"
                            >
                                Apply Fixes <ArrowRight size={18} />
                            </button>
                        </div>
                    )}
                </div>
            )}

            {/* Correction Results */}
            {correction && (
                <div className="bg-slate-50 p-6 rounded-xl border border-slate-200 animate-in fade-in">
                    <h3 className="font-bold text-lg mb-4">Correction Report</h3>
                    <div className="space-y-3">
                        {correction.applied_corrections.map((c, i) => (
                            <div key={i} className="flex items-start gap-3 bg-white p-4 rounded border border-slate-100">
                                <div className="bg-green-100 text-green-700 px-2 py-0.5 rounded text-xs font-bold mt-1">
                                    {c.status}
                                </div>
                                <div>
                                    <p className="font-medium text-slate-900">{c.rule_id}</p>
                                    <p className="text-slate-600 text-sm">{c.description}</p>
                                </div>
                            </div>
                        ))}
                        {correction.applied_corrections.length === 0 && (
                            <p className="text-slate-500 italic">No applicable rules found for this claim.</p>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
}
