import { useAuth } from '@/hooks/useAuth';
import { useDashboardStats } from '@/hooks/useDashboard';
import { useScanJobs, useJobs } from '@/hooks/useJobs';
import { Briefcase, CheckCircle, FileText, PlayCircle, ExternalLink, Download, ChevronDown, ChevronRight } from 'lucide-react';
import { Fragment, useMemo, useState } from 'react';

// Helper function to determine job status based on data
function getJobStatus(job: any): { label: string; color: string } {
  // Check if in NAV report (complete)
  if (job.nav_report_id || job.in_nav_report) {
    return { label: 'Complete', color: 'bg-purple-100 text-purple-800' };
  }

  // Check if application sent
  if (job.application_sent_at || (job.application_status === 'submitted')) {
    return { label: 'Sended', color: 'bg-blue-100 text-blue-800' };
  }

  // Check if søknad written
  if (job.has_application || job.cover_letter_id) {
    return { label: 'Søknad', color: 'bg-teal-100 text-teal-800' };
  }

  // Check if analyzed
  if (job.relevance_score !== null && job.relevance_score !== undefined && job.ai_recommendation) {
    return { label: 'Analyzed', color: 'bg-green-100 text-green-800' };
  }

  // Check if full details extracted
  if (job.description && job.company && job.location) {
    return { label: 'Full', color: 'bg-yellow-100 text-yellow-800' };
  }

  // New job (only URL, no details yet)
  return { label: 'New', color: 'bg-gray-100 text-gray-800' };
}

const STATUS_OPTIONS = [
  { value: '', label: 'All statuses' },
  { value: 'Complete', label: 'Complete' },
  { value: 'Sended', label: 'Sended' },
  { value: 'Søknad', label: 'Søknad' },
  { value: 'Analyzed', label: 'Analyzed' },
  { value: 'Full', label: 'Full' },
  { value: 'New', label: 'New' },
];

const DATE_INTERVAL_OPTIONS = [
  { value: '', label: 'Any time range' },
  { value: '2', label: 'Last 2 days' },
  { value: '5', label: 'Last 5 days' },
  { value: '7', label: 'Last 7 days' },
  { value: '14', label: 'Last 14 days' },
];

type JobFilterField = 'title' | 'company' | 'location' | 'status' | 'addedDate' | 'addedInterval';
type FilterState = Record<JobFilterField, string>;

const matchesFilterText = (value: string | null | undefined, filter: string) => {
  if (!filter) return true;
  return String(value || '').toLowerCase().includes(filter.toLowerCase());
};

const getJobAddedTimestamp = (job: any): number | null => {
  const dateString = job.discovered_at || job.scraped_at;
  if (!dateString) return null;
  const parsed = Date.parse(dateString);
  return Number.isNaN(parsed) ? null : parsed;
};

const matchesAddedDate = (timestamp: number | null, filterDate: string) => {
  if (!filterDate) return true;
  if (!timestamp) return false;
  const jobDate = new Date(timestamp).toISOString().split('T')[0];
  return jobDate === filterDate;
};

const matchesAddedInterval = (timestamp: number | null, intervalValue: string) => {
  if (!intervalValue) return true;
  if (!timestamp) return false;
  const days = Number(intervalValue);
  if (Number.isNaN(days) || days <= 0) return true;
  const diffMs = Date.now() - timestamp;
  return diffMs <= days * 24 * 60 * 60 * 1000;
};

export default function Dashboard() {
  const { user } = useAuth();
  const { data: stats, isLoading: statsLoading } = useDashboardStats(user?.id || '');
  const { data: jobs, isLoading: jobsLoading } = useJobs(user?.id || '');
  const scanJobs = useScanJobs();
 
  const [selectedJobs, setSelectedJobs] = useState<string[]>([]);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [expandedJobId, setExpandedJobId] = useState<string | null>(null);
  const [filters, setFilters] = useState<FilterState>({
    title: '',
    company: '',
    location: '',
    status: '',
    addedDate: '',
    addedInterval: '',
  });
 
  const filteredJobs = useMemo(() => {
    const list = jobs || [];
    return list.filter((job: any) => {
      const statusLabel = getJobStatus(job).label;
      const addedTimestamp = getJobAddedTimestamp(job);
      return (
        matchesFilterText(job.title, filters.title) &&
        matchesFilterText(job.company, filters.company) &&
        matchesFilterText(job.location, filters.location) &&
        (filters.status ? statusLabel === filters.status : true) &&
        matchesAddedDate(addedTimestamp, filters.addedDate) &&
        matchesAddedInterval(addedTimestamp, filters.addedInterval)
      );
    });
  }, [jobs, filters]);
 
  const handleFilterChange = (field: JobFilterField, value: string) => {
    setFilters((prev: FilterState) => ({
      ...prev,
      [field]: value,
    }));
  };

  const handleScanNow = () => {
    if (user) {
      scanJobs.mutate({
        user_id: user.id,
        scan_type: 'MANUAL',
      });
    }
  };

  const handleSelectJob = (jobId: string) => {
    setSelectedJobs((prev: string[]) =>
      prev.includes(jobId) ? prev.filter((id: string) => id !== jobId) : [...prev, jobId]
    );
  };
 
  const handleSelectAll = () => {
    if (selectedJobs.length === filteredJobs.length && filteredJobs.length > 0) {
      setSelectedJobs([]);
    } else {
      setSelectedJobs(filteredJobs.map((j: any) => j.id));
    }
  };

  const toggleExpandJob = (jobId: string) => {
    setExpandedJobId(expandedJobId === jobId ? null : jobId);
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
              `Created: ${data.jobsSaved} new\n` +
              `Updated: ${data.jobsUpdated} existing\n` +
              `Unchanged: ${data.jobsSkipped} skipped`);

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

  const handleAnalyzeRelevance = async () => {
    if (selectedJobs.length === 0) {
      alert('⚠️ Please select at least one job to analyze');
      return;
    }

    setIsAnalyzing(true);

    try {
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

      const response = await fetch(`${supabaseUrl}/functions/v1/job-analyzer`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${supabaseAnonKey}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          jobIds: selectedJobs,
          userId: user?.id,
        }),
      });

      const data = await response.json();

      if (data.success) {
        alert(`✅ Analyzed ${data.jobsAnalyzed} job(s)!\n\n` +
              `Updated: ${data.jobsUpdated}\n` +
              `Failed: ${data.jobsFailed}`);

        // Refresh jobs list
        window.location.reload();
      } else {
        alert(`❌ Error: ${data.error}`);
      }
    } catch (error: any) {
      console.error('Analyze error:', error);
      alert('❌ Error analyzing relevance. Check console for details.');
    } finally {
      setIsAnalyzing(false);
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

      {/* Scraped Jobs Table */}
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-lg font-semibold text-gray-900">Scraped Jobs</h2>
              <p className="text-sm text-gray-500 mt-1">
                Showing {filteredJobs.length} of {jobs?.length || 0} jobs • {selectedJobs.length} selected
              </p>
            </div>
            {selectedJobs.length > 0 && (
              <div className="flex items-center gap-3">
                <button
                  onClick={handleExtractDetails}
                  disabled={isExtracting || isAnalyzing}
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
                <button
                  onClick={handleAnalyzeRelevance}
                  disabled={isAnalyzing || isExtracting}
                  className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                      Analyzing...
                    </>
                  ) : (
                    <>
                      <CheckCircle className="w-4 h-4" />
                      Analyze Relevance ({selectedJobs.length})
                    </>
                  )}
                </button>
              </div>
            )}
          </div>
          <div className="mt-4 grid gap-3 md:grid-cols-6">
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Title</span>
              <input
                value={filters.title}
                onChange={(event) => handleFilterChange('title', event.target.value)}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
                placeholder="Filter by title"
              />
            </label>
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Company</span>
              <input
                value={filters.company}
                onChange={(event) => handleFilterChange('company', event.target.value)}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
                placeholder="Filter by company"
              />
            </label>
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Location</span>
              <input
                value={filters.location}
                onChange={(event) => handleFilterChange('location', event.target.value)}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
                placeholder="Filter by location"
              />
            </label>
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Status</span>
              <select
                value={filters.status}
                onChange={(event) => handleFilterChange('status', event.target.value)}
                className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
              >
                {STATUS_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Added date</span>
              <input
                type="date"
                value={filters.addedDate}
                onChange={(event) => handleFilterChange('addedDate', event.target.value)}
                className="w-full rounded-md border border-gray-200 px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
              />
            </label>
            <label className="text-xs text-gray-500">
              <span className="text-gray-700 block mb-1">Interval</span>
              <select
                value={filters.addedInterval}
                onChange={(event) => handleFilterChange('addedInterval', event.target.value)}
                className="w-full rounded-md border border-gray-200 bg-white px-3 py-2 text-sm focus:border-primary-600 focus:outline-none"
              >
                {DATE_INTERVAL_OPTIONS.map((option) => (
                  <option key={option.value} value={option.value}>
                    {option.label}
                  </option>
                ))}
              </select>
            </label>
          </div>
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
          ) : filteredJobs.length === 0 ? (
            <div className="p-8 text-center text-gray-500">
              <p>No jobs match the current filters</p>
            </div>
          ) : (
            <table className="min-w-full divide-y divide-gray-200">
              <thead className="bg-gray-50">
                <tr>
                  <th className="px-6 py-3 text-left w-12">
                    <input
                      type="checkbox"
                      checked={selectedJobs.length === filteredJobs.length && filteredJobs.length > 0}
                      onChange={handleSelectAll}
                      className="rounded border-gray-300"
                    />
                  </th>
                  <th className="px-6 py-3 text-left w-8"></th>
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
                    Contact
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Added
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Deadline
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Score
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Relevance
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                  <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Actions
                  </th>
                </tr>
              </thead>
              <tbody className="bg-white divide-y divide-gray-200">
                {filteredJobs.map((job: any) => {
                  const addedTimestamp = getJobAddedTimestamp(job);
                  return (
                    <Fragment key={job.id}>
                      <tr
                        className={`${selectedJobs.includes(job.id) ? 'bg-blue-50' : 'hover:bg-gray-50'} cursor-pointer`}
                        onClick={(e) => {
                          if ((e.target as HTMLElement).closest('input, a')) return;
                          toggleExpandJob(job.id);
                        }}
                      >
                        <td className="px-6 py-4 whitespace-nowrap">
                          <input
                            type="checkbox"
                            checked={selectedJobs.includes(job.id)}
                            onChange={() => handleSelectJob(job.id)}
                            className="rounded border-gray-300"
                          />
                        </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            toggleExpandJob(job.id);
                          }}
                          className="text-gray-400 hover:text-gray-600"
                        >
                          {expandedJobId === job.id ? (
                            <ChevronDown className="w-4 h-4" />
                          ) : (
                            <ChevronRight className="w-4 h-4" />
                          )}
                        </button>
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
                      <td className="px-6 py-4">
                        <div className="text-xs text-gray-700">
                          {job.contact_person && (
                            <div className="mb-1">{job.contact_person}</div>
                          )}
                          {job.contact_email && (
                            <div className="mb-1">
                              <a href={`mailto:${job.contact_email}`} className="text-primary-600 hover:underline">
                                {job.contact_email}
                              </a>
                            </div>
                          )}
                          {job.contact_phone && (
                            <div>
                              <a href={`tel:${job.contact_phone}`} className="text-primary-600 hover:underline">
                                {job.contact_phone}
                              </a>
                            </div>
                          )}
                          {!job.contact_person && !job.contact_email && !job.contact_phone && '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {addedTimestamp ? new Date(addedTimestamp).toLocaleDateString('no-NO') : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div className="text-sm text-gray-900">
                          {job.deadline ? new Date(job.deadline).toLocaleDateString('no-NO') : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {job.relevance_score !== null && job.relevance_score !== undefined ? (
                          <div className="flex items-center">
                            <span className={`text-lg font-bold ${
                              job.relevance_score >= 70 ? 'text-green-600' :
                              job.relevance_score >= 40 ? 'text-yellow-600' :
                              'text-red-600'
                            }`}>
                              {job.relevance_score}
                            </span>
                            <span className="text-xs text-gray-500 ml-1">/100</span>
                          </div>
                        ) : (
                          <span className="text-xs text-gray-400">Not analyzed</span>
                        )}
                      </td>
                      <td className="px-6 py-4">
                        <div className="text-xs text-gray-700 max-w-xs">
                          {job.ai_recommendation ? (
                            <div className="line-clamp-2" title={job.ai_recommendation}>
                              {job.ai_recommendation}
                            </div>
                          ) : '-'}
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {(() => {
                          const status = getJobStatus(job);
                          return (
                            <span className={`px-2 py-1 inline-flex text-xs leading-5 font-semibold rounded-full ${status.color}`}>
                              {status.label}
                            </span>
                          );
                        })()}
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
                    {expandedJobId === job.id && (
                      <tr key={`${job.id}-details`} className="bg-gray-50">
                        <td colSpan={12} className="px-6 py-4">
                          <div className="space-y-4">
                            {/* AI Recommendation - Full Text */}
                            {job.ai_recommendation && (
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">🤖 AI Relevance Analysis</h4>
                                <div className="bg-white rounded-lg p-4 border border-gray-200">
                                  <p className="text-sm text-gray-700 whitespace-pre-wrap">{job.ai_recommendation}</p>
                                </div>
                              </div>
                            )}

                            {/* Description */}
                            {job.description && (
                              <div>
                                <h4 className="text-sm font-semibold text-gray-900 mb-2">Job Description</h4>
                                <p className="text-sm text-gray-700 whitespace-pre-wrap max-h-96 overflow-y-auto">{job.description}</p>
                              </div>
                            )}

                            {/* Metadata */}
                            {(job.source || job.scraped_at || job.discovered_at || job.relevance_score) && (
                              <div className="flex items-center gap-6 text-xs text-gray-500 pt-2 border-t border-gray-200">
                                <div>
                                  <span className="font-medium">Source:</span> {job.source}
                                </div>
                                <div>
                                  <span className="font-medium">Scraped:</span> {new Date(job.scraped_at || job.discovered_at).toLocaleString()}
                                </div>
                                {job.relevance_score && (
                                  <div>
                                    <span className="font-medium">Relevance:</span> {job.relevance_score}%
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        </td>
                      </tr>
                    )}
                  </Fragment>
                );
              })}
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
