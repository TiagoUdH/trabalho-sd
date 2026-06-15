import { useState, useRef, useCallback } from 'react';

const API_BASE = '/api';

export default function ImageUploader({ onResult, onError, onStart }) {
  const [file, setFile] = useState(null);
  const [preview, setPreview] = useState(null);
  const [loading, setLoading] = useState(false);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef(null);

  const handleFile = useCallback((f) => {
    if (!f || !f.type.startsWith('image/')) return;
    setFile(f);
    setPreview(URL.createObjectURL(f));
  }, []);

  const handleDrop = useCallback((e) => {
    e.preventDefault();
    setDragOver(false);
    handleFile(e.dataTransfer.files[0]);
  }, [handleFile]);

  const handleAnalyze = async () => {
    if (!file) return;
    setLoading(true);
    onStart();

    const formData = new FormData();
    formData.append('imagem', file);

    const t0 = performance.now();
    try {
      const res = await fetch(`${API_BASE}/analisar`, {
        method: 'POST',
        body: formData,
      });

      const data = await res.json();

      if (!res.ok && res.status !== 207) {
        throw new Error(data.erro || `Erro HTTP ${res.status}`);
      }

      onResult({ ...data, tempo_front_ms: Math.round(performance.now() - t0) });
    } catch (err) {
      onError(err.message === 'Failed to fetch'
        ? 'Não foi possível conectar ao servidor. Verifique se o backend está rodando em localhost:5000.'
        : err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = () => {
    setFile(null);
    setPreview(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  return (
    <div className="w-full max-w-2xl mx-auto">
      <div
        onDragOver={(e) => { e.preventDefault(); setDragOver(true); }}
        onDragLeave={() => setDragOver(false)}
        onDrop={handleDrop}
        onClick={() => inputRef.current?.click()}
        className={`
          relative border-2 border-dashed rounded-2xl p-10 text-center cursor-pointer
          transition-all duration-200
          ${dragOver
            ? 'border-indigo-400 bg-indigo-500/10 scale-[1.01]'
            : 'border-slate-600 hover:border-slate-500 bg-slate-800/50'}
          ${loading ? 'pointer-events-none opacity-60' : ''}
        `}
      >
        <input
          ref={inputRef}
          type="file"
          accept="image/*"
          onChange={(e) => handleFile(e.target.files[0])}
          className="hidden"
        />

        {preview ? (
          <img
            src={preview}
            alt="Preview"
            className="max-h-72 mx-auto rounded-lg shadow-lg object-contain"
          />
        ) : (
          <div className="space-y-3">
            <svg className="w-14 h-14 mx-auto text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
            </svg>
            <p className="text-slate-400 text-lg font-medium">
              Arraste uma imagem aqui ou clique para selecionar
            </p>
            <p className="text-slate-600 text-sm">PNG, JPG, BMP, WebP</p>
          </div>
        )}
      </div>

      {file && (
        <div className="flex gap-3 mt-4 justify-center">
          <button
            onClick={handleAnalyze}
            disabled={loading}
            className="px-8 py-3 bg-indigo-600 hover:bg-indigo-500 disabled:bg-indigo-800 disabled:cursor-not-allowed
                       text-white font-semibold rounded-xl transition-colors shadow-lg shadow-indigo-600/25
                       flex items-center gap-2"
          >
            {loading && (
              <svg className="animate-spin w-5 h-5" viewBox="0 0 24 24" fill="none">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
              </svg>
            )}
            {loading ? 'Analisando...' : 'Analisar Imagem'}
          </button>
          <button
            onClick={handleReset}
            disabled={loading}
            className="px-8 py-3 bg-slate-700 hover:bg-slate-600 disabled:opacity-50
                       text-slate-200 font-medium rounded-xl transition-colors border border-slate-600"
          >
            Cancelar
          </button>
        </div>
      )}
    </div>
  );
}
