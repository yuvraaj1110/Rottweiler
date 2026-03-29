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
      const response = await axios.post(
        'http://localhost:8000/process-video',
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
    <div className="min-h-screen bg-gray-900 text-gray-100 p-6">
      <div className="max-w-4xl mx-auto">
        <header className="text-center mb-8">
          <h1 className="text-3xl font-bold text-amber-400">
            Rottweiler V2.0
          </h1>
          <p className="mt-2 text-gray-400">
            Security-focused video clipping tool
          </p>
        </header>

        <form onSubmit={handleSubmit} className="space-y-6">
          {/* Video Upload Section */}
          <div 
            className="border-2 border-dashed border-gray-600 rounded-lg p-8 text-center transition-colors hover:border-gray-400"
            onDragOver={handleDragOver}
            onDrop={handleDrop}
          >
            <p className="text-gray-400 mb-2">
              {videoFile ? `Selected: ${videoFile.name}` : 'Drag & drop your .mp4 video here or click to select'}
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
              className="mt-4 inline-block bg-gray-800 hover:bg-gray-700 text-amber-300 font-semibold py-2 px-4 rounded transition-colors"
            >
              Browse Files
            </button>
          </div>

          {/* Metadata Input */}
          <div className="space-y-2">
            <label className="block text-sm font-medium text-gray-300">
              Video Start Time (Real-world)
            </label>
            <input
              type="datetime-local"
              value={startTime}
              onChange={(e) => setStartTime(e.target.value)}
              className="w-full bg-gray-800 border-gray-600 rounded-md text-gray-100 py-2 px-3 focus:outline-none focus:ring-2 focus-ring-amber-400"
              required
            />
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isProcessing || !videoFile || !startTime}
            className="w-full bg-amber-600 hover:bg-amber-700 text-gray-900 font-bold py-3 px-6 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isProcessing ? 'Processing Video...' : 'Process Video'}
          </button>
        </form>

        {/* Error Message */}
        {error && (
          <div className="mt-4 p-4 bg-red-900/50 border border-red-500 rounded-lg text-red-400">
            {error}
          </div>
        )}

        {/* Results Gallery */}
        {clips.length > 0 && (
          <div className="mt-8">
            <h2 className="text-xl font-bold text-amber-400 mb-4">
              Generated Clips ({clips.length})
            </h2>
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {clips.map((clip, index) => (
                <div key={index} className="bg-gray-800 rounded-lg p-4 border border-gray-700 hover:border-amber-400 transition-border">
                  <div className="flex items-center justify-between mb-2">
                    <span className="font-mono text-sm text-gray-300">
                      {clip.name}
                    </span>
                    <a 
                      href={clip.url} 
                      download={clip.name}
                      className="bg-emerald-600 hover:bg-emerald-700 text-white text-sm font-semibold py-1 px-3 rounded transition-colors"
                    >
                      Download
                    </a>
                  </div>
                  <div className="mt-2 text-xs text-gray-500">
                    Ready for download
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

export default App;