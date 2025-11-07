import { useAuth } from '@/hooks/useAuth';
import { useApplications } from '@/hooks/useApplications';
import { CheckCircle, XCircle, Clock } from 'lucide-react';

export default function Applications() {
  const { user } = useAuth();
  const { data: applications, isLoading } = useApplications(user?.id || '');

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'SUCCESS':
        return <CheckCircle className="w-5 h-5 text-green-600" />;
      case 'FAILED':
        return <XCircle className="w-5 h-5 text-red-600" />;
      default:
        return <Clock className="w-5 h-5 text-yellow-600" />;
    }
  };

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Applications</h1>

      {isLoading ? (
        <div className="text-center py-12">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto"></div>
        </div>
      ) : !applications || applications.length === 0 ? (
        <div className="bg-white rounded-lg shadow p-12 text-center">
          <p className="text-gray-500">No applications yet. Approve some jobs to get started!</p>
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow overflow-hidden">
          <table className="min-w-full divide-y divide-gray-200">
            <thead className="bg-gray-50">
              <tr>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Job</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Company</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Submitted</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">Status</th>
                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase">NAV</th>
              </tr>
            </thead>
            <tbody className="bg-white divide-y divide-gray-200">
              {applications.map((app) => (
                <tr key={app.id}>
                  <td className="px-6 py-4">
                    <div className="text-sm font-medium text-gray-900">{app.job?.title}</div>
                  </td>
                  <td className="px-6 py-4 text-sm text-gray-600">{app.job?.company}</td>
                  <td className="px-6 py-4 text-sm text-gray-600">
                    {app.submitted_at ? new Date(app.submitted_at).toLocaleDateString() : '-'}
                  </td>
                  <td className="px-6 py-4">
                    <div className="flex items-center gap-2">
                      {getStatusIcon(app.status)}
                      <span className="text-sm">{app.status}</span>
                    </div>
                  </td>
                  <td className="px-6 py-4">
                    {app.nav_reported ? (
                      <span className="text-green-600 text-sm">✓ Reported</span>
                    ) : (
                      <span className="text-gray-400 text-sm">Not reported</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
