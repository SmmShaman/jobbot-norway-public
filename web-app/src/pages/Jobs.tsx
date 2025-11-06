import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useJobs } from '@/hooks/useJobs';
import { ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react';

export default function Jobs() {
  const { user } = useAuth();
  const [statusFilter, setStatusFilter] = useState<string>('');
  const { data: jobs, isLoading } = useJobs(user?.id || '', { status: statusFilter || undefined });

  const getScoreColor = (score: number) => {
    if (score >= 80) return 'text-green-600 bg-green-50';
    if (score >= 60) return 'text-yellow-600 bg-yellow-50';
    return 'text-red-600 bg-red-50';
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h1 className="text-3xl font-bold text-gray-900">Jobs</h1>
        <select
          value={statusFilter}
          onChange={(e) => setStatusFilter(e.target.value)}
          className="px-4 py-2 border border-gray-300 rounded-lg"
        >
          <option value="">All Status</option>
          <option value="NEW">New</option>
          <option value="ANALYZED">Analyzed</option>
          <option value="APPROVED">Approved</option>
          <option value="REJECTED">Rejected</option>
        </select>
      </div>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        </div>
      ) : !jobs || jobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No jobs found. Try scanning for new opportunities!</p>
        </div>
      ) : (
        <div className="space-y-4">
          {jobs.map((job) => (
            <div key={job.id} className="bg-white rounded-lg shadow p-6">
              <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3">
                    <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                    {job.relevance_score > 0 && (
                      <span className={`px-3 py-1 rounded-full text-sm font-medium ${getScoreColor(job.relevance_score)}`}>
                        {job.relevance_score}% Match
                      </span>
                    )}
                  </div>
                  {job.company && (
                    <p className="text-gray-600 mt-1">{job.company}</p>
                  )}
                  {job.location && (
                    <p className="text-sm text-gray-500 mt-1">📍 {job.location}</p>
                  )}
                  <p className="text-sm text-gray-500 mt-2">
                    Source: {job.source} • Posted: {job.posted_date ? new Date(job.posted_date).toLocaleDateString() : 'N/A'}
                  </p>

                  {job.match_reasons && job.match_reasons.length > 0 && (
                    <div className="mt-4">
                      <p className="text-sm font-medium text-gray-700">Why this matches:</p>
                      <ul className="mt-2 space-y-1">
                        {job.match_reasons.map((reason, idx) => (
                          <li key={idx} className="text-sm text-gray-600">• {reason}</li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>

                <div className="flex flex-col gap-2 ml-4">
                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                  >
                    <ExternalLink className="w-4 h-4" />
                    View Job
                  </a>
                  {job.status === 'ANALYZED' && (
                    <>
                      <button className="flex items-center gap-2 px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        <ThumbsUp className="w-4 h-4" />
                        Approve
                      </button>
                      <button className="flex items-center gap-2 px-4 py-2 bg-red-600 text-white rounded-lg hover:bg-red-700">
                        <ThumbsDown className="w-4 h-4" />
                        Reject
                      </button>
                    </>
                  )}
                </div>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
