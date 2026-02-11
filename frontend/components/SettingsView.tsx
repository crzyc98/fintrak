import React, { useState, useEffect } from 'react';
import {
  getUnclassifiedCount,
  triggerBatchClassification,
  getBatchProgress,
  BatchProgressResponseData,
} from '../src/services/api';

const SettingsView: React.FC = () => {
  const [unclassifiedCount, setUnclassifiedCount] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isTriggering, setIsTriggering] = useState(false);
  const [batchId, setBatchId] = useState<string | null>(null);
  const [progress, setProgress] = useState<BatchProgressResponseData | null>(null);
  const [batchSize, setBatchSize] = useState<number>(50);
  const [batchSizeError, setBatchSizeError] = useState<string | null>(null);

  useEffect(() => {
    loadUnclassifiedCount();
    checkForActiveJob();
  }, []);

  // Poll for progress when a batch is running
  useEffect(() => {
    if (!batchId) return;
    if (progress?.status === 'completed' || progress?.status === 'failed') return;

    const interval = setInterval(async () => {
      try {
        const data = await getBatchProgress(batchId);
        setProgress(data);
        if (data.status === 'completed' || data.status === 'failed') {
          loadUnclassifiedCount();
        }
      } catch {
        // Ignore polling errors
      }
    }, 2000);

    return () => clearInterval(interval);
  }, [batchId, progress?.status]);

  const loadUnclassifiedCount = async () => {
    try {
      setIsLoading(true);
      const data = await getUnclassifiedCount();
      setUnclassifiedCount(data.count);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load count');
    } finally {
      setIsLoading(false);
    }
  };

  const checkForActiveJob = async () => {
    // No server-side "list active jobs" endpoint — we only resume if we have a batchId in state
    // This is intentionally a no-op; real resume happens if user stays on page
  };

  const handleTrigger = async () => {
    setError(null);
    setIsTriggering(true);
    setProgress(null);

    try {
      const result = await triggerBatchClassification(batchSize);
      setBatchId(result.batch_id);

      if (result.status === 'completed') {
        setProgress({
          batch_id: result.batch_id,
          status: 'completed',
          total_transactions: result.total_transactions,
          processed_transactions: result.total_transactions,
          success_count: 0,
          failure_count: 0,
          skipped_count: 0,
          rule_match_count: 0,
          desc_rule_match_count: 0,
          ai_match_count: 0,
          error_message: null,
          started_at: new Date().toISOString(),
          completed_at: new Date().toISOString(),
        });
        loadUnclassifiedCount();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to trigger classification');
    } finally {
      setIsTriggering(false);
    }
  };

  const handleBatchSizeChange = (value: string) => {
    const num = parseInt(value, 10);
    if (isNaN(num)) {
      setBatchSize(50);
      setBatchSizeError(null);
      return;
    }
    setBatchSize(num);
    if (num < 10) {
      setBatchSizeError('Minimum batch size is 10');
    } else if (num > 200) {
      setBatchSizeError('Maximum batch size is 200');
    } else {
      setBatchSizeError(null);
    }
  };

  const isJobRunning = progress?.status === 'running' || isTriggering;
  const isJobDone = progress?.status === 'completed' || progress?.status === 'failed';
  const canTrigger = !isJobRunning && unclassifiedCount !== null && unclassifiedCount > 0 && !batchSizeError;

  const progressPercent = progress && progress.total_transactions > 0
    ? Math.round((progress.processed_transactions / progress.total_transactions) * 100)
    : 0;

  const duration = progress?.started_at && progress?.completed_at
    ? Math.round((new Date(progress.completed_at).getTime() - new Date(progress.started_at).getTime()) / 1000)
    : null;

  const handleRetry = () => {
    setBatchId(null);
    setProgress(null);
    setError(null);
    loadUnclassifiedCount();
  };

  return (
    <div className="max-w-2xl">
      <div className="bg-[#0a0f1d] border border-white/5 rounded-2xl p-6">
        <h2 className="text-lg font-bold text-white mb-1">Batch Classification</h2>
        <p className="text-sm text-gray-500 mb-6">
          Classify all unclassified transactions using AI and learned rules.
        </p>

        {/* Unclassified count */}
        {isLoading ? (
          <div className="text-sm text-gray-500 mb-4">Loading transaction count...</div>
        ) : error && !progress ? (
          <div className="text-sm text-red-400 mb-4">{error}</div>
        ) : (
          <div className="text-sm text-gray-300 mb-4">
            {unclassifiedCount === 0 ? (
              <span className="text-green-400">All transactions are classified.</span>
            ) : (
              <span>
                <span className="text-white font-semibold">{unclassifiedCount?.toLocaleString()}</span>{' '}
                unclassified transaction{unclassifiedCount !== 1 ? 's' : ''}
              </span>
            )}
          </div>
        )}

        {/* Batch size config */}
        <div className="mb-4">
          <label className="block text-xs font-medium text-gray-400 mb-1">
            Batch Size (transactions per AI request)
          </label>
          <input
            type="number"
            min={10}
            max={200}
            value={batchSize}
            onChange={(e) => handleBatchSizeChange(e.target.value)}
            disabled={isJobRunning}
            className="w-32 bg-[#050910] border border-white/10 rounded-lg px-3 py-1.5 text-sm text-white focus:outline-none focus:border-blue-500 disabled:opacity-50"
          />
          {batchSizeError && (
            <p className="text-xs text-red-400 mt-1">{batchSizeError}</p>
          )}
        </div>

        {/* Trigger button */}
        <button
          onClick={handleTrigger}
          disabled={!canTrigger}
          className="bg-[#3b82f6] hover:bg-[#2563eb] disabled:bg-gray-700 disabled:cursor-not-allowed px-5 py-2 rounded-xl text-xs font-bold text-white transition-all shadow-lg shadow-blue-900/10 mb-4"
        >
          {isTriggering ? 'Starting...' : isJobRunning ? 'Running...' : 'Classify All'}
        </button>

        {error && progress && (
          <div className="text-sm text-red-400 mb-4">{error}</div>
        )}

        {/* Progress bar */}
        {progress && progress.status === 'running' && (
          <div className="mt-4">
            <div className="flex justify-between text-xs text-gray-400 mb-1">
              <span>Processing...</span>
              <span>{progress.processed_transactions.toLocaleString()} / {progress.total_transactions.toLocaleString()}</span>
            </div>
            <div className="w-full bg-[#050910] rounded-full h-2 overflow-hidden">
              <div
                className="bg-blue-500 h-2 rounded-full transition-all duration-500"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
            <div className="flex gap-4 mt-2 text-xs text-gray-500">
              <span className="text-green-400">{progress.success_count} success</span>
              <span className="text-red-400">{progress.failure_count} failed</span>
              <span className="text-yellow-400">{progress.skipped_count} skipped</span>
            </div>
          </div>
        )}

        {/* Completion summary */}
        {isJobDone && progress && (
          <div className={`mt-4 p-4 rounded-xl border ${
            progress.status === 'completed' ? 'border-green-500/20 bg-green-500/5' : 'border-red-500/20 bg-red-500/5'
          }`}>
            <h3 className={`text-sm font-semibold mb-2 ${
              progress.status === 'completed' ? 'text-green-400' : 'text-red-400'
            }`}>
              {progress.status === 'completed' ? 'Classification Complete' : 'Classification Failed'}
            </h3>

            {progress.error_message && (
              <p className="text-xs text-red-400 mb-2">{progress.error_message}</p>
            )}

            <div className="grid grid-cols-2 gap-x-6 gap-y-1 text-xs">
              <div className="text-gray-400">Total processed</div>
              <div className="text-white font-medium">{progress.processed_transactions.toLocaleString()}</div>

              <div className="text-gray-400">Rule matches</div>
              <div className="text-white font-medium">{progress.rule_match_count.toLocaleString()}</div>

              <div className="text-gray-400">Description rule matches</div>
              <div className="text-white font-medium">{progress.desc_rule_match_count.toLocaleString()}</div>

              <div className="text-gray-400">AI matches</div>
              <div className="text-white font-medium">{progress.ai_match_count.toLocaleString()}</div>

              <div className="text-gray-400">Skipped</div>
              <div className="text-white font-medium">{progress.skipped_count.toLocaleString()}</div>

              <div className="text-gray-400">Failed</div>
              <div className="text-white font-medium">{progress.failure_count.toLocaleString()}</div>

              {duration !== null && (
                <>
                  <div className="text-gray-400">Duration</div>
                  <div className="text-white font-medium">{duration}s</div>
                </>
              )}
            </div>

            {/* Retry section */}
            {(progress.status === 'failed' || (unclassifiedCount !== null && unclassifiedCount > 0)) && (
              <div className="mt-3 pt-3 border-t border-white/5">
                {unclassifiedCount !== null && unclassifiedCount > 0 && (
                  <p className="text-xs text-yellow-400 mb-2">
                    {unclassifiedCount.toLocaleString()} transaction{unclassifiedCount !== 1 ? 's' : ''} still unclassified — click to retry
                  </p>
                )}
                <button
                  onClick={handleRetry}
                  className="bg-[#3b82f6] hover:bg-[#2563eb] px-4 py-1.5 rounded-lg text-xs font-bold text-white transition-all"
                >
                  Retry
                </button>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default SettingsView;
