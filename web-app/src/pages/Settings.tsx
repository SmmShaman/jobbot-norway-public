import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useUserProfile, useUpdateProfile, useUserSettings, useUpdateSettings, useUploadResume, useAIParsedProfile, useAnalyzeResumes } from '@/hooks/useSettings';
import { User, Settings as SettingsIcon, Globe, Zap, MessageSquare, Upload, Save, Trash2, CheckCircle2, FileText, Eye, Sparkles } from 'lucide-react';

export default function Settings() {
  const { user } = useAuth();
  const { data: profile } = useUserProfile(user?.id || '');
  const { data: settings } = useUserSettings(user?.id || '');
  const { data: aiProfile, refetch: refetchAIProfile } = useAIParsedProfile(user?.id || '');
  const updateProfile = useUpdateProfile();
  const updateSettings = useUpdateSettings();
  const uploadResume = useUploadResume();
  const analyzeResumes = useAnalyzeResumes();

  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);

  // Profile form state
  const [profileForm, setProfileForm] = useState({
    full_name: '',
    phone: '',
    fnr: '',
  });

  // Update form when profile loads
  useEffect(() => {
    if (profile) {
      setProfileForm({
        full_name: profile.full_name || '',
        phone: profile.phone || '',
        fnr: profile.fnr || '',
      });
    }
  }, [profile]);

  // Search URLs state
  const [navUrls, setNavUrls] = useState<string[]>([]);
  const [finnUrls, setFinnUrls] = useState<string[]>([]);
  const [newNavUrl, setNewNavUrl] = useState('');
  const [newFinnUrl, setNewFinnUrl] = useState('');

  useEffect(() => {
    if (settings) {
      setNavUrls(settings.nav_search_urls || []);
      setFinnUrls(settings.finn_search_urls || []);
    }
  }, [settings]);

  // Application settings state
  const [appSettings, setAppSettings] = useState({
    min_relevance_score: 70,
    auto_apply_threshold: 85,
    max_applications_per_day: 5,
    require_manual_approval: true,
  });

  useEffect(() => {
    if (settings) {
      setAppSettings({
        min_relevance_score: settings.min_relevance_score || 70,
        auto_apply_threshold: settings.auto_apply_threshold || 85,
        max_applications_per_day: settings.max_applications_per_day || 5,
        require_manual_approval: settings.require_manual_approval ?? true,
      });
    }
  }, [settings]);

  // NAV credentials state
  const [navCredentials, setNavCredentials] = useState({
    nav_fnr: '',
    nav_password: '',
  });

  // Telegram settings state
  const [telegramSettings, setTelegramSettings] = useState({
    telegram_chat_id: '',
    telegram_enabled: false,
  });

  // AI Prompt settings state
  const [aiPromptSettings, setAiPromptSettings] = useState({
    custom_system_prompt: '',
    custom_user_prompt: '',
  });

  useEffect(() => {
    if (settings) {
      setAiPromptSettings({
        custom_system_prompt: settings.custom_system_prompt || '',
        custom_user_prompt: settings.custom_user_prompt || '',
      });
    }
  }, [settings]);

  useEffect(() => {
    if (settings) {
      setTelegramSettings({
        telegram_chat_id: settings.telegram_chat_id || '',
        telegram_enabled: settings.telegram_enabled || false,
      });
    }
  }, [settings]);

  const handleSaveProfile = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      await updateProfile.mutateAsync({
        userId: user.id,
        updates: profileForm,
      });
      alert('✅ Profile updated successfully!');
    } catch (error) {
      alert('❌ Error updating profile');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveSearchUrls = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        userId: user.id,
        updates: {
          nav_search_urls: navUrls,
          finn_search_urls: finnUrls,
        },
      });
      alert('✅ Search URLs updated!');
    } catch (error) {
      alert('❌ Error updating URLs');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveAppSettings = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        userId: user.id,
        updates: appSettings,
      });
      alert('✅ Settings saved!');
    } catch (error) {
      alert('❌ Error saving settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveNavCredentials = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        userId: user.id,
        updates: {
          nav_fnr: navCredentials.nav_fnr,
          nav_password_encrypted: navCredentials.nav_password,
        },
      });
      alert('✅ NAV credentials saved!');
      setNavCredentials({ ...navCredentials, nav_password: '' });
    } catch (error) {
      alert('❌ Error saving credentials');
    } finally {
      setIsSaving(false);
    }
  };

  const handleSaveTelegram = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      await updateSettings.mutateAsync({
        userId: user.id,
        updates: telegramSettings,
      });
      alert('✅ Telegram settings saved!');
    } catch (error) {
      alert('❌ Error saving Telegram settings');
    } finally {
      setIsSaving(false);
    }
  };

  const handleResumeUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !user) return;

    if (file.type !== 'application/pdf') {
      alert('❌ Please upload a PDF file');
      return;
    }

    if (file.size > 10 * 1024 * 1024) {
      alert('❌ File size must be less than 10MB');
      return;
    }

    setIsSaving(true);
    try {
      await uploadResume.mutateAsync({ userId: user.id, file });
      await refetchAIProfile(); // Refresh AI-parsed data
      alert('✅ Resume uploaded and analyzed successfully!');
    } catch (error: any) {
      console.error('Upload error:', error);
      alert('❌ Error: ' + (error.message || 'Upload failed'));
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'resume', label: 'Resume', icon: Upload },
    { id: 'search', label: 'Search URLs', icon: Globe },
    { id: 'application', label: 'Application', icon: Zap },
    { id: 'nav', label: 'NAV Login', icon: SettingsIcon },
    { id: 'telegram', label: 'Telegram', icon: MessageSquare },
  ];

  return (
    <div className="space-y-6">
      <h1 className="text-3xl font-bold text-gray-900">Settings</h1>

      {/* Tabs */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {tabs.map((tab) => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id)}
              className={`flex items-center gap-2 py-4 px-1 border-b-2 font-medium text-sm transition-colors ${
                activeTab === tab.id
                  ? 'border-primary-500 text-primary-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              <tab.icon className="w-5 h-5" />
              {tab.label}
            </button>
          ))}
        </nav>
      </div>

      {/* Tab Content */}
      <div className="bg-white rounded-lg shadow p-6">
        {/* Profile Tab */}
        {activeTab === 'profile' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">User Profile</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Full Name
              </label>
              <input
                type="text"
                value={profileForm.full_name}
                onChange={(e) => setProfileForm({ ...profileForm, full_name: e.target.value })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Email
              </label>
              <input
                type="email"
                value={user?.email || ''}
                disabled
                className="w-full px-4 py-2 border border-gray-300 rounded-lg bg-gray-50"
              />
              <p className="text-sm text-gray-500 mt-1">Email cannot be changed</p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Phone
              </label>
              <input
                type="tel"
                value={profileForm.phone}
                onChange={(e) => setProfileForm({ ...profileForm, phone: e.target.value })}
                placeholder="+47 123 45 678"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Norwegian ID (FNR)
              </label>
              <input
                type="text"
                value={profileForm.fnr}
                onChange={(e) => setProfileForm({ ...profileForm, fnr: e.target.value })}
                placeholder="11 digits"
                maxLength={11}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary-500"
              />
            </div>

            <button
              onClick={handleSaveProfile}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Profile'}
            </button>
          </div>
        )}

        {/* Resume Tab */}
        {activeTab === 'resume' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Resume Upload & AI Analysis</h2>

            {/* Upload Section */}
            <div className="border-2 border-dashed border-gray-300 rounded-lg p-8 text-center">
              <Upload className="w-12 h-12 mx-auto mb-4 text-gray-400" />
              <p className="text-gray-600 mb-2">Upload your resumes (PDF, max 10MB each)</p>
              <p className="text-sm text-gray-500 mb-4">You can upload up to 5 resumes</p>

              <input
                type="file"
                accept=".pdf"
                onChange={handleResumeUpload}
                className="hidden"
                id="resume-upload"
                disabled={isSaving || (settings?.resume_files && settings.resume_files.length >= 5)}
              />
              <label
                htmlFor="resume-upload"
                className={`inline-flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 cursor-pointer ${
                  isSaving || (settings?.resume_files && settings.resume_files.length >= 5) ? 'opacity-50 cursor-not-allowed' : ''
                }`}
              >
                <Upload className="w-4 h-4" />
                {isSaving ? 'Uploading...' : 'Choose File'}
              </label>

              {settings?.resume_files && settings.resume_files.length >= 5 && (
                <p className="text-sm text-orange-600 mt-2">Maximum 5 resumes reached</p>
              )}
            </div>

            {/* Uploaded Resumes List */}
            {settings?.resume_files && settings.resume_files.length > 0 && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary-600" />
                  Uploaded Resumes ({settings.resume_files.length}/5)
                </h3>

                <div className="space-y-2">
                  {settings.resume_files.map((filePath, index) => (
                    <div key={filePath} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="bg-primary-100 text-primary-700 px-2 py-1 rounded text-sm font-medium">
                          #{index + 1}
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {filePath.split('/').pop()}
                          </p>
                          <p className="text-xs text-gray-500">{filePath}</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <a
                          href={`https://ptrmidlhfdbybxmyovtm.supabase.co/storage/v1/object/public/resumes/${filePath}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
                        >
                          📄 PDF
                        </a>
                        <button
                          onClick={async () => {
                            const url = `https://ptrmidlhfdbybxmyovtm.supabase.co/storage/v1/object/public/resumes/${filePath}`;
                            const response = await fetch(url);
                            const blob = await response.blob();
                            const text = await blob.text();
                            const win = window.open('', '_blank');
                            if (win) {
                              win.document.write('<html><head><title>Extracted Text</title></head><body><pre style="white-space: pre-wrap; font-family: monospace; padding: 20px; line-height: 1.5;">' + text.replace(/</g, '&lt;').replace(/>/g, '&gt;') + '</pre></body></html>');
                            }
                          }}
                          className="inline-flex items-center gap-1 text-xs bg-white border border-blue-300 text-blue-700 px-2 py-1 rounded hover:bg-blue-50"
                        >
                          <Eye className="w-3 h-3" />
                          Текст
                        </button>
                      </div>
                    </div>
                  ))}
                </div>

                {/* Analyze Button */}
                <button
                  onClick={async () => {
                    if (!user) return;
                    setIsSaving(true);
                    try {
                      await analyzeResumes.mutateAsync({ userId: user.id });
                      await refetchAIProfile();
                      alert('✅ Resumes analyzed successfully!');
                    } catch (error: any) {
                      alert('❌ Analysis error: ' + error.message);
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  disabled={isSaving}
                  className="w-full mt-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                >
                  <Sparkles className="w-5 h-5" />
                  {isSaving ? 'Аналізую резюме...' : `Аналізувати всі ${settings.resume_files.length} резюме з AI`}
                </button>

                <p className="text-xs text-gray-500 mt-2 text-center">
                  🤖 AI об'єднає інформацію з усіх резюме в один профіль
                </p>
              </div>
            )}

            {/* AI Prompt Editor */}
            <div className="bg-purple-50 border border-purple-200 rounded-lg p-4">
              <h3 className="text-lg font-semibold text-purple-900 mb-3">🤖 AI Prompt Customization</h3>
              <p className="text-purple-800 text-sm mb-4">
                <strong>Info:</strong> Customize the AI prompt used to analyze your resume. These prompts are sent to Azure OpenAI GPT-4.
              </p>

              <div className="space-y-4">
                {/* System Prompt */}
                <div>
                  <label className="block text-sm font-medium text-purple-900 mb-2">
                    System Prompt (AI Role & Instructions)
                  </label>
                  <textarea
                    value={aiPromptSettings.custom_system_prompt || `You are an EXPERT HR Data Analyst specializing in creating COMPLETE, DETAILED professional profiles for Norwegian job applications.

Your mission: Extract EVERY possible detail from resumes and CREATE A FULLY POPULATED profile that leaves NO FIELD EMPTY. When information is missing, make INTELLIGENT INFERENCES based on context, career patterns, and Norwegian job market standards.

NEVER return incomplete profiles. EVERY field must contain meaningful, realistic data.`}
                    onChange={(e) => setAiPromptSettings({ ...aiPromptSettings, custom_system_prompt: e.target.value })}
                    className="w-full px-3 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-xs"
                    rows={8}
                    placeholder="Enter system prompt..."
                  />
                </div>

                {/* User Prompt */}
                <div>
                  <label className="block text-sm font-medium text-purple-900 mb-2">
                    User Prompt (Task Instructions)
                  </label>
                  <textarea
                    value={aiPromptSettings.custom_user_prompt || `Create a MAXIMALLY COMPLETE professional JSON profile for Norwegian job applications.

This profile will be used for automated job applications in Norway, so ensure:
- Phone numbers follow Norwegian format (+47 XXX XX XXX)
- Include Norwegian language skills (minimum B1 level)
- Address should be Norwegian city unless clearly stated otherwise
- Industries should include relevant Norwegian market sectors
- All technical skills should be comprehensively categorized
- Combine ALL information from ALL resumes into ONE comprehensive profile`}
                    onChange={(e) => setAiPromptSettings({ ...aiPromptSettings, custom_user_prompt: e.target.value })}
                    className="w-full px-3 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent font-mono text-xs"
                    rows={10}
                    placeholder="Enter user prompt..."
                  />
                </div>

                {/* Save Button */}
                <button
                  onClick={async () => {
                    if (!user) return;
                    setIsSaving(true);
                    try {
                      await updateSettings.mutateAsync({
                        userId: user.id,
                        updates: aiPromptSettings,
                      });
                      alert('✅ AI prompts saved successfully!');
                    } catch (error: any) {
                      alert('❌ Error: ' + error.message);
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  disabled={isSaving}
                  className="w-full bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2"
                >
                  <Save className="w-4 h-4" />
                  {isSaving ? 'Saving...' : 'Save AI Prompts'}
                </button>

                <p className="text-xs text-purple-600">
                  💡 Tip: Leave empty to use default prompts. Your custom prompts will be used for all future resume uploads.
                </p>
              </div>
            </div>

            {/* AI-Parsed Profile Data */}
            {aiProfile && (
              <div className="mt-6 space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                  AI-Extracted Profile Data
                </h3>

                <div className="bg-white border border-gray-200 rounded-lg p-4 space-y-3">
                  {aiProfile.full_name && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Full Name</label>
                      <p className="text-gray-900">{aiProfile.full_name}</p>
                    </div>
                  )}

                  {aiProfile.professional_summary && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Professional Summary</label>
                      <p className="text-gray-900">{aiProfile.professional_summary}</p>
                    </div>
                  )}

                  {aiProfile.total_experience_years > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Years of Experience</label>
                      <p className="text-gray-900">{aiProfile.total_experience_years} years</p>
                    </div>
                  )}

                  {aiProfile.technical_skills && aiProfile.technical_skills.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Technical Skills</label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {aiProfile.technical_skills.map((skill: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm"
                          >
                            {skill}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {aiProfile.languages && aiProfile.languages.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Languages</label>
                      <div className="flex flex-wrap gap-2 mt-2">
                        {aiProfile.languages.map((lang: string, idx: number) => (
                          <span
                            key={idx}
                            className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm"
                          >
                            {lang}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {aiProfile.work_experience && Array.isArray(aiProfile.work_experience) && aiProfile.work_experience.length > 0 && (
                    <div>
                      <label className="text-sm font-medium text-gray-600">Work Experience</label>
                      <div className="mt-2 space-y-3">
                        {aiProfile.work_experience.map((exp: any, idx: number) => (
                          <div key={idx} className="p-3 bg-gray-50 rounded-lg">
                            <p className="font-medium text-gray-900">{exp.position}</p>
                            <p className="text-sm text-gray-600">{exp.company}</p>
                            {exp.duration && (
                              <p className="text-sm text-gray-500">{exp.duration}</p>
                            )}
                          </div>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                <p className="text-sm text-gray-500">
                  Parsed at: {new Date(aiProfile.parsed_at).toLocaleString()}
                </p>
              </div>
            )}
          </div>
        )}

        {/* Search URLs Tab */}
        {activeTab === 'search' && (
          <div className="space-y-6">
            <h2 className="text-xl font-semibold mb-4">Job Search URLs</h2>

            {/* NAV URLs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                NAV.no Search URLs
              </label>
              <p className="text-sm text-gray-500 mb-3">
                Add pre-filtered arbeidsplassen.nav.no URLs with your preferred locations and criteria
              </p>

              <div className="flex gap-2 mb-3">
                <input
                  type="url"
                  value={newNavUrl}
                  onChange={(e) => setNewNavUrl(e.target.value)}
                  placeholder="https://arbeidsplassen.nav.no/stillinger?..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={() => {
                    if (newNavUrl) {
                      setNavUrls([...navUrls, newNavUrl]);
                      setNewNavUrl('');
                    }
                  }}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Add
                </button>
              </div>

              <div className="space-y-2">
                {navUrls.map((url, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                    <Globe className="w-4 h-4 text-gray-400" />
                    <span className="flex-1 text-sm truncate">{url}</span>
                    <button
                      onClick={() => setNavUrls(navUrls.filter((_, i) => i !== idx))}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            {/* FINN URLs */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                FINN.no Search URLs
              </label>
              <p className="text-sm text-gray-500 mb-3">
                Add pre-filtered finn.no job search URLs
              </p>

              <div className="flex gap-2 mb-3">
                <input
                  type="url"
                  value={newFinnUrl}
                  onChange={(e) => setNewFinnUrl(e.target.value)}
                  placeholder="https://www.finn.no/job/fulltime/search.html?..."
                  className="flex-1 px-4 py-2 border border-gray-300 rounded-lg"
                />
                <button
                  onClick={() => {
                    if (newFinnUrl) {
                      setFinnUrls([...finnUrls, newFinnUrl]);
                      setNewFinnUrl('');
                    }
                  }}
                  className="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700"
                >
                  Add
                </button>
              </div>

              <div className="space-y-2">
                {finnUrls.map((url, idx) => (
                  <div key={idx} className="flex items-center gap-2 p-3 bg-gray-50 rounded-lg">
                    <Globe className="w-4 h-4 text-gray-400" />
                    <span className="flex-1 text-sm truncate">{url}</span>
                    <button
                      onClick={() => setFinnUrls(finnUrls.filter((_, i) => i !== idx))}
                      className="p-1 text-red-600 hover:bg-red-50 rounded"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                ))}
              </div>
            </div>

            <button
              onClick={handleSaveSearchUrls}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save URLs'}
            </button>
          </div>
        )}

        {/* Application Settings Tab */}
        {activeTab === 'application' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Application Settings</h2>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Minimum Relevance Score
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={appSettings.min_relevance_score}
                onChange={(e) => setAppSettings({ ...appSettings, min_relevance_score: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-sm text-gray-500 mt-1">
                Only show jobs with AI relevance score above this value (0-100)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Auto-Apply Threshold
              </label>
              <input
                type="number"
                min="0"
                max="100"
                value={appSettings.auto_apply_threshold}
                onChange={(e) => setAppSettings({ ...appSettings, auto_apply_threshold: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-sm text-gray-500 mt-1">
                Automatically apply to jobs with score above this (if auto-apply enabled)
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Max Applications Per Day
              </label>
              <input
                type="number"
                min="1"
                max="50"
                value={appSettings.max_applications_per_day}
                onChange={(e) => setAppSettings({ ...appSettings, max_applications_per_day: parseInt(e.target.value) })}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="manual-approval"
                checked={appSettings.require_manual_approval}
                onChange={(e) => setAppSettings({ ...appSettings, require_manual_approval: e.target.checked })}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded"
              />
              <label htmlFor="manual-approval" className="ml-2 text-sm text-gray-700">
                Require manual approval before applying
              </label>
            </div>

            <button
              onClick={handleSaveAppSettings}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        )}

        {/* NAV Credentials Tab */}
        {activeTab === 'nav' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">NAV Login Credentials</h2>

            <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4 mb-4">
              <p className="text-yellow-800 text-sm">
                <strong>Security:</strong> Your password is encrypted before storage.
                It's only used for automatic NAV reporting.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                FNR (Norwegian ID)
              </label>
              <input
                type="text"
                value={navCredentials.nav_fnr}
                onChange={(e) => setNavCredentials({ ...navCredentials, nav_fnr: e.target.value })}
                placeholder="11 digits"
                maxLength={11}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                NAV Password
              </label>
              <input
                type="password"
                value={navCredentials.nav_password}
                onChange={(e) => setNavCredentials({ ...navCredentials, nav_password: e.target.value })}
                placeholder="Enter to update"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
            </div>

            <button
              onClick={handleSaveNavCredentials}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Credentials'}
            </button>
          </div>
        )}

        {/* Telegram Tab */}
        {activeTab === 'telegram' && (
          <div className="space-y-4">
            <h2 className="text-xl font-semibold mb-4">Telegram Notifications</h2>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-4">
              <p className="text-blue-800 text-sm">
                Get instant notifications about new jobs, applications, and NAV reports via Telegram bot.
              </p>
            </div>

            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Telegram Chat ID
              </label>
              <input
                type="text"
                value={telegramSettings.telegram_chat_id}
                onChange={(e) => setTelegramSettings({ ...telegramSettings, telegram_chat_id: e.target.value })}
                placeholder="Your Telegram chat ID"
                className="w-full px-4 py-2 border border-gray-300 rounded-lg"
              />
              <p className="text-sm text-gray-500 mt-1">
                Get your chat ID by messaging @userinfobot on Telegram
              </p>
            </div>

            <div className="flex items-center">
              <input
                type="checkbox"
                id="telegram-enabled"
                checked={telegramSettings.telegram_enabled}
                onChange={(e) => setTelegramSettings({ ...telegramSettings, telegram_enabled: e.target.checked })}
                className="w-4 h-4 text-primary-600 border-gray-300 rounded"
              />
              <label htmlFor="telegram-enabled" className="ml-2 text-sm text-gray-700">
                Enable Telegram notifications
              </label>
            </div>

            <button
              onClick={handleSaveTelegram}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
