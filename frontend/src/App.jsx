import { useState } from 'react';
import ImageUploader from './components/ImageUploader';
import ResultViewer from './components/ResultViewer';
import SliceTable from './components/SliceTable';
import WorkerLoad from './components/WorkerLoad';

export default function App() {
  const [state, setState] = useState('idle'); // idle | processing | done | error
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  return (
    <div className="min-h-screen flex flex-col">
      {/* Header */}
      <header className="border-b border-slate-800 bg-slate-900/50 backdrop-blur-sm">
        <div className="max-w-5xl mx-auto px-4 py-4 flex items-center gap-3">
          <div className="w-8 h-8 rounded-lg bg-indigo-600 flex items-center justify-center">
            <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
            </svg>
          </div>
          <div>
            <h1 className="text-xl font-bold text-white">Detector de Vermelho</h1>
            <p className="text-xs text-slate-500">Sistema Distribuído — Análise paralela de imagem</p>
          </div>
        </div>
      </header>

      {/* Main */}
      <main className="flex-1 py-10 px-4 space-y-8">
        {state !== 'done' && state !== 'processing' && (
          <div className="text-center mb-6">
            <h2 className="text-3xl font-bold text-white mb-2">
              Analisar Imagem
            </h2>
            <p className="text-slate-400 max-w-md mx-auto">
              Envie uma imagem e o sistema distribuirá a análise entre múltiplos workers detectando a presença da cor vermelha.
            </p>
          </div>
        )}

        {/* Processing State */}
        {state === 'processing' && (
          <div className="flex flex-col items-center justify-center py-20 space-y-6">
            <div className="relative">
              <div className="w-20 h-20 border-4 border-slate-700 rounded-full" />
              <div className="absolute inset-0 w-20 h-20 border-4 border-transparent border-t-indigo-500 rounded-full animate-spin" />
            </div>
            <div className="text-center space-y-1">
              <p className="text-xl font-medium text-white">Analisando imagem...</p>
              <p className="text-slate-500 text-sm">
                Distribuindo fatias para os workers e aguardando resultados
              </p>
            </div>
          </div>
        )}

        {/* Done State */}
        {state === 'done' && result && (
          <div className="space-y-8 pb-12">
            <ResultViewer result={result} requestId={result.request_id} />
            <SliceTable detalhes={result.detalhes_por_fatia} falhas={result.fatias_com_falha} />
            <WorkerLoad carga={result.carga_por_no} />

            <div className="text-center">
              <button
                onClick={() => { setState('idle'); setResult(null); setError(null); }}
                className="px-6 py-3 bg-slate-700 hover:bg-slate-600 text-slate-200 font-medium
                           rounded-xl transition-colors border border-slate-600"
              >
                Nova Análise
              </button>
            </div>
          </div>
        )}

        {/* Error State */}
        {state === 'error' && (
          <div className="max-w-xl mx-auto">
            <div className="bg-red-500/10 border border-red-500/30 rounded-xl p-6 text-center">
              <svg className="w-10 h-10 text-red-400 mx-auto mb-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5}
                  d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4.5c-.77-.833-2.694-.833-3.464 0L3.34 16.5c-.77.833.192 2.5 1.732 2.5z" />
              </svg>
              <p className="text-red-400 font-medium mb-1">Erro na análise</p>
              <p className="text-slate-300 text-sm mb-4">{error}</p>
              <button
                onClick={() => { setState('idle'); setResult(null); setError(null); }}
                className="px-6 py-2 bg-red-600 hover:bg-red-500 text-white text-sm font-medium
                           rounded-lg transition-colors"
              >
                Tentar novamente
              </button>
            </div>
          </div>
        )}

        {/* Idle State */}
        {state === 'idle' && (
          <ImageUploader
            onStart={() => { setState('processing'); setError(null); setResult(null); }}
            onResult={(data) => { setResult(data); setState('done'); }}
            onError={(msg) => { setError(msg); setState('error'); }}
          />
        )}
      </main>

      {/* Footer */}
      <footer className="border-t border-slate-800 py-4 text-center text-xs text-slate-600">
        Sistema Distribuído — Detector de Vermelho com Master/Worker + RabbitMQ
      </footer>
    </div>
  );
}
