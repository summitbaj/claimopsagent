import { useState, useEffect } from 'react';
import { X, Upload, FileText, Trash2, Settings } from 'lucide-react';
import axios from 'axios';

const API_URL = 'http://localhost:8000';

export default function SettingsPanel({ isOpen, onClose }) {
    const [sources, setSources] = useState([]);
    const [loading, setLoading] = useState(false);
    const [uploading, setUploading] = useState(false);
    const [selectedFiles, setSelectedFiles] = useState([]);

    useEffect(() => {
        if (isOpen) {
            loadSources();
        } else {
            // Reset loading state when closed
            setLoading(false);
        }
    }, [isOpen]);

    const loadSources = async () => {
        setLoading(true);

        // Add a timeout to prevent infinite loading
        const timeoutId = setTimeout(() => {
            console.warn('API request timed out');
            setLoading(false);
            setSources([]);
        }, 5000); // 5 second timeout

        try {
            const res = await axios.get(`${API_URL}/knowledge-sources`);
            clearTimeout(timeoutId);
            console.log('Sources loaded:', res.data);
            setSources(res.data.sources || []);
        } catch (err) {
            clearTimeout(timeoutId);
            console.error('Error loading sources:', err);
            setSources([]); // Set to empty array on error
        } finally {
            setLoading(false);
        }
    };

    const handleFileSelect = (e) => {
        const files = Array.from(e.target.files);
        setSelectedFiles(files);
    };

    const handleUpload = async () => {
        if (selectedFiles.length === 0) return;

        setUploading(true);
        const results = [];

        for (const file of selectedFiles) {
            try {
                const formData = new FormData();
                formData.append('file', file);

                const res = await axios.post(`${API_URL}/ingest`, formData, {
                    headers: { 'Content-Type': 'multipart/form-data' }
                });

                results.push({ file: file.name, success: true, data: res.data });
            } catch (err) {
                results.push({ file: file.name, success: false, error: err.message });
            }
        }

        setUploading(false);
        setSelectedFiles([]);
        loadSources();

        const successCount = results.filter(r => r.success).length;
        alert(`${successCount} of ${results.length} files uploaded successfully`);
    };

    const handleDelete = async (filename) => {
        if (!confirm(`Delete "${filename}" from knowledge base?`)) return;

        try {
            await axios.delete(`${API_URL}/knowledge-sources/${encodeURIComponent(filename)}`);
            loadSources();
        } catch (err) {
            alert(`Error deleting file: ${err.message}`);
        }
    };

    const getFileIcon = (fileType) => {
        const iconClass = "w-4 h-4";
        switch (fileType) {
            case 'pdf':
                return <FileText className={iconClass} color="#ef4444" />;
            case 'pptx':
            case 'ppt':
                return <FileText className={iconClass} color="#f97316" />;
            case 'docx':
            case 'doc':
                return <FileText className={iconClass} color="#3b82f6" />;
            default:
                return <FileText className={iconClass} />;
        }
    };

    const formatDate = (isoString) => {
        const date = new Date(isoString);
        return date.toLocaleDateString() + ' ' + date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    };

    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-xl shadow-2xl w-full max-w-3xl max-h-[90vh] flex flex-col">
                <div className="flex items-center justify-between p-6 border-b border-slate-200">
                    <div className="flex items-center gap-3">
                        <Settings className="w-6 h-6 text-slate-700" />
                        <h2 className="text-2xl font-bold text-slate-900">Knowledge Base Settings</h2>
                    </div>
                    <button onClick={onClose} className="text-slate-400 hover:text-slate-600 transition-colors">
                        <X size={24} />
                    </button>
                </div>

                <div className="p-6 border-b border-slate-200">
                    <h3 className="text-lg font-semibold text-slate-800 mb-3">Upload Knowledge Sources</h3>
                    <p className="text-sm text-slate-600 mb-4">
                        Add PowerPoint (.pptx), PDF (.pdf), or Word (.docx) files to expand the knowledge base.
                    </p>

                    <div className="flex items-center gap-3">
                        <input
                            type="file"
                            multiple
                            accept=".pptx,.ppt,.pdf,.docx,.doc"
                            onChange={handleFileSelect}
                            className="flex-1 text-sm text-slate-600 file:mr-4 file:py-2 file:px-4 file:rounded-lg file:border-0 file:text-sm file:font-semibold file:bg-blue-600 file:text-white hover:file:bg-blue-700"
                            disabled={uploading}
                        />
                        <button
                            onClick={handleUpload}
                            disabled={selectedFiles.length === 0 || uploading}
                            className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex items-center gap-2"
                        >
                            <Upload size={18} />
                            {uploading ? 'Uploading...' : `Upload ${selectedFiles.length > 0 ? `(${selectedFiles.length})` : ''}`}
                        </button>
                    </div>

                    {selectedFiles.length > 0 && (
                        <div className="mt-3 text-sm text-slate-600">
                            <span className="font-medium">Selected files:</span> {selectedFiles.map(f => f.name).join(', ')}
                        </div>
                    )}
                </div>

                <div className="flex-1 overflow-y-auto p-6">
                    <h3 className="text-lg font-semibold text-slate-800 mb-3">Uploaded Sources</h3>

                    {loading && sources.length === 0 ? (
                        <div className="text-center py-8 text-slate-500">Loading...</div>
                    ) : sources.length === 0 ? (
                        <div className="text-center py-8 text-slate-400">No files uploaded yet</div>
                    ) : (
                        <div className="space-y-2">
                            {sources.map((source, idx) => (
                                <div key={idx} className="flex items-center justify-between p-4 bg-slate-50 rounded-lg border border-slate-200 hover:border-slate-300 transition-colors">
                                    <div className="flex items-center gap-3 flex-1 min-w-0">
                                        {getFileIcon(source.file_type)}
                                        <div className="flex-1 min-w-0">
                                            <div className="font-medium text-slate-900 truncate">{source.filename}</div>
                                            <div className="text-xs text-slate-500 flex items-center gap-3">
                                                <span>{source.file_type.toUpperCase()}</span>
                                                <span>•</span>
                                                <span>{source.chunks_created} chunks</span>
                                                <span>•</span>
                                                <span>{formatDate(source.uploaded_at)}</span>
                                            </div>
                                        </div>
                                    </div>
                                    <button onClick={() => handleDelete(source.filename)} className="ml-3 p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors" title="Delete source">
                                        <Trash2 size={18} />
                                    </button>
                                </div>
                            ))}
                        </div>
                    )}
                </div>

                <div className="p-6 border-t border-slate-200 bg-slate-50">
                    <div className="flex items-center justify-between text-sm text-slate-600">
                        <span>Total sources: {sources.length}</span>
                        <button onClick={onClose} className="px-4 py-2 bg-slate-700 text-white rounded-lg hover:bg-slate-800 transition-colors">
                            Done
                        </button>
                    </div>
                </div>
            </div>
        </div>
    );
}
