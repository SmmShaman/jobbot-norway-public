import { useAuth } from '@/hooks/useAuth';
import { useDashboardStats, useMonitoringLogs } from '@/hooks/useDashboard';
import { useScanJobs } from '@/hooks/useJobs';
import { Briefcase, CheckCircle, Clock, FileText, PlayCircle } from 'lucide-react';
import WorkerMonitor from '@/components/WorkerMonitor';

export default function Dashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats(user?.id || '');
  const { data: logs } = useMonitoringLogs(user?.id || '', 5);
  const scanJobs = useScanJobs();

  const handleScanNow = () => {
    if (user) {
      scanJobs.mutate({
        user_id: user.id,
        scan_type: 'MANUAL',
      });
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

      {/* Worker Monitor */}
      <WorkerMonitor />

      {/* Recent Activity */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-lg font-semibold text-gray-900">Recent Scans</h2>
        </div>
        <div className="p-6">
          {!logs || logs.length === 0 ? (
            <div className="text-center py-8 text-gray-500">
              <Clock className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No recent activity. Click "Scan Jobs Now" to get started!</p>
            </div>
          ) : (
            <div className="space-y-4">
              {logs.map((log) => (
                <div
                  key={log.id}
                  className="flex items-center justify-between p-4 bg-gray-50 rounded-lg"
                >
                  <div>
                    <p className="font-medium text-gray-900">
                      {log.scan_type} Scan
                    </p>
                    <p className="text-sm text-gray-600">
                      {log.jobs_found} jobs found • {log.jobs_relevant} relevant
                    </p>
                    <p className="text-xs text-gray-500 mt-1">
                      {new Date(log.started_at).toLocaleString()}
                    </p>
                  </div>
                  <div>
                    <span
                      className={`px-3 py-1 rounded-full text-sm font-medium ${
                        log.status === 'COMPLETED'
                          ? 'bg-green-100 text-green-800'
                          : log.status === 'FAILED'
                          ? 'bg-red-100 text-red-800'
                          : 'bg-yellow-100 text-yellow-800'
                      }`}
                    >
                      {log.status}
                    </span>
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
