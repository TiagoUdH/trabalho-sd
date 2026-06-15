import { useState, useEffect } from 'react';

const API_BASE = '/api';

function formatTime(ms) {
  if (ms < 1000) return `${ms} ms`;
  return `${(ms / 1000).toFixed(2)} s`;
}

export default function ResultViewer({ result, requestId }) {
  const [imageLoaded, setImageLoaded] = useState(false);
  const [imageError, setImageError] = useState(false);

  const imageUrl = `${API_BASE}/resultado/${requestId}/imagem`;

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6">
      {/* Verdict Banner */}
      <div className={`
        rounded-xl p-6 text-center border-2 transition-all
        ${result.encontrou_vermelho
          ? 'bg-red-500/10 border-red-500/30'
          : 'bg-emerald-500/10 border-emerald-500/30'}
      `}>
        <div className={`
          text-3xl font-bold mb-2
          ${result.encontrou_vermelho ? 'text-red-400' : 'text-emerald-400'}
        `}>
          {result.encontrou_vermelho ? 'Vermelho Detectado' : 'Nenhum Vermelho'}
        </div>
        <p className="text-slate-300 text-lg">{result.conclusao_final}</p>
      </div>

      {/* Time */}
      <div className="flex justify-center gap-8 text-sm text-slate-400">
        <div className="text-center">
          <span className="block text-2xl font-mono text-white">{formatTime(result.tempo_ms)}</span>
          <span>Tempo servidor</span>
        </div>
        <div className="text-center">
          <span className="block text-2xl font-mono text-white">{formatTime(result.tempo_front_ms)}</span>
          <span>Tempo total (round-trip)</span>
        </div>
        <div className="text-center">
          <span className="block text-2xl font-mono text-white">{result.fatias_processadas}</span>
          <span>Fatias processadas</span>
        </div>
      </div>

      {/* Visual Log Image */}
      <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
        <div className="px-4 py-3 bg-slate-800 border-b border-slate-700">
          <h3 className="text-slate-300 font-medium text-sm">Log Visual — Fatias Anotadas</h3>
        </div>
        <div className="p-4">
          {!imageError ? (
            <>
              {!imageLoaded && (
                <div className="flex items-center justify-center h-48 text-slate-500">
                  <svg className="animate-spin w-6 h-6 mr-2" viewBox="0 0 24 24" fill="none">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                    <path className="opacity-75" fill="currentColor"
                      d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z" />
                  </svg>
                  Carregando imagem...
                </div>
              )}
              <img
                src={imageUrl}
                alt="Resultado visual com fatias anotadas"
                onLoad={() => setImageLoaded(true)}
                onError={() => setImageError(true)}
                className={`w-full rounded-lg ${imageLoaded ? 'block' : 'hidden'}`}
              />
            </>
          ) : (
            <p className="text-slate-500 text-center py-8">
              Imagem de resultado não disponível
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
