import { useAuth } from '@/hooks/useAuth';
import { useActiveScanTasks, useScanTaskStats } from '@/hooks/useScanTasks';
import {
  Activity,
  CheckCircle,
  Clock,
  XCircle,
  Loader2,
  AlertCircle,
  TrendingUp
} from 'lucide-react';

export default function WorkerMonitor() {
  const { user } = useAuth();
  const { data: activeTasks, isLoading } = useActiveScanTasks(user?.id || '');
  const { data: stats } = useScanTaskStats(user?.id || '');

  if (isLoading) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex items-center justify-center">
          <Loader2 className="w-6 h-6 animate-spin text-primary-600" />
          <span className="ml-2 text-gray-600">Loading worker status...</span>
        </div>
      </div>
    );
  }

  const hasActiveTasks = activeTasks && activeTasks.length > 0;

  return (
    <div className="space-y-4">
      {/* Worker Status Card */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div className="flex items-center">
              <Activity className={`w-5 h-5 mr-2 ${hasActiveTasks ? 'text-green-600 animate-pulse' : 'text-gray-400'}`} />
              <h2 className="text-lg font-semibold text-gray-900">Worker Status</h2>
            </div>
            {hasActiveTasks ? (
              <span className="flex items-center text-sm text-green-600 font-medium">
                <span className="w-2 h-2 bg-green-600 rounded-full mr-2 animate-pulse"></span>
                Active
              </span>
            ) : (
              <span className="flex items-center text-sm text-gray-500">
                <span className="w-2 h-2 bg-gray-400 rounded-full mr-2"></span>
                Idle
              </span>
            )}
          </div>
        </div>

        <div className="p-6">
          {/* Stats Grid */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
            <div className="text-center p-4 bg-gray-50 rounded-lg">
              <div className="text-2xl font-bold text-gray-900">{stats?.total || 0}</div>
              <div className="text-sm text-gray-600">Total Tasks</div>
            </div>
            <div className="text-center p-4 bg-yellow-50 rounded-lg">
              <div className="text-2xl font-bold text-yellow-600">{stats?.pending || 0}</div>
              <div className="text-sm text-gray-600">Pending</div>
            </div>
            <div className="text-center p-4 bg-blue-50 rounded-lg">
              <div className="text-2xl font-bold text-blue-600">{stats?.processing || 0}</div>
              <div className="text-sm text-gray-600">Processing</div>
            </div>
            <div className="text-center p-4 bg-green-50 rounded-lg">
              <div className="text-2xl font-bold text-green-600">{stats?.total_jobs_saved || 0}</div>
              <div className="text-sm text-gray-600">Jobs Found</div>
            </div>
          </div>

          {/* Active Tasks */}
          {hasActiveTasks ? (
            <div className="space-y-3">
              <h3 className="text-sm font-medium text-gray-700 flex items-center">
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                Active Scans
              </h3>
              {activeTasks.map((task) => (
                <div
                  key={task.id}
                  className="border border-gray-200 rounded-lg p-4 bg-gradient-to-r from-blue-50 to-white"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center mb-2">
                        <span
                          className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            task.source === 'FINN'
                              ? 'bg-purple-100 text-purple-800'
                              : 'bg-blue-100 text-blue-800'
                          }`}
                        >
                          {task.source}
                        </span>
                        <span
                          className={`ml-2 inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                            task.status === 'PROCESSING'
                              ? 'bg-blue-100 text-blue-800'
                              : 'bg-yellow-100 text-yellow-800'
                          }`}
                        >
                          {task.status === 'PROCESSING' ? (
                            <>
                              <Loader2 className="w-3 h-3 mr-1 animate-spin" />
                              Processing
                            </>
                          ) : (
                            <>
                              <Clock className="w-3 h-3 mr-1" />
                              Pending
                            </>
                          )}
                        </span>
                      </div>
                      <p className="text-sm text-gray-600 truncate" title={task.url}>
                        {task.url}
                      </p>
                      <div className="flex items-center mt-2 text-xs text-gray-500">
                        {task.worker_id && (
                          <span className="flex items-center mr-4">
                            <Activity className="w-3 h-3 mr-1" />
                            Worker: {task.worker_id.substring(0, 8)}...
                          </span>
                        )}
                        {task.jobs_found > 0 && (
                          <span className="flex items-center">
                            <TrendingUp className="w-3 h-3 mr-1 text-green-600" />
                            {task.jobs_found} jobs found
                          </span>
                        )}
                      </div>
                    </div>
                    <div className="ml-4">
                      {task.status === 'PROCESSING' && (
                        <div className="relative w-12 h-12">
                          <svg className="transform -rotate-90 w-12 h-12">
                            <circle
                              cx="24"
                              cy="24"
                              r="20"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="transparent"
                              className="text-gray-200"
                            />
                            <circle
                              cx="24"
                              cy="24"
                              r="20"
                              stroke="currentColor"
                              strokeWidth="4"
                              fill="transparent"
                              strokeDasharray="125.6"
                              strokeDashoffset="31.4"
                              className="text-blue-600 animate-pulse"
                            />
                          </svg>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p className="text-sm">Worker is idle. No active scans.</p>
              <p className="text-xs mt-1">Click "Scan Jobs Now" to start scanning</p>
            </div>
          )}

          {/* Recent Activity Summary */}
          {stats && (stats.completed > 0 || stats.failed > 0) && (
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-medium text-gray-700 mb-3">Recent Activity</h3>
              <div className="flex items-center justify-around text-sm">
                <div className="flex items-center">
                  <CheckCircle className="w-4 h-4 text-green-600 mr-2" />
                  <span className="text-gray-600">
                    {stats.completed} completed
                  </span>
                </div>
                {stats.failed > 0 && (
                  <div className="flex items-center">
                    <XCircle className="w-4 h-4 text-red-600 mr-2" />
                    <span className="text-gray-600">
                      {stats.failed} failed
                    </span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Tips Card */}
      {!hasActiveTasks && (!stats || stats.total === 0) && (
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start">
            <AlertCircle className="w-5 h-5 text-blue-600 mr-3 mt-0.5" />
            <div>
              <h3 className="text-sm font-medium text-blue-900">How to use the Worker</h3>
              <ul className="mt-2 text-sm text-blue-800 space-y-1">
                <li>1. Add search URLs in Settings (FINN.no or NAV.no)</li>
                <li>2. Click "Scan Jobs Now" to start</li>
                <li>3. Worker will automatically scan and save jobs</li>
                <li>4. Monitor progress here in real-time</li>
              </ul>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
