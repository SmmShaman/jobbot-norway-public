import { useState, useEffect } from 'react';
import { useAuth } from '@/hooks/useAuth';
import { useUserProfile, useUpdateProfile, useUserSettings, useUpdateSettings, useUploadResume, useAIParsedProfile, useAnalyzeResumes, useSavedProfiles, useSaveProfile, useSetActiveProfile, useDeleteProfile } from '@/hooks/useSettings';
import { User, Settings as SettingsIcon, Globe, Zap, MessageSquare, Upload, Save, Trash2, CheckCircle2, FileText, Eye, Sparkles, Archive, Star, Play, Loader2, Clock } from 'lucide-react';

export default function Settings() {
  const { user } = useAuth();
  const { data: profile } = useUserProfile(user?.id || '');
  const { data: settings } = useUserSettings(user?.id || '');
  const { data: aiProfile, refetch: refetchAIProfile } = useAIParsedProfile(user?.id || '');
  const updateProfile = useUpdateProfile();
  const updateSettings = useUpdateSettings();
  const uploadResume = useUploadResume();
  const analyzeResumes = useAnalyzeResumes();

  // Saved profiles hooks
  const { data: savedProfiles, refetch: refetchSavedProfiles } = useSavedProfiles(user?.id || '');
  const saveProfile = useSaveProfile();
  const setActiveProfile = useSetActiveProfile();
  const deleteProfile = useDeleteProfile();

  const [activeTab, setActiveTab] = useState('profile');
  const [isSaving, setIsSaving] = useState(false);
  const [extractedText, setExtractedText] = useState<string>('');
  const [isExtracting, setIsExtracting] = useState(false);

  // Profile saving state
  const [profileName, setProfileName] = useState<string>('');
  const [showSaveDialog, setShowSaveDialog] = useState(false);

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
  const [isScraping, setIsScraping] = useState(false);
  const [scrapeResults, setScrapeResults] = useState<any>(null);

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

  // Scheduled scanning settings state
  const [scheduleSettings, setScheduleSettings] = useState({
    scan_schedule_enabled: false,
    scan_schedule_cron: '0 9 * * *', // Default: Every day at 9 AM
    scan_schedule_timezone: 'Europe/Oslo',
  });

  // Custom schedule settings
  const [scheduleMode, setScheduleMode] = useState<'preset' | 'custom'>('preset');
  const [customHour, setCustomHour] = useState('9');
  const [customMinute, setCustomMinute] = useState('0');
  const [customDays, setCustomDays] = useState<string[]>(['*']); // * = every day

  useEffect(() => {
    if (settings) {
      setScheduleSettings({
        scan_schedule_enabled: settings.scan_schedule_enabled || false,
        scan_schedule_cron: settings.scan_schedule_cron || '0 9 * * *',
        scan_schedule_timezone: settings.scan_schedule_timezone || 'Europe/Oslo',
      });
    }
  }, [settings]);

  // Parse cron to extract custom values
  useEffect(() => {
    const cron = scheduleSettings.scan_schedule_cron;
    const parts = cron.split(' ');
    if (parts.length === 5) {
      const [minute, hour, , , dayOfWeek] = parts;
      setCustomMinute(minute);
      setCustomHour(hour);
      if (dayOfWeek === '*') {
        setCustomDays(['*']);
      } else {
        setCustomDays(dayOfWeek.split(','));
      }
    }
  }, [scheduleSettings.scan_schedule_cron]);

  // Generate cron expression from custom settings
  const generateCronExpression = (hour: string, minute: string, days: string[]): string => {
    const dayString = days.includes('*') ? '*' : days.join(',');
    return `${minute} ${hour} * * ${dayString}`;
  };

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

  const handleScrapeJobs = async () => {
    if (!user || finnUrls.length === 0) {
      alert('⚠️ Please add at least one FINN.no search URL first');
      return;
    }

    setIsScraping(true);
    setScrapeResults(null);

    try {
      const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
      const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

      // Scrape all FINN URLs
      const results = [];
      for (const searchUrl of finnUrls) {
        const response = await fetch(`${supabaseUrl}/functions/v1/job-scraper`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${supabaseAnonKey}`,
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            searchUrl,
            userId: user.id,
          }),
        });

        const data = await response.json();
        results.push(data);
      }

      // Aggregate results
      const totalScraped = results.reduce((sum, r) => sum + (r.jobsScraped || 0), 0);
      const totalSaved = results.reduce((sum, r) => sum + (r.jobsSaved || 0), 0);
      const totalUpdated = results.reduce((sum, r) => sum + (r.jobsUpdated || 0), 0);
      const totalSkipped = results.reduce((sum, r) => sum + (r.jobsSkipped || 0), 0);

      setScrapeResults({
        success: true,
        totalScraped,
        totalSaved,
        totalUpdated,
        totalSkipped,
        results,
      });

      alert(`✅ Scraping complete!\n\nScraped: ${totalScraped} jobs\nCreated: ${totalSaved} new\nUpdated: ${totalUpdated} existing\nUnchanged: ${totalSkipped} skipped`);
    } catch (error: any) {
      console.error('Scrape error:', error);
      alert('❌ Error scraping jobs. Check console for details.');
      setScrapeResults({
        success: false,
        error: error.message,
      });
    } finally {
      setIsScraping(false);
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

  // Handler to save current AI profile as a saved profile
  const handleSaveCurrentProfile = async () => {
    if (!user || !aiProfile) {
      alert('❌ No AI profile to save. Please analyze your resumes first.');
      return;
    }

    // Get source resumes from settings
    const sourceResumes = settings?.resume_files || [];

    setIsSaving(true);
    try {
      await saveProfile.mutateAsync({
        userId: user.id,
        profileName: profileName || null, // null will auto-generate name with timestamp
        profileData: aiProfile,
        sourceResumes: sourceResumes,
      });

      alert(`✅ Профіль "${profileName || 'автозбережено'}" успішно збережено!`);
      setProfileName('');
      setShowSaveDialog(false);
      refetchSavedProfiles();
    } catch (error: any) {
      alert(`❌ Помилка збереження профілю: ${error.message || 'Unknown error'}`);
    } finally {
      setIsSaving(false);
    }
  };

  // Handler to activate a saved profile
  const handleActivateProfile = async (profileId: string) => {
    if (!user) return;

    try {
      await setActiveProfile.mutateAsync({ userId: user.id, profileId });
      alert('✅ Профіль активовано! Він буде використовуватися для оцінки вакансій.');
      refetchSavedProfiles();
    } catch (error: any) {
      alert(`❌ Помилка активації профілю: ${error.message || 'Unknown error'}`);
    }
  };

  // Handler to delete a saved profile
  const handleDeleteSavedProfile = async (profileId: string, profileName: string) => {
    if (!user) return;

    const confirmed = window.confirm(
      `⚠️ Ви впевнені, що хочете видалити профіль "${profileName}"?\n\nЦю дію не можна скасувати.`
    );

    if (!confirmed) return;

    try {
      await deleteProfile.mutateAsync({ profileId, userId: user.id });
      alert('✅ Профіль видалено');
      refetchSavedProfiles();
    } catch (error: any) {
      alert(`❌ Помилка видалення профілю: ${error.message || 'Unknown error'}`);
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

  const handleToggleDay = (day: string) => {
    if (customDays.includes('*')) {
      // If "every day" is selected, replace with the clicked day
      setCustomDays([day]);
    } else if (customDays.includes(day)) {
      // Remove day if already selected
      const newDays = customDays.filter(d => d !== day);
      // If no days selected, set to every day
      setCustomDays(newDays.length === 0 ? ['*'] : newDays);
    } else {
      // Add day
      setCustomDays([...customDays, day]);
    }
  };

  const handleSaveScheduleSettings = async () => {
    if (!user) return;
    setIsSaving(true);
    try {
      // If custom mode, generate cron from custom settings
      let cronToSave = scheduleSettings.scan_schedule_cron;
      if (scheduleMode === 'custom') {
        cronToSave = generateCronExpression(customHour, customMinute, customDays);
      }

      console.log('Saving schedule settings:', {
        scan_schedule_enabled: scheduleSettings.scan_schedule_enabled,
        scan_schedule_cron: cronToSave,
        scan_schedule_timezone: scheduleSettings.scan_schedule_timezone,
      });

      await updateSettings.mutateAsync({
        userId: user.id,
        updates: {
          scan_schedule_enabled: scheduleSettings.scan_schedule_enabled,
          scan_schedule_cron: cronToSave,
          scan_schedule_timezone: scheduleSettings.scan_schedule_timezone,
        } as any,
      });

      // Update local state with saved cron
      setScheduleSettings({
        ...scheduleSettings,
        scan_schedule_cron: cronToSave,
      });

      alert('✅ Automation settings saved!');
    } catch (error: any) {
      console.error('Error saving automation settings:', error);
      const errorMessage = error?.message || error?.error?.message || JSON.stringify(error);
      alert(`❌ Error saving automation settings:\n\n${errorMessage}\n\nPlease check browser console for details.`);
    } finally {
      setIsSaving(false);
    }
  };

  const tabs = [
    { id: 'profile', label: 'Profile', icon: User },
    { id: 'resume', label: 'Resume', icon: Upload },
    { id: 'search', label: 'Search URLs', icon: Globe },
    { id: 'application', label: 'Application', icon: Zap },
    { id: 'automation', label: 'Automation', icon: Clock },
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

            {/* Debug info - показує що є в settings */}
            {settings && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-3 text-xs">
                <details>
                  <summary className="cursor-pointer font-medium text-blue-900">🔍 Debug: Settings Data</summary>
                  <pre className="mt-2 text-blue-800 overflow-auto">
                    {JSON.stringify({
                      resume_storage_path: settings.resume_storage_path,
                      resume_files: settings.resume_files,
                      resume_files_length: settings.resume_files?.length || 0,
                    }, null, 2)}
                  </pre>
                </details>
              </div>
            )}

            {/* Uploaded Resumes List */}
            {settings && (settings.resume_files?.length > 0 || settings.resume_storage_path) && (
              <div className="bg-white border border-gray-200 rounded-lg p-4">
                <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
                  <FileText className="w-5 h-5 text-primary-600" />
                  Uploaded Resumes ({(settings.resume_files?.length || (settings.resume_storage_path ? 1 : 0))}/5)
                </h3>

                {/* Show message if resume_files doesn't exist (migration not run) */}
                {!settings.resume_files && settings.resume_storage_path && (
                  <div className="mb-3 p-2 bg-orange-50 border border-orange-200 rounded text-sm text-orange-800">
                    ⚠️ Старий формат даних. Виконай SQL міграцію щоб побачити всі резюме.
                  </div>
                )}

                <div className="space-y-2">
                  {/* Show new format resume_files */}
                  {settings.resume_files && settings.resume_files.length > 0 ? (
                    settings.resume_files.map((filePath: string, index: number) => (
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
                  ))
                  ) : settings.resume_storage_path ? (
                    /* Fallback: show old format resume_storage_path as single resume */
                    <div className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center gap-3">
                        <span className="bg-primary-100 text-primary-700 px-2 py-1 rounded text-sm font-medium">
                          #1
                        </span>
                        <div>
                          <p className="text-sm font-medium text-gray-900">
                            {settings.resume_storage_path.split('/').pop()}
                          </p>
                          <p className="text-xs text-gray-500">{settings.resume_storage_path}</p>
                        </div>
                      </div>

                      <div className="flex gap-2">
                        <a
                          href={`https://ptrmidlhfdbybxmyovtm.supabase.co/storage/v1/object/public/resumes/${settings.resume_storage_path}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center gap-1 text-xs bg-white border border-gray-300 text-gray-700 px-2 py-1 rounded hover:bg-gray-100"
                        >
                          📄 PDF
                        </a>
                        <button
                          onClick={async () => {
                            const url = `https://ptrmidlhfdbybxmyovtm.supabase.co/storage/v1/object/public/resumes/${settings.resume_storage_path}`;
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
                  ) : null}
                </div>

                {/* Extract Text Button */}
                <button
                  onClick={async () => {
                    if (!user || !settings) return;
                    setIsExtracting(true);
                    try {
                      const resumeFiles = settings.resume_files || (settings.resume_storage_path ? [settings.resume_storage_path] : []);

                      if (resumeFiles.length === 0) {
                        alert('❌ Немає завантажених резюме');
                        return;
                      }

                      console.log(`Витягую текст з ${resumeFiles.length} резюме з unpdf...`);

                      // Викликаємо Edge Function з unpdf для якісного парсингу
                      const { storage } = await import('@/lib/supabase');
                      const result = await storage.extractTextFromResumes(user.id);

                      setExtractedText(result.combinedText);
                      console.log('Результат витягування:', result.stats);

                      alert(`✅ Текст витягнуто з unpdf!\n\n` +
                            `📊 Резюме: ${result.stats.successCount}/${result.stats.totalResumes}\n` +
                            `📝 Символів: ${result.stats.totalCharacters.toLocaleString()}\n` +
                            `❌ Помилок: ${result.stats.failedCount}`);
                    } catch (error: any) {
                      console.error('Помилка витягування:', error);
                      alert('❌ Помилка витягування тексту: ' + error.message);
                    } finally {
                      setIsExtracting(false);
                    }
                  }}
                  disabled={isExtracting}
                  className="w-full mt-4 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                >
                  <FileText className="w-5 h-5" />
                  {isExtracting ? 'Витягую текст з unpdf...' : `📝 Витягти ЯКІСНИЙ текст з усіх ${settings.resume_files?.length || 1} резюме (unpdf)`}
                </button>

                {/* Extracted Text Display */}
                {extractedText && (
                  <div className="mt-4 bg-gray-50 border border-gray-300 rounded-lg p-4">
                    <div className="flex justify-between items-center mb-2">
                      <h4 className="text-sm font-semibold text-gray-900">📄 Витягнутий текст ({extractedText.length} символів)</h4>
                      <button
                        onClick={() => setExtractedText('')}
                        className="text-xs text-gray-600 hover:text-red-600"
                      >
                        ✕ Очистити
                      </button>
                    </div>
                    <div className="bg-white border border-gray-200 rounded p-3 max-h-96 overflow-y-auto">
                      <pre className="text-xs font-mono whitespace-pre-wrap text-gray-700">
                        {extractedText}
                      </pre>
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      💡 Цей текст буде відправлений в AI для аналізу
                    </p>
                  </div>
                )}

                {/* Analyze Button */}
                <button
                  onClick={async () => {
                    if (!user) return;

                    // Якщо текст не витягнуто, попередити
                    if (!extractedText) {
                      const confirm = window.confirm('⚠️ Текст ще не витягнуто!\n\nСпочатку натисніть "📝 Витягти текст з усіх резюме" щоб переглянути що буде відправлено в AI.\n\nАбо продовжити аналіз зараз (Edge Function витягне текст автоматично з unpdf)?');
                      if (!confirm) return;
                    }

                    setIsSaving(true);
                    try {
                      await analyzeResumes.mutateAsync({ userId: user.id });
                      await refetchAIProfile();
                      alert('✅ Резюме проаналізовані успішно!\n\nПерейдіть вниз щоб побачити AI-витягнуті дані.');
                    } catch (error: any) {
                      alert('❌ Помилка аналізу: ' + error.message);
                    } finally {
                      setIsSaving(false);
                    }
                  }}
                  disabled={isSaving || (!settings.resume_files && !settings.resume_storage_path)}
                  className="w-full mt-4 bg-gradient-to-r from-purple-600 to-blue-600 text-white px-6 py-3 rounded-lg hover:from-purple-700 hover:to-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 font-semibold"
                >
                  <Sparkles className="w-5 h-5" />
                  {isSaving ? 'Аналізую резюме з AI...' : `✨ Аналізувати ${extractedText ? 'витягнутий текст' : `всі ${settings.resume_files?.length || 1} резюме`} з AI`}
                </button>

                <p className="text-xs text-gray-500 mt-2 text-center">
                  {extractedText
                    ? '🤖 AI проаналізує витягнутий текст і створить профіль'
                    : '🤖 Рекомендується спочатку витягнути текст для перегляду'}
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

                {/* Check if this is a custom prompt response */}
                {aiProfile.career_objective === 'Custom AI Profile Analysis' && aiProfile.professional_summary ? (
                  <div className="bg-white border-2 border-purple-300 rounded-lg p-4">
                    <div className="mb-4 flex items-center gap-2">
                      <span className="px-3 py-1 bg-purple-100 text-purple-700 text-xs font-semibold rounded-full">
                        🎨 Custom AI Analysis
                      </span>
                      <span className="text-sm text-gray-500">
                        Generated using your custom prompt structure
                      </span>
                    </div>

                    <div className="bg-gray-50 p-4 rounded border border-gray-200 overflow-x-auto">
                      <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800">{aiProfile.professional_summary}</pre>
                    </div>
                  </div>
                ) : (
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
                )}

                <p className="text-sm text-gray-500">
                  Parsed at: {new Date(aiProfile.parsed_at).toLocaleString()}
                </p>

                {/* Save Profile Button */}
                <div className="mt-6 border-t pt-4">
                  {!showSaveDialog ? (
                    <button
                      onClick={() => setShowSaveDialog(true)}
                      className="flex items-center gap-2 bg-purple-600 text-white px-6 py-3 rounded-lg hover:bg-purple-700 transition-colors"
                    >
                      <Archive className="w-5 h-5" />
                      💾 Зберегти профіль
                    </button>
                  ) : (
                    <div className="space-y-4 bg-purple-50 p-4 rounded-lg border border-purple-200">
                      <h4 className="font-semibold text-purple-900">Збереження профілю</h4>
                      <div>
                        <label className="block text-sm font-medium text-purple-700 mb-2">
                          Назва профілю (необов'язково)
                        </label>
                        <input
                          type="text"
                          value={profileName}
                          onChange={(e) => setProfileName(e.target.value)}
                          placeholder="Наприклад: Senior Frontend Developer або залиште порожнім для автоназви"
                          className="w-full px-4 py-2 border border-purple-300 rounded-lg focus:ring-2 focus:ring-purple-500 focus:border-transparent"
                        />
                        <p className="text-xs text-purple-600 mt-1">
                          💡 Якщо залишити порожнім, профіль буде збережено з поточною датою та часом
                        </p>
                      </div>
                      <div className="flex gap-2">
                        <button
                          onClick={handleSaveCurrentProfile}
                          disabled={isSaving}
                          className="flex items-center gap-2 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 disabled:opacity-50"
                        >
                          <Save className="w-4 h-4" />
                          {isSaving ? 'Збереження...' : 'Зберегти'}
                        </button>
                        <button
                          onClick={() => {
                            setShowSaveDialog(false);
                            setProfileName('');
                          }}
                          className="px-4 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
                        >
                          Скасувати
                        </button>
                      </div>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Saved Profiles List */}
            {savedProfiles && savedProfiles.length > 0 && (
              <div className="mt-8 space-y-4">
                <h3 className="text-lg font-semibold text-gray-900 flex items-center gap-2">
                  <Archive className="w-5 h-5 text-purple-600" />
                  Збережені профілі ({savedProfiles.length})
                </h3>

                <div className="space-y-3">
                  {savedProfiles.map((savedProfile: any) => (
                    <div
                      key={savedProfile.id}
                      className={`bg-white border rounded-lg p-4 ${
                        savedProfile.is_active
                          ? 'border-green-500 shadow-md'
                          : 'border-gray-200'
                      }`}
                    >
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <h4 className="font-semibold text-gray-900">
                              {savedProfile.profile_name}
                            </h4>
                            {savedProfile.is_active && (
                              <span className="flex items-center gap-1 px-2 py-1 bg-green-100 text-green-700 text-xs rounded-full">
                                <Star className="w-3 h-3 fill-current" />
                                Активний
                              </span>
                            )}
                          </div>

                          <div className="text-sm text-gray-600 space-y-1">
                            <p>
                              📄 Резюме: {savedProfile.total_resumes_analyzed} шт.
                            </p>
                            <p>
                              🗓️ Створено: {new Date(savedProfile.created_at).toLocaleString('uk-UA')}
                            </p>
                            {savedProfile.description && (
                              <p className="text-gray-500 italic">{savedProfile.description}</p>
                            )}
                          </div>

                          {/* Profile data preview */}
                          {savedProfile.profile_data && (
                            <div className="mt-3 p-3 bg-gray-50 rounded text-xs space-y-1">
                              {savedProfile.profile_data.full_name && (
                                <p><strong>Ім'я:</strong> {savedProfile.profile_data.full_name}</p>
                              )}
                              {savedProfile.profile_data.professional_summary && (
                                <p className="text-gray-600 line-clamp-2">
                                  {savedProfile.profile_data.professional_summary}
                                </p>
                              )}
                              {savedProfile.profile_data.technical_skills && savedProfile.profile_data.technical_skills.length > 0 && (
                                <p>
                                  <strong>Навички:</strong> {savedProfile.profile_data.technical_skills.slice(0, 5).join(', ')}
                                  {savedProfile.profile_data.technical_skills.length > 5 && '...'}
                                </p>
                              )}
                            </div>
                          )}
                        </div>

                        <div className="flex flex-col gap-2 ml-4">
                          {!savedProfile.is_active && (
                            <button
                              onClick={() => handleActivateProfile(savedProfile.id)}
                              className="flex items-center gap-1 px-3 py-2 bg-green-100 text-green-700 rounded-lg hover:bg-green-200 text-sm"
                              title="Активувати цей профіль для оцінки вакансій"
                            >
                              <Star className="w-4 h-4" />
                              Активувати
                            </button>
                          )}
                          <button
                            onClick={() => handleDeleteSavedProfile(savedProfile.id, savedProfile.profile_name)}
                            className="flex items-center gap-1 px-3 py-2 bg-red-50 text-red-600 rounded-lg hover:bg-red-100 text-sm"
                          >
                            <Trash2 className="w-4 h-4" />
                            Видалити
                          </button>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>

                <div className="mt-4 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <p className="text-sm text-blue-900">
                    ℹ️ <strong>Як це працює:</strong> Активний профіль використовується AI для оцінки релевантності вакансій.
                    Ви можете зберігати різні версії профілів для різних типів вакансій (наприклад, Frontend, Backend, Full-stack)
                    і перемикатися між ними.
                  </p>
                </div>
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

            {/* Scrape Jobs Button */}
            {finnUrls.length > 0 && (
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div>
                    <h3 className="font-medium text-blue-900">Manual Job Scraping</h3>
                    <p className="text-sm text-blue-700 mt-1">
                      Scrape jobs from {finnUrls.length} FINN.no URL{finnUrls.length > 1 ? 's' : ''}
                    </p>
                  </div>
                  <button
                    onClick={handleScrapeJobs}
                    disabled={isScraping}
                    className="flex items-center gap-2 bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
                  >
                    {isScraping ? (
                      <>
                        <Loader2 className="w-4 h-4 animate-spin" />
                        Scraping...
                      </>
                    ) : (
                      <>
                        <Play className="w-4 h-4" />
                        Scrape Jobs Now
                      </>
                    )}
                  </button>
                </div>

                {scrapeResults && (
                  <div className={`mt-3 p-3 rounded ${scrapeResults.success ? 'bg-green-50 border border-green-200' : 'bg-red-50 border border-red-200'}`}>
                    {scrapeResults.success ? (
                      <div className="text-sm text-green-800">
                        <div className="font-medium mb-1">✅ Scraping Complete!</div>
                        <div>📊 Found: <strong>{scrapeResults.totalScraped}</strong> jobs</div>
                        <div>💾 Saved: <strong>{scrapeResults.totalSaved}</strong> new</div>
                        <div>⏭️ Skipped: <strong>{scrapeResults.totalSkipped}</strong> duplicates</div>
                      </div>
                    ) : (
                      <div className="text-sm text-red-800">
                        ❌ Error: {scrapeResults.error}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}

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

        {/* Automation Tab */}
        {activeTab === 'automation' && (
          <div className="space-y-6">
            <div>
              <h2 className="text-xl font-semibold mb-2">Scheduled Scanning</h2>
              <p className="text-sm text-gray-600 mb-6">
                Automate job scanning by setting up a schedule. The system will automatically check for new jobs at specified times.
              </p>
            </div>

            <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <Clock className="w-5 h-5 text-blue-600 mt-0.5 flex-shrink-0" />
                <div className="space-y-2 text-sm text-blue-800">
                  <p className="font-medium">How it works:</p>
                  <ul className="list-disc list-inside space-y-1 ml-2">
                    <li>Enable automatic scanning below</li>
                    <li>Choose your preferred schedule (daily, twice daily, or custom)</li>
                    <li>System will scrape jobs, extract details, and analyze relevance automatically</li>
                    <li>Receive Telegram notifications for relevant jobs (if Telegram is enabled)</li>
                  </ul>
                </div>
              </div>
            </div>

            {/* Enable/Disable Toggle */}
            <div className="flex items-center justify-between p-4 bg-gray-50 rounded-lg">
              <div>
                <label htmlFor="schedule-enabled" className="text-sm font-medium text-gray-900">
                  Enable Scheduled Scanning
                </label>
                <p className="text-xs text-gray-500 mt-1">
                  Automatically scan for jobs based on your schedule
                </p>
              </div>
              <div className="flex items-center">
                <input
                  type="checkbox"
                  id="schedule-enabled"
                  checked={scheduleSettings.scan_schedule_enabled}
                  onChange={(e) => setScheduleSettings({ ...scheduleSettings, scan_schedule_enabled: e.target.checked })}
                  className="w-5 h-5 text-primary-600 border-gray-300 rounded focus:ring-primary-500"
                />
              </div>
            </div>

            {/* Schedule Settings */}
            <div className="space-y-4">
              {/* Schedule Mode Selection */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-3">
                  Schedule Type
                </label>
                <div className="flex gap-4">
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="scheduleMode"
                      checked={scheduleMode === 'preset'}
                      onChange={() => setScheduleMode('preset')}
                      disabled={!scheduleSettings.scan_schedule_enabled}
                      className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500 disabled:opacity-50"
                    />
                    <span className="text-sm text-gray-700">Quick presets</span>
                  </label>
                  <label className="flex items-center gap-2 cursor-pointer">
                    <input
                      type="radio"
                      name="scheduleMode"
                      checked={scheduleMode === 'custom'}
                      onChange={() => setScheduleMode('custom')}
                      disabled={!scheduleSettings.scan_schedule_enabled}
                      className="w-4 h-4 text-primary-600 border-gray-300 focus:ring-primary-500 disabled:opacity-50"
                    />
                    <span className="text-sm text-gray-700">Custom time & days</span>
                  </label>
                </div>
              </div>

              {/* Preset Mode */}
              {scheduleMode === 'preset' && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Scan Schedule
                  </label>
                  <select
                    value={scheduleSettings.scan_schedule_cron}
                    onChange={(e) => setScheduleSettings({ ...scheduleSettings, scan_schedule_cron: e.target.value })}
                    disabled={!scheduleSettings.scan_schedule_enabled}
                    className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed"
                  >
                    <option value="0 9 * * *">Every day at 9:00 AM</option>
                    <option value="0 9,18 * * *">Twice daily (9:00 AM & 6:00 PM)</option>
                    <option value="0 */6 * * *">Every 6 hours</option>
                    <option value="0 */4 * * *">Every 4 hours</option>
                    <option value="0 9 * * 1">Every Monday at 9:00 AM</option>
                    <option value="0 9 * * 1,3,5">Monday, Wednesday, Friday at 9:00 AM</option>
                  </select>
                  <p className="text-xs text-gray-500 mt-1">
                    Choose from common schedules
                  </p>
                </div>
              )}

              {/* Custom Mode */}
              {scheduleMode === 'custom' && (
                <div className="space-y-4 p-4 bg-gray-50 rounded-lg border border-gray-200">
                  <div className="grid grid-cols-2 gap-4">
                    {/* Hour */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Hour (0-23)
                      </label>
                      <select
                        value={customHour}
                        onChange={(e) => setCustomHour(e.target.value)}
                        disabled={!scheduleSettings.scan_schedule_enabled}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed"
                      >
                        {Array.from({ length: 24 }, (_, i) => (
                          <option key={i} value={i.toString()}>
                            {i.toString().padStart(2, '0')}:00
                          </option>
                        ))}
                      </select>
                    </div>

                    {/* Minute */}
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Minute (0-59)
                      </label>
                      <select
                        value={customMinute}
                        onChange={(e) => setCustomMinute(e.target.value)}
                        disabled={!scheduleSettings.scan_schedule_enabled}
                        className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed"
                      >
                        {Array.from({ length: 60 }, (_, i) => (
                          <option key={i} value={i.toString()}>
                            :{i.toString().padStart(2, '0')}
                          </option>
                        ))}
                      </select>
                    </div>
                  </div>

                  {/* Days of Week */}
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Days of Week
                    </label>
                    <div className="flex flex-wrap gap-2">
                      {[
                        { label: 'Every Day', value: '*' },
                        { label: 'Mon', value: '1' },
                        { label: 'Tue', value: '2' },
                        { label: 'Wed', value: '3' },
                        { label: 'Thu', value: '4' },
                        { label: 'Fri', value: '5' },
                        { label: 'Sat', value: '6' },
                        { label: 'Sun', value: '0' },
                      ].map((day) => {
                        const isSelected = customDays.includes(day.value);
                        return (
                          <button
                            key={day.value}
                            type="button"
                            onClick={() => handleToggleDay(day.value)}
                            disabled={!scheduleSettings.scan_schedule_enabled}
                            className={`px-3 py-2 rounded-lg text-sm font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed ${
                              isSelected
                                ? 'bg-primary-600 text-white'
                                : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                            }`}
                          >
                            {day.label}
                          </button>
                        );
                      })}
                    </div>
                    <p className="text-xs text-gray-500 mt-2">
                      Select specific days or "Every Day" to run daily
                    </p>
                  </div>

                  {/* Preview */}
                  <div className="bg-blue-50 border border-blue-200 rounded p-3">
                    <p className="text-xs text-blue-800">
                      <span className="font-medium">Preview:</span> Will run at {customHour.padStart(2, '0')}:{customMinute.padStart(2, '0')}
                      {customDays.includes('*') ? ' every day' : ` on ${customDays.map(d => ['Sun','Mon','Tue','Wed','Thu','Fri','Sat'][parseInt(d)] || 'Every Day').join(', ')}`}
                    </p>
                  </div>
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Timezone
                </label>
                <select
                  value={scheduleSettings.scan_schedule_timezone}
                  onChange={(e) => setScheduleSettings({ ...scheduleSettings, scan_schedule_timezone: e.target.value })}
                  disabled={!scheduleSettings.scan_schedule_enabled}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg disabled:bg-gray-100 disabled:cursor-not-allowed"
                >
                  <option value="Europe/Oslo">Europe/Oslo (Norway)</option>
                  <option value="Europe/Kiev">Europe/Kiev (Ukraine)</option>
                  <option value="Europe/London">Europe/London (UK)</option>
                  <option value="UTC">UTC</option>
                </select>
              </div>
            </div>

            {/* Current Schedule Info */}
            {scheduleSettings.scan_schedule_enabled && (
              <div className="bg-green-50 border border-green-200 rounded-lg p-4">
                <p className="text-sm text-green-800">
                  <span className="font-medium">✓ Active:</span> Next scan will run according to your schedule ({scheduleSettings.scan_schedule_cron}) in {scheduleSettings.scan_schedule_timezone} timezone.
                </p>
              </div>
            )}

            {/* Warning if disabled */}
            {!scheduleSettings.scan_schedule_enabled && (
              <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
                <p className="text-sm text-yellow-800">
                  <span className="font-medium">⚠ Disabled:</span> Automatic scanning is currently off. Enable it above to start scheduled scans.
                </p>
              </div>
            )}

            <button
              onClick={handleSaveScheduleSettings}
              disabled={isSaving}
              className="flex items-center gap-2 bg-primary-600 text-white px-6 py-2 rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              <Save className="w-4 h-4" />
              {isSaving ? 'Saving...' : 'Save Automation Settings'}
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
