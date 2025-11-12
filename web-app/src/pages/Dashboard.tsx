import { useAuth } from '@/hooks/useAuth';
import { useDashboardStats, useMonitoringLogs } from '@/hooks/useDashboard';
import { useScanJobs, useJobs } from '@/hooks/useJobs';
import { Briefcase, CheckCircle, Clock, FileText, PlayCircle, ExternalLink, Download } from 'lucide-react';
import { useState } from 'react';

export default function Dashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats(user?.id || '');
  const { data: logs } = useMonitoringLogs(user?.id || '', 5);
  const { data: jobs, isLoading: jobsLoading } = useJobs(user?.id || '');
  const scanJobs = useScanJobs();

  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);

  const handleScanNow = () => {
    if (user) {
      scanJobs.mutate({
        user_id: user.id,
        scan_type: 'MANUAL',
      });
    }
  };

  const handleSelectJob = (jobId: string) => {
    setSelectedJobs(prev =>
      prev.includes(jobId) ? prev.filter(id => id !== jobId) : [...prev, jobId]
    );
  };

  const handleSelectAll = () => {
    if (selectedJobs.length === jobs?.length) {
      setSelectedJobs([]);
    } else {
      setSelectedJobs(jobs?.map((j: any) => j.id) || []);
    }
  };

  const handleExtractDetails = async () => {
    if (selectedJobs.length === 0) {
      alert('⚠️ Please select at least one job');
      return;
    }

    setIsExtracting(true);

    try {
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

      // Get URLs of selected jobs
      const selectedJobsData = (jobs || []).filter((j: any) => selectedJobs.includes(j.id));
      const jobUrls = selectedJobsData.map((j: any) => j.url);

      // Call job-scraper with MODE 2 (jobUrls)
      const response = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseAnonKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobUrls,
          userId: user?.id,
        }),
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ Extracted details for ${data.jobsScraped} job(s)!\n\n` +
              `Saved: ${data.jobsSaved} new\n` +
              `Updated: ${data.jobsSkipped} existing`);

        // Refresh jobs list
        window.location.reload();
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    } catch (error: any) {
      console.error('Extract error:', error);
      alert('❌ Error extracting details. Check console for details.');
    } finally {
      setIsExtracting(false);
      setSelectedJobs([]);
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

      {/* Scraped Jobs Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200 flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">Scraped Jobs</h2>
            <p className="text-sm text-gray-500 mt-1">
              {jobs?.length || 0} jobs found • {selectedJobs.length} selected
            </p>
          </div>
          {selectedJobs.length > 0 && (
            <button
              onClick={handleExtractDetails}
              disabled={isExtracting}
              className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isExtracting ? (
                <>
                  <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                  Extracting...
                </>
              ) : (
                <>
                  <Download className="w-4 h-4" />
                  Extract Details ({selectedJobs.length})
                </>
              )}
            </button>
          )}
        </div>

        <div className="overflow-x-auto">
          {jobsLoading ? (
            <div className="p-8 text-center text-gray-500">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
              <p className="mt-2">Loading jobs...</p>
            </div>
          ) : !jobs || jobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <Briefcase className="w-12 h-12 mx-auto mb-3 opacity-50" />
              <p>No jobs found yet. Add FINN.no URLs in Settings and click "Scrape Jobs Now"</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left">
                    <input
                      type="checkbox"
                      checked={selectedJobs.length === (jobs?.length || 0)}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300"
                    />
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Title
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Company
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Location
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Discovered
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {(jobs || []).map((job: any) => (
                  <tr key={job.id} className={selectedJobs.includes(job.id) ? 'bg-blue-50' : 'hover:bg-gray-50'}>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <input
                        type="checkbox"
                        checked={selectedJobs.includes(job.id)}
                        onChange={() => handleSelectJob(job.id)}
                        className="rounded border-gray-300"
                      />
                    </td>
                    <td className="px-6 py-4">
                      <div className="text-sm font-medium text-gray-900">{job.title}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{job.company || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <div className="text-sm text-gray-900">{job.location || '-'}</div>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap">
                      <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${
                        job.status === 'NEW' ? 'bg-blue-100 text-blue-800' :
                        job.status === 'RELEVANT' ? 'bg-green-100 text-green-800' :
                        'bg-gray-100 text-gray-800'
                      }`}>
                        {job.status}
                      </span>
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                      {new Date(job.discovered_at).toLocaleDateString()}
                    </td>
                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                      <a
                        href={job.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary-600 hover:text-primary-900 inline-flex items-center gap-1"
                      >
                        View <ExternalLink className="w-3 h-3" />
                      </a>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
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
