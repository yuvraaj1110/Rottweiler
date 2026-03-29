import React, { useState } from 'react';
import axios from 'axios';

function App() {
  const [videoFile, setVideoFile] = useState(null);
  const [startTime, setStartTime] = useState('');
  const [isProcessing, setIsProcessing] = useState(false);
  const [clips, setClips] = useState([]);
  const [error, setError] = useState('');

  const handleFileChange = (e) => {
    if (e.target.files[0]) {
      setVideoFile(e.target.files[0]);
    }
  };

  const handleDragOver = (e) => {
    e.preventDefault();
  };

  const handleDrop = (e) => {
    e.preventDefault();
    if (e.dataTransfer.files[0]) {
      setVideoFile(e.dataTransfer.files[0]);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!videoFile || !startTime) {
      setError('Please select a video file and specify start time');
      return;
    }

    setIsProcessing(true);
    setError('');

    const formData = new FormData();
    formData.append('video', videoFile);
    formData.append('start_time', startTime);

    try {
      const apiUrl = import.meta.env.VITE_API_URL || 'http://localhost:8000';
      const response = await axios.post(
        `${apiUrl}/process-video`,
        formData,
        {
          headers: {
            'Content-Type': 'multipart/form-data',
          },
        }
      );

      // Assuming backend returns { clips: [{ name: string, url: string }] }
      setClips(response.data.clips || []);
    } catch (err) {
      console.error('Error processing video:', err);
      setError(
        err.response?.data?.detail || 
        err.message || 
        'Failed to process video. Please try again.'
      );
    } finally {
      setIsProcessing(false);
    }
  };

  return (
    <div className="min-h-screen bg-midnight-bg text-slate-200 font-terminal">
      <div className="max-w-6xl mx-auto px-4 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-white mb-2">
            ROTTWEILER V2.0
          </h1>
          <p className="text-xl text-midnight-slate">
            Security Terminal - Hardware-Linked Video Indexing System
          </p>
          <div className="w-16 h-0.5 bg-midnight-accent mx-auto mt-4"></div>
        </div>

        {/* Main Card */}
        <div className="bg-midnight-surface backdrop-blur-sm border border-midnight-accent/20 rounded-xl p-8 shadow-[0_0_15px_rgba(30,58,138,0.2)]">
          <form onSubmit={handleSubmit} className="space-y-6">
            {/* Video Upload Section */}
            <div className="border-2 border-dashed border-midnight-slate/30 rounded-xl p-8 text-center transition-all hover:border-midnight-accent/50">
              <div className="space-y-4">
                <div className="flex items-center justify-center space-x-3">
                  <svg className="h-6 w-6 text-midnight-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M7 16l4-4m0 0l4-4m-4 4H18" />
                  </svg>
                  <p className="text-sm font-medium">
                    {videoFile ? `Selected: ${videoFile.name}` : 'Drag & drop your .mp4 video here'}
                  </p>
                </div>
                <p className="text-xs text-slate-400">
                  or click to select
                </p>
                <input 
                  type="file" 
                  accept="video/mp4" 
                  onChange={handleFileChange}
                  className="hidden"
                />
                <button 
                  type="button"
                  onClick={() => document.querySelector('input[type="file"]').click()}
                  className="mt-4 inline-flex items-center px-4 py-2 bg-gradient-to-b from-midnight-cobalt to-midnight-accent hover:brightness-110 text-white font-semibold rounded-lg transition-all"
                >
                  Browse Files
                </button>
              </div>
            </div>

            {/* Metadata Input */}
            <div className="space-y-3">
              <label className="block text-sm font-medium text-midnight-slate">
                Video Start Time (Real-world UTC)
              </label>
              <div className="relative">
                <input
                  type="datetime-local"
                  value={startTime}
                  onChange={(e) => setStartTime(e.target.value)}
                  className="w-full pl-10 pr-4 py-3 bg-midnight-bg border border-midnight-accent/30 rounded-lg text-slate-100 focus:outline-none focus:ring-2 focus:ring-midnight-cobalt focus:border-midnight-cobalt"
                  required
                />
                <div className="absolute inset-y-0 left-0 flex items-center pl-3 pointer-events-none">
                  <svg className="h-5 w-5 text-slate-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                  </svg>
                </div>
              </div>
            </div>

            {/* Submit Button */}
            <button
              type="submit"
              disabled={isProcessing || !videoFile || !startTime}
              className="w-full flex items-center justify-center py-3 px-6 bg-gradient-to-b from-midnight-cobalt to-midnight-accent hover:brightness-110 text-white font-bold rounded-lg transition-all duration-200 transform hover:-translate-y-0.5"
            >
              {isProcessing ? (
                <>
                  <svg className="animate-spin h-5 w-5 mr-2" fill="none" viewBox="0 0 24 24">
                    <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                    <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8z"></path>
                  </svg>
                  Processing Video...
                </>
              ) : (
                <>
                  <svg className="h-5 w-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4l3 3"></path>
                  </svg>
                  Process Video
                </>
              )}
            </button>
          </form>
        </div>

        {/* Error Message */}
        {error && (
          <div className="mt-6 p-4 bg-red-900/50 border border-red-500/30 rounded-lg text-red-400">
            <div className="flex items-center space-x-3">
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
              <span>{error}</span>
            </div>
          </div>
        )}

        {/* Results Gallery */}
        {clips.length > 0 && (
          <div className="mt-10">
            <div className="flex items-center justify-between mb-6">
              <h2 className="text-2xl font-bold text-white">
                Generated Clips ({clips.length})
              </h2>
              <div className="text-sm text-midnight-slate">
                Ready for download • {clips.length} clip{clips.length !== 1 ? 's' : ''}
              </div>
            </div>
            <div className="grid gap-6">
              {/* Responsive grid: 1col on mobile, 2col on tablet, 3col on desktop */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
                {clips.map((clip, index) => (
                  <div key={index} className="bg-midnight-surface border border-midnight-accent/20 rounded-xl p-6 hover:border-midnight-accent/40 transition-all duration-200">
                    <div className="flex items-center justify-between mb-4">
                      <div className="flex items-center space-x-3">
                        <div className="h-8 w-8 bg-midnight-accent/20 rounded-full flex items-center justify-center">
                          <svg className="h-4 w-4 text-midnight-accent" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M8 7V3m8 4V3m-9 8h10M5 21h14a2 2 0 002-2V9a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
                          </svg>
                        </div>
                        <span className="font-mono text-sm">{clip.name}</span>
                      </div>
                      <a 
                        href={clip.url} 
                        download={clip.name}
                        className="inline-flex items-center px-3 py-1 bg-gradient-to-b from-midnight-cobalt to-midnight-accent hover:brightness-110 text-white text-xs font-semibold rounded transition-colors"
                      >
                        Download
                        <svg className="ml-2 h-3 w-3" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2 2 2 0 11-2 2 2 2 0 11z" />
                        </svg>
                      </a>
                    </div>
                    <div className="text-xs text-slate-400">
                      30-second security clip • Generated from motion event
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;