import React, { useState } from 'react';
import { useMsal } from "@azure/msal-react";
import { loginRequest } from "../authConfig";

const API_URL = 'http://localhost:8000';

/**
 * Custom Prediction Criteria UI Component
 * Allows users to define their own prediction criteria
 */
export default function CustomPredictionPanel({ onPredict }) {
  const { instance, accounts } = useMsal();
  const [claimId, setClaimId] = useState('');
  const [criteria, setCriteria] = useState({
    focus_areas: ['procedure codes', 'modifiers', 'amounts'],
    similarity_rules: 'Same status and similar amount range (+/- 50%)',
    risk_factors: ['missing modifiers', 'invalid procedure codes', 'amount thresholds'],
    comparison_context: 'Compare with claims from last 30 days'
  });
  
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);

  // Predefined templates
  const templates = {
    default: {
      focus_areas: ['procedure codes', 'modifiers', 'amounts'],
      similarity_rules: 'Same status and similar amount range (+/- 50%)',
      risk_factors: ['missing modifiers', 'invalid procedure codes', 'amount thresholds'],
      comparison_context: 'Compare with claims from last 30 days'
    },
    strict: {
      focus_areas: ['procedure codes', 'modifiers', 'amounts', 'diagnosis codes', 'place of service'],
      similarity_rules: 'Exact status match and amount within 25%',
      risk_factors: ['missing modifiers', 'invalid procedure codes', 'amount thresholds', 'diagnosis mismatches', 'invalid place of service'],
      comparison_context: 'Compare with claims from last 7 days only'
    },
    lenient: {
      focus_areas: ['amounts', 'status'],
      similarity_rules: 'Any status and amount within 100%',
      risk_factors: ['major code errors only'],
      comparison_context: 'Compare with claims from last 90 days'
    }
  };

  const handleTemplateSelect = (templateName) => {
    setCriteria(templates[templateName]);
  };

  const handleFocusAreaToggle = (area) => {
    setCriteria(prev => ({
      ...prev,
      focus_areas: prev.focus_areas.includes(area)
        ? prev.focus_areas.filter(a => a !== area)
        : [...prev.focus_areas, area]
    }));
  };

  const handleRiskFactorToggle = (factor) => {
    setCriteria(prev => ({
      ...prev,
      risk_factors: prev.risk_factors.includes(factor)
        ? prev.risk_factors.filter(f => f !== factor)
        : [...prev.risk_factors, factor]
    }));
  };

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
    if (!claimId.trim()) {
      alert('Please enter a claim ID');
      return;
    }

    setLoading(true);
    setResult(null);

    try {
      const token = await getToken();
      const response = await fetch(`${API_URL}/predict-custom`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${token}`
        },
        body: JSON.stringify({
          claim_id: claimId,
          ...criteria
        })
      });

      const data = await response.json();
      setResult(data);
      
      if (onPredict) {
        onPredict(data);
      }
    } catch (error) {
      console.error('Prediction error:', error);
      setResult({ error: error.message });
    } finally {
      setLoading(false);
    }
  };

  const focusAreaOptions = [
    'procedure codes',
    'modifiers',
    'amounts',
    'diagnosis codes',
    'place of service',
    'units/days',
    'dates of service'
  ];

  const riskFactorOptions = [
    'missing modifiers',
    'invalid procedure codes',
    'amount thresholds',
    'diagnosis mismatches',
    'invalid place of service',
    'duplicate service lines',
    'date range issues'
  ];

  return (
    <div className="max-w-4xl mx-auto p-6 space-y-6">
      <div className="bg-white rounded-lg shadow-md p-6">
        <h2 className="text-2xl font-bold mb-4">Custom Claim Prediction</h2>
        <p className="text-gray-600 mb-6">
          Define your own criteria for claim analysis and prediction
        </p>

        {/* Claim ID Input */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Claim ID</label>
          <input
            type="text"
            value={claimId}
            onChange={(e) => setClaimId(e.target.value)}
            className="w-full px-4 py-2 border rounded-md"
            placeholder="Enter claim ID..."
          />
        </div>

        {/* Templates */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Quick Templates</label>
          <div className="flex gap-2">
            <button
              onClick={() => handleTemplateSelect('default')}
              className="px-4 py-2 bg-blue-500 text-white rounded hover:bg-blue-600"
            >
              Default
            </button>
            <button
              onClick={() => handleTemplateSelect('strict')}
              className="px-4 py-2 bg-red-500 text-white rounded hover:bg-red-600"
            >
              Strict
            </button>
            <button
              onClick={() => handleTemplateSelect('lenient')}
              className="px-4 py-2 bg-green-500 text-white rounded hover:bg-green-600"
            >
              Lenient
            </button>
          </div>
        </div>

        {/* Focus Areas */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Focus Areas</label>
          <p className="text-xs text-gray-500 mb-2">What aspects should the AI analyze?</p>
          <div className="flex flex-wrap gap-2">
            {focusAreaOptions.map(area => (
              <button
                key={area}
                onClick={() => handleFocusAreaToggle(area)}
                className={`px-3 py-1 rounded-full text-sm ${
                  criteria.focus_areas.includes(area)
                    ? 'bg-blue-500 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                {area}
              </button>
            ))}
          </div>
        </div>

        {/* Similarity Rules */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Similarity Rules</label>
          <p className="text-xs text-gray-500 mb-2">How to identify similar claims for comparison</p>
          <textarea
            value={criteria.similarity_rules}
            onChange={(e) => setCriteria({ ...criteria, similarity_rules: e.target.value })}
            className="w-full px-4 py-2 border rounded-md"
            rows={2}
            placeholder="e.g., Same status and similar amount range (+/- 50%)"
          />
        </div>

        {/* Risk Factors */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Risk Factors to Check</label>
          <p className="text-xs text-gray-500 mb-2">What should be flagged as potential issues?</p>
          <div className="flex flex-wrap gap-2">
            {riskFactorOptions.map(factor => (
              <button
                key={factor}
                onClick={() => handleRiskFactorToggle(factor)}
                className={`px-3 py-1 rounded-full text-sm ${
                  criteria.risk_factors.includes(factor)
                    ? 'bg-red-500 text-white'
                    : 'bg-gray-200 text-gray-700'
                }`}
              >
                {factor}
              </button>
            ))}
          </div>
        </div>

        {/* Comparison Context */}
        <div className="mb-6">
          <label className="block text-sm font-medium mb-2">Comparison Context</label>
          <p className="text-xs text-gray-500 mb-2">Timeframe and scope for historical comparison</p>
          <input
            type="text"
            value={criteria.comparison_context}
            onChange={(e) => setCriteria({ ...criteria, comparison_context: e.target.value })}
            className="w-full px-4 py-2 border rounded-md"
            placeholder="e.g., Compare with claims from last 30 days"
          />
        </div>

        {/* Predict Button */}
        <button
          onClick={handlePredict}
          disabled={loading}
          className="w-full py-3 bg-indigo-600 text-white rounded-md hover:bg-indigo-700 disabled:bg-gray-400"
        >
          {loading ? 'Analyzing...' : 'Predict with Custom Criteria'}
        </button>
      </div>

      {/* Results Display */}
      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          <h3 className="text-xl font-bold mb-4">Prediction Results</h3>
          
          {result.error ? (
            <div className="bg-red-50 border border-red-200 rounded p-4 text-red-700">
              Error: {result.error}
            </div>
          ) : (
            <div className="space-y-4">
              {/* Prediction */}
              <div className={`p-4 rounded-lg ${
                result.prediction === 'FAIL' ? 'bg-red-50 border border-red-200' : 'bg-green-50 border border-green-200'
              }`}>
                <div className="flex justify-between items-center">
                  <span className="text-lg font-bold">Prediction: {result.prediction}</span>
                  <span className="text-sm">Confidence: {(result.confidence_score * 100).toFixed(1)}%</span>
                </div>
              </div>

              {/* Top Reasons */}
              <div>
                <h4 className="font-semibold mb-2">Top Reasons</h4>
                <ul className="list-disc list-inside space-y-1">
                  {result.top_reasons?.map((reason, idx) => (
                    <li key={idx} className="text-gray-700">{reason}</li>
                  ))}
                </ul>
              </div>

              {/* Risk Factors */}
              {result.risk_factors_found?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Risk Factors Found</h4>
                  <div className="space-y-2">
                    {result.risk_factors_found.map((risk, idx) => (
                      <div key={idx} className="bg-yellow-50 border border-yellow-200 rounded p-3">
                        <div className="flex justify-between items-start">
                          <span className="font-medium">{risk.factor}</span>
                          <span className={`text-xs px-2 py-1 rounded ${
                            risk.severity === 'HIGH' ? 'bg-red-500 text-white' :
                            risk.severity === 'MEDIUM' ? 'bg-orange-500 text-white' :
                            'bg-yellow-500 text-white'
                          }`}>
                            {risk.severity}
                          </span>
                        </div>
                        <p className="text-sm text-gray-600 mt-1">{risk.details}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Similar Claims */}
              {result.similar_claims?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Similar Claims Analyzed</h4>
                  <p className="text-sm text-gray-600 mb-2">{result.similarity_explanation}</p>
                  <div className="space-y-2">
                    {result.similar_claims.map((claim, idx) => (
                      <div key={idx} className="bg-gray-50 border rounded p-3">
                        <div className="flex justify-between">
                          <span className="font-mono text-sm">{claim.claim_id}</span>
                          <span className={`font-semibold ${
                            claim.outcome === 'FAIL' ? 'text-red-600' : 'text-green-600'
                          }`}>
                            {claim.outcome}
                          </span>
                        </div>
                        {claim.reason && (
                          <p className="text-sm text-gray-600 mt-1">{claim.reason}</p>
                        )}
                        {claim.similarity_score && (
                          <p className="text-xs text-gray-500 mt-1">
                            Similarity: {(claim.similarity_score * 100).toFixed(1)}%
                          </p>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Criteria Applied */}
              {result.criteria_applied && (
                <div className="bg-blue-50 border border-blue-200 rounded p-4">
                  <h4 className="font-semibold mb-2">Criteria Applied</h4>
                  <div className="text-sm space-y-1">
                    <p><strong>Focus Areas:</strong> {result.criteria_applied.focus_areas?.join(', ')}</p>
                    <p><strong>Similarity Rules:</strong> {result.criteria_applied.similarity_rules}</p>
                  </div>
                </div>
              )}

              {/* Focus Areas Analysis */}
              {result.focus_areas_analyzed?.length > 0 && (
                <div>
                  <h4 className="font-semibold mb-2">Focus Area Analysis</h4>
                  <div className="space-y-2">
                    {result.focus_areas_analyzed.map((analysis, idx) => (
                      <div key={idx} className="bg-gray-50 border rounded p-3">
                        <p className="font-medium">{analysis.area}</p>
                        <p className="text-sm text-gray-600">{analysis.finding}</p>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
