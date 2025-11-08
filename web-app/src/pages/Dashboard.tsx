import { useAuth } from '@/hooks/useAuth';
import { useDashboardStats } from '@/hooks/useDashboard';
import { useScanJobs } from '@/hooks/useJobs';
import { useScanTasks, useCancelScanTask, useDeleteScanTask } from '@/hooks/useScanTasks';
import { Briefcase, CheckCircle, Clock, FileText, PlayCircle, StopCircle, Trash2 } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats(user?.id || '');
  const { data: scanTasks, isLoading: scanTasksLoading } = useScanTasks(user?.id || '', 5);
  const scanJobs = useScanJobs();
  const cancelTask = useCancelScanTask();
  const deleteTask = useDeleteScanTask();

  const [deleteConfirmId, setDeleteConfirmId] = useState<string | null>(null);

  const handleScanNow = () => {
    if (user) {
      scanJobs.mutate({
        user_id: user.id,
        scan_type: 'MANUAL',
      });
    }
  };

  const handleCancelTask = (taskId: string) => {
    cancelTask.mutate(taskId);
  };

  const handleDeleteTask = (taskId: string) => {
    if (deleteConfirmId === taskId) {
      deleteTask.mutate(taskId);
      setDeleteConfirmId(null);
    } else {
      setDeleteConfirmId(taskId);
      // Reset confirmation after 3 seconds
      setTimeout(() => setDeleteConfirmId(null), 3000);
    }
  };

  const statCards = [
    {
      name: 'Total Jobs',
      value: stats?.total_jobs || 0,
      icon: Briefcase,
      color: 'bg-blue-500',
    },
    {
      name: 'Relevant Jobs',
      value: stats?.relevant_jobs || 0,
      icon: CheckCircle,
      color: 'bg-green-500',
    },
    {
      name: 'Applications',
      value: stats?.total_applications || 0,
      icon: FileText,
      color: 'bg-purple-500',
    },
    {
      name: 'NAV Reports',
      value: stats?.nav_reports || 0,
      icon: CheckCircle,
      color: 'bg-orange-500',
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Dashboard</h1>
          <p className="text-gray-600 mt-1">
            Welcome back, {user?.user_metadata?.full_name || user?.email}!
          </p>
        </div>
        <button
          onClick={handleScanNow}
          disabled={scanJobs.isPending}
          className="flex items-center gap-2 bg-primary-600 text-white px-6 py-3 rounded-lg font-medium hover:bg-primary-700 disabled:opacity-50 transition-colors"
        >
          <PlayCircle className="w-5 h-5" />
          {scanJobs.isPending ? 'Scanning...' : 'Scan Jobs Now'}
        </button>
      </div>

      {/* Stats Cards */}
      {statsLoading ? (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {[1, 2, 3, 4].map((i) => (
            <div key={i} className="bg-white rounded-lg p-6 shadow animate-pulse">
              <div className="h-12 bg-gray-200 rounded"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          {statCards.map((stat) => (
            <div key={stat.name} className="bg-white rounded-lg p-6 shadow">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600">{stat.name}</p>
                  <p className="text-3xl font-bold text-gray-900 mt-2">{stat.value}</p>
                </div>
                <div className={`${stat.color} p-3 rounded-lg`}>
                  <stat.icon className="w-6 h-6 text-white" />
                </div>
              </div>
            </div>
          ))}
        </div>
      )}

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Scans</h2>
        </div>
        <div className="p-6">
          {scanTasksLoading ? (
            <div className="text-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            </div>
          ) : !scanTasks || scanTasks.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No recent activity. Click "Scan Jobs Now" to get started!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {scanTasks.map((task) => (
                <div
                  key={task.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
                >
                  <div className="flex-1">
                    <p className="font-medium text-gray-900">
                      {task.scan_type} Scan
                    </p>
                    <p className="text-sm text-gray-600">
                      {task.jobs_found || 0} jobs found • {task.jobs_saved || 0} saved
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(task.created_at).toLocaleString()}
                    </p>
                    {task.error_message && (
                      <p className="text-xs text-red-600 mt-1">
                        Error: {task.error_message}
                      </p>
                    )}
                    <p className="text-xs text-gray-400 mt-1 truncate max-w-md">
                      {task.url}
                    </p>
                  </div>

                  <div className="flex items-center gap-2">
                    {/* Status Badge */}
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium whitespace-nowrap ${
                        task.status === 'COMPLETED'
                          ? 'bg-green-100 text-green-800'
                          : task.status === 'FAILED'
                          ? 'bg-red-100 text-red-800'
                          : task.status === 'PROCESSING'
                          ? 'bg-blue-100 text-blue-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {task.status}
                    </span>

                    {/* Action Buttons */}
                    {(task.status === 'PENDING' || task.status === 'PROCESSING') && (
                      <button
                        onClick={() => handleCancelTask(task.id)}
                        disabled={cancelTask.isPending}
                        className="p-2 text-red-600 hover:bg-red-50 rounded-lg transition-colors disabled:opacity-50"
                        title="Cancel scan"
                      >
                        <StopCircle className="w-5 h-5" />
                      </button>
                    )}

                    {(task.status === 'COMPLETED' || task.status === 'FAILED') && (
                      <button
                        onClick={() => handleDeleteTask(task.id)}
                        disabled={deleteTask.isPending}
                        className={`p-2 rounded-lg transition-colors disabled:opacity-50 ${
                          deleteConfirmId === task.id
                            ? 'bg-red-600 text-white hover:bg-red-700'
                            : 'text-gray-600 hover:bg-gray-200'
                        }`}
                        title={deleteConfirmId === task.id ? 'Click again to confirm' : 'Delete task'}
                      >
                        <Trash2 className="w-5 h-5" />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="bg-primary-50 border border-primary-200 rounded-lg p-6">
        <h3 className="font-semibold text-primary-900 mb-4">Quick Start Guide</h3>
        <ol className="space-y-2 text-primary-800">
          <li>1. Configure your search URLs and preferences in Settings</li>
          <li>2. Upload your resume for AI analysis</li>
          <li>3. Click "Scan Jobs Now" to find relevant opportunities</li>
          <li>4. Review and approve applications in the Jobs page</li>
          <li>5. Monitor your applications in the Applications page</li>
        </ol>
      </div>
    </div>
  );
}
