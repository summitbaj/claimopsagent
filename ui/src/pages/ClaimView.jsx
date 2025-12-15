
import { useState } from 'react';
import axios from 'axios';
import { AlertCircle, CheckCircle, ArrowRight, Sliders } from 'lucide-react';
import clsx from 'clsx';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";
import CustomPredictionPanel from '../components/CustomPredictionPanel';

const API_URL = 'http://localhost:8000';

export default function ClaimView() {
    const [claimId, setClaimId] = useState('');
    const [prediction, setPrediction] = useState(null);
    const [correction, setCorrection] = useState(null);
    const [loading, setLoading] = useState(false);
    const [activeTab, setActiveTab] = useState('standard');

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

            <div className="flex gap-2 border-b border-slate-200">
                <button
                    onClick={() => setActiveTab('standard')}
                    className={clsx(
                        "px-4 py-2 font-medium border-b-2 transition-colors",
                        activeTab === 'standard' ? "border-blue-600 text-blue-600" : "border-transparent text-slate-600 hover:text-slate-900"
                    )}
                >
                    Standard Prediction
                </button>
                <button
                    onClick={() => setActiveTab('custom')}
                    className={clsx(
                        "px-4 py-2 font-medium border-b-2 transition-colors flex items-center gap-2",
                        activeTab === 'custom' ? "border-blue-600 text-blue-600" : "border-transparent text-slate-600 hover:text-slate-900"
                    )}
                >
                    <Sliders size={16} />
                    Custom Criteria
                </button>
            </div>

            {activeTab === 'standard' && (
                <>
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

                                {/* AI Rationale */}
                                {prediction.rationale && (
                                    <div className="mb-6 bg-white/50 p-4 rounded-lg border border-slate-200/50">
                                        <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500 mb-2 flex items-center gap-2">
                                            <span className="text-lg">🧠</span> AI Rationale
                                        </h4>
                                        <p className="text-slate-800 leading-relaxed">{prediction.rationale}</p>
                                    </div>
                                )}

                                {/* Chain of Thought / Reasoning Trace */}
                                {prediction.reasoning_trace && prediction.reasoning_trace.length > 0 && (
                                    <div className="mb-6">
                                        <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500 mb-2">Analysis Trace</h4>
                                        <div className="space-y-2 bg-slate-100 p-3 rounded-lg text-sm text-slate-700 max-h-48 overflow-y-auto">
                                            {prediction.reasoning_trace.map((step, i) => (
                                                <div key={i} className="flex gap-2">
                                                    <span className="text-slate-400 font-mono text-xs pt-0.5">{i + 1}.</span>
                                                    <span>{step}</span>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                )}

                                {prediction.top_reasons?.length > 0 && (
                                    <div className="mt-4">
                                        <h4 className="font-semibold text-sm uppercase tracking-wide text-slate-500 mb-2">Risk Factors</h4>
                                        <ul className="list-disc list-inside space-y-1 text-slate-700">
                                            {prediction.top_reasons.map((r, i) => <li key={i}>{r}</li>)}
                                        </ul>
                                    </div>
                                )}

                                {prediction.limitations && (
                                    <div className="mt-4 text-xs text-slate-500 italic border-t pt-2 border-slate-200">
                                        Note: {prediction.limitations}
                                    </div>
                                )}
                            </div>

                            {prediction.claim_details && Object.keys(prediction.claim_details).length > 0 && (
                                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                                    <h3 className="text-lg font-bold mb-4">Claim Details</h3>
                                    <div className="grid grid-cols-2 md:grid-cols-3 gap-4 text-sm">
                                        <div>
                                            <p className="text-slate-500">Claim ID</p>
                                            <p className="font-medium">{prediction.claim_details.smvs_claimid}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Patient Name</p>
                                            <p className="font-medium">{prediction.claim_details['patient.fullname'] || prediction.claim_details['patient.fullname@OData.Community.Display.V1.FormattedValue'] || prediction.claim_details.fullname}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Insurance</p>
                                            <p className="font-medium">{prediction.claim_details['insurance.smvs_health_insurance_company@OData.Community.Display.V1.FormattedValue'] || prediction.claim_details['insurance.smvs_health_insurance_company'] || 'N/A'}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Insurance Type</p>
                                            <p className="font-medium">{prediction.claim_details['insurance.smvs_insurance_type@OData.Community.Display.V1.FormattedValue'] || prediction.claim_details['insurance.smvs_insurance_type'] || '-'}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Status</p>
                                            <p className="font-medium">{prediction.claim_details.smvs_claimstatus}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Claimed Amount</p>
                                            <p className="font-medium">${prediction.claim_details.smvs_claimed_amount}</p>
                                        </div>
                                        <div>
                                            <p className="text-slate-500">Received Amount</p>
                                            <p className="font-medium">${prediction.claim_details.smvs_recieved_amount}</p>
                                        </div>
                                    </div>
                                    <div className="mt-4 text-xs text-slate-400">
                                        Created: {new Date(prediction.claim_details.createdon).toLocaleDateString()}
                                    </div>
                                </div>
                            )}

                            {prediction.service_lines && prediction.service_lines.length > 0 && (
                                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                                    <h3 className="text-lg font-bold mb-4">Service Lines</h3>
                                    <div className="overflow-x-auto">
                                        <table className="w-full text-sm text-left">
                                            <thead className="text-xs uppercase bg-slate-50 text-slate-500">
                                                <tr>
                                                    <th className="px-4 py-2">Service</th>
                                                    <th className="px-4 py-2">Description</th>
                                                    <th className="px-4 py-2">Code</th>
                                                    <th className="px-4 py-2">Modifiers</th>
                                                    <th className="px-4 py-2">Charges</th>
                                                    <th className="px-4 py-2">Date</th>
                                                </tr>
                                            </thead>
                                            <tbody className="divide-y divide-slate-100">
                                                {prediction.service_lines.map((line, i) => (
                                                    <tr key={i} className="hover:bg-slate-50">
                                                        <td className="px-4 py-2 font-medium">{line.smvs_name}</td>
                                                        <td className="px-4 py-2 text-slate-600">{line['cpt.smvs_description'] || '-'}</td>
                                                        <td className="px-4 py-2">{line.smvs_proceduresservicesorsupplies}</td>
                                                        <td className="px-4 py-2">{line.smvs_modifiers}</td>
                                                        <td className="px-4 py-2">${line.smvs_charges}</td>
                                                        <td className="px-4 py-2">{line.smvs_datesofservice}</td>
                                                    </tr>
                                                ))}
                                            </tbody>
                                        </table>
                                    </div>
                                </div>
                            )}

                            {prediction.similar_claims_data && prediction.similar_claims_data.length > 0 && (
                                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm">
                                    <h3 className="text-lg font-bold mb-4">Similar Claims Context</h3>
                                    <div className="space-y-3">
                                        {prediction.similar_claims_data.map((claim, i) => (
                                            <div key={i} className="flex justify-between items-start p-3 bg-slate-50 rounded text-sm">
                                                <div>
                                                    <div className="font-medium flex items-center gap-2">
                                                        {claim.smvs_claimid}
                                                        <span className="text-xs font-normal text-slate-500 px-2 py-0.5 bg-white rounded border">
                                                            {claim['patient.fullname'] || claim['patient.fullname@OData.Community.Display.V1.FormattedValue'] || 'Unknown Patient'}
                                                        </span>
                                                    </div>
                                                    <p className="text-slate-500 text-xs mt-1">
                                                        {claim.smvs_claimstatus} • {claim.smvs_claim_type}
                                                    </p>
                                                    <p className="text-slate-500 text-xs">
                                                        {claim['insurance.smvs_health_insurance_company@OData.Community.Display.V1.FormattedValue'] || 'No Insurance'}
                                                        {claim['insurance.smvs_insurance_type@OData.Community.Display.V1.FormattedValue'] && ` • ${claim['insurance.smvs_insurance_type@OData.Community.Display.V1.FormattedValue']}`}
                                                    </p>
                                                </div>
                                                <div className="text-right">
                                                    <p className="font-medium">${claim.smvs_claimed_amount}</p>
                                                    <p className="text-slate-500 text-xs">{new Date(claim.createdon).toLocaleDateString()}</p>
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {prediction.prediction === 'FAIL' && (
                                <div className="bg-white p-6 rounded-xl border border-slate-200 shadow-sm flex items-center justify-between">
                                    <div>
                                        <h3 className="font-semibold text-lg">Auto-Correction Available</h3>
                                        <p className="text-slate-500 text-sm">Apply known rules to fix specific issues found in this claim.</p>
                                    </div>
                                    <button onClick={handleCorrect} className="flex items-center gap-2 bg-slate-900 text-white px-5 py-2.5 rounded-lg hover:bg-slate-800">
                                        Apply Fixes <ArrowRight size={18} />
                                    </button>
                                </div>
                            )}
                        </div>
                    )}

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
                </>
            )}

            {activeTab === 'custom' && (
                <CustomPredictionPanel />
            )}
        </div>
    );
}
