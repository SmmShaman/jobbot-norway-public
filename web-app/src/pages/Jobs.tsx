import { useState } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useJobs } from '@/hooks/useJobs';
import {
  Briefcase,
  MapPin,
  Building2,
  Calendar,
  Clock,
  Mail,
  Phone,
  User,
  ExternalLink,
  CheckCircle,
  XCircle,
  Search,
  Loader2
} from 'lucide-react';
import type { Job } from '@/types';

export default function Jobs() {
  const { user } = useAuth();
  const [filters, setFilters] = useState({
    status: 'all',
    source: 'all',
    search: ''
  });

  const { data: jobs, isLoading } = useJobs(user?.id || '', filters);

  // Filter jobs based on search and filters
  const filteredJobs = jobs?.filter((job: Job) => {
    const matchesSearch = !filters.search ||
      job.title.toLowerCase().includes(filters.search.toLowerCase()) ||
      job.company.toLowerCase().includes(filters.search.toLowerCase()) ||
      job.description?.toLowerCase().includes(filters.search.toLowerCase());

    const matchesStatus = filters.status === 'all' || job.status === filters.status;
    const matchesSource = filters.source === 'all' || job.source === filters.source;

    return matchesSearch && matchesStatus && matchesSource;
  }) || [];

  const statusColors: Record<string, string> = {
    'NEW': 'bg-blue-100 text-blue-800',
    'REVIEWED': 'bg-purple-100 text-purple-800',
    'RELEVANT': 'bg-green-100 text-green-800',
    'NOT_RELEVANT': 'bg-gray-100 text-gray-800',
    'APPROVED': 'bg-teal-100 text-teal-800',
    'APPLIED': 'bg-indigo-100 text-indigo-800',
    'REJECTED': 'bg-red-100 text-red-800',
    'ARCHIVED': 'bg-gray-100 text-gray-600'
  };

  const sourceColors: Record<string, string> = {
    'FINN': 'bg-orange-100 text-orange-800',
    'NAV': 'bg-blue-100 text-blue-800'
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-8 h-8 animate-spin text-primary-600" />
        <span className="ml-3 text-gray-600">Loading jobs...</span>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Job Listings</h1>
          <p className="text-gray-600 mt-1">
            {filteredJobs.length} job{filteredJobs.length !== 1 ? 's' : ''} found
          </p>
        </div>
      </div>

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4">
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Search */}
          <div className="md:col-span-2">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                placeholder="Search jobs..."
                value={filters.search}
                onChange={(e) => setFilters({ ...filters, search: e.target.value })}
                className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
              />
            </div>
          </div>

          {/* Status Filter */}
          <div>
            <select
              value={filters.status}
              onChange={(e) => setFilters({ ...filters, status: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Status</option>
              <option value="NEW">New</option>
              <option value="REVIEWED">Reviewed</option>
              <option value="RELEVANT">Relevant</option>
              <option value="NOT_RELEVANT">Not Relevant</option>
              <option value="APPROVED">Approved</option>
              <option value="APPLIED">Applied</option>
              <option value="REJECTED">Rejected</option>
            </select>
          </div>

          {/* Source Filter */}
          <div>
            <select
              value={filters.source}
              onChange={(e) => setFilters({ ...filters, source: e.target.value })}
              className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
            >
              <option value="all">All Sources</option>
              <option value="FINN">FINN.no</option>
              <option value="NAV">NAV</option>
            </select>
          </div>
        </div>
      </div>

      {/* Jobs List */}
      {filteredJobs.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <Briefcase className="w-16 h-16 mx-auto text-gray-400 mb-4" />
          <h3 className="text-lg font-medium text-gray-900 mb-2">No jobs found</h3>
          <p className="text-gray-600">Try adjusting your filters or scan for new jobs</p>
        </div>
      ) : (
        <div className="space-y-4">
          {filteredJobs.map((job: Job) => (
            <div key={job.id} className="bg-white rounded-lg shadow hover:shadow-lg transition-shadow">
              <div className="p-6">
                {/* Header Row */}
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-2">
                      <h3 className="text-xl font-semibold text-gray-900">{job.title}</h3>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${statusColors[job.status] || 'bg-gray-100 text-gray-800'}`}>
                        {job.status}
                      </span>
                      <span className={`px-2.5 py-0.5 rounded-full text-xs font-medium ${sourceColors[job.source] || 'bg-gray-100 text-gray-800'}`}>
                        {job.source}
                      </span>
                    </div>

                    <div className="flex items-center gap-4 text-sm text-gray-600 flex-wrap">
                      <span className="flex items-center">
                        <Building2 className="w-4 h-4 mr-1" />
                        {job.company}
                      </span>
                      {job.location && (
                        <span className="flex items-center">
                          <MapPin className="w-4 h-4 mr-1" />
                          {job.location}
                        </span>
                      )}
                      {job.employment_type && (
                        <span className="flex items-center">
                          <Briefcase className="w-4 h-4 mr-1" />
                          {job.employment_type}
                        </span>
                      )}
                      {job.extent && (
                        <span className="flex items-center">
                          <Clock className="w-4 h-4 mr-1" />
                          {job.extent}
                        </span>
                      )}
                    </div>
                  </div>

                  <a
                    href={job.url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="ml-4 flex items-center gap-1 text-primary-600 hover:text-primary-700 text-sm font-medium"
                  >
                    View <ExternalLink className="w-4 h-4" />
                  </a>
                </div>

                {/* Description */}
                {job.description && (
                  <div className="mb-4">
                    <p className="text-gray-700 line-clamp-3">{job.description}</p>
                  </div>
                )}

                {/* Details Grid */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-4">
                  {/* Contact Info */}
                  {(job.contact_name || job.contact_email || job.contact_phone) && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                        <User className="w-4 h-4 mr-1" />
                        Contact
                      </h4>
                      {job.contact_name && (
                        <p className="text-sm text-gray-700">{job.contact_name}</p>
                      )}
                      {job.contact_email && (
                        <p className="text-sm text-gray-600 flex items-center mt-1">
                          <Mail className="w-3 h-3 mr-1" />
                          {job.contact_email}
                        </p>
                      )}
                      {job.contact_phone && (
                        <p className="text-sm text-gray-600 flex items-center mt-1">
                          <Phone className="w-3 h-3 mr-1" />
                          {job.contact_phone}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Employment Details */}
                  {(job.salary_range || job.start_date || job.deadline) && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                        <Briefcase className="w-4 h-4 mr-1" />
                        Details
                      </h4>
                      {job.salary_range && (
                        <p className="text-sm text-gray-700">Salary: {job.salary_range}</p>
                      )}
                      {job.start_date && (
                        <p className="text-sm text-gray-700 mt-1">Start: {job.start_date}</p>
                      )}
                      {job.deadline && (
                        <p className="text-sm text-gray-700 mt-1 flex items-center">
                          <Calendar className="w-3 h-3 mr-1 text-red-600" />
                          Deadline: {new Date(job.deadline).toLocaleDateString()}
                        </p>
                      )}
                    </div>
                  )}

                  {/* Address */}
                  {(job.address || job.city || job.county) && (
                    <div className="bg-gray-50 rounded-lg p-3">
                      <h4 className="text-sm font-semibold text-gray-900 mb-2 flex items-center">
                        <MapPin className="w-4 h-4 mr-1" />
                        Address
                      </h4>
                      {job.address && (
                        <p className="text-sm text-gray-700">{job.address}</p>
                      )}
                      <p className="text-sm text-gray-700">
                        {[job.city, job.postalCode, job.county].filter(Boolean).join(', ')}
                      </p>
                    </div>
                  )}
                </div>

                {/* Requirements, Responsibilities, Benefits */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {job.requirements && job.requirements.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Requirements</h4>
                      <ul className="space-y-1">
                        {job.requirements.slice(0, 3).map((req, i) => (
                          <li key={i} className="text-sm text-gray-600 flex items-start">
                            <CheckCircle className="w-3 h-3 mr-1 mt-0.5 text-green-600 flex-shrink-0" />
                            <span className="line-clamp-2">{req}</span>
                          </li>
                        ))}
                        {job.requirements.length > 3 && (
                          <li className="text-xs text-gray-500">+{job.requirements.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}

                  {job.responsibilities && job.responsibilities.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Responsibilities</h4>
                      <ul className="space-y-1">
                        {job.responsibilities.slice(0, 3).map((resp, i) => (
                          <li key={i} className="text-sm text-gray-600 flex items-start">
                            <Briefcase className="w-3 h-3 mr-1 mt-0.5 text-blue-600 flex-shrink-0" />
                            <span className="line-clamp-2">{resp}</span>
                          </li>
                        ))}
                        {job.responsibilities.length > 3 && (
                          <li className="text-xs text-gray-500">+{job.responsibilities.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}

                  {job.benefits && job.benefits.length > 0 && (
                    <div>
                      <h4 className="text-sm font-semibold text-gray-900 mb-2">Benefits</h4>
                      <ul className="space-y-1">
                        {job.benefits.slice(0, 3).map((benefit, i) => (
                          <li key={i} className="text-sm text-gray-600 flex items-start">
                            <CheckCircle className="w-3 h-3 mr-1 mt-0.5 text-purple-600 flex-shrink-0" />
                            <span className="line-clamp-2">{benefit}</span>
                          </li>
                        ))}
                        {job.benefits.length > 3 && (
                          <li className="text-xs text-gray-500">+{job.benefits.length - 3} more</li>
                        )}
                      </ul>
                    </div>
                  )}
                </div>

                {/* Footer with metadata */}
                <div className="mt-4 pt-4 border-t border-gray-200 flex items-center justify-between text-xs text-gray-500">
                  <div className="flex items-center gap-4">
                    {job.posted_date && (
                      <span>Posted: {new Date(job.posted_date).toLocaleDateString()}</span>
                    )}
                    {job.scraped_at && (
                      <span>Scraped: {new Date(job.scraped_at).toLocaleDateString()}</span>
                    )}
                    {job.finnkode && (
                      <span>FINN Code: {job.finnkode}</span>
                    )}
                  </div>
                  {job._skip && (
                    <span className="flex items-center text-red-600">
                      <XCircle className="w-3 h-3 mr-1" />
                      Skipped: {job._skip_reason}
                    </span>
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
