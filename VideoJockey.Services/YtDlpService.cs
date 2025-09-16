using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.Extensions.Logging;
using VideoJockey.Core.Interfaces;

namespace VideoJockey.Services
{
    public class YtDlpService : IYtDlpService
    {
        private readonly ILogger<YtDlpService> _logger;
        private readonly string _ytDlpPath;
        private readonly string _cookiesPath;
        private static readonly Regex ProgressRegex = new(@"\[download\]\s+(\d+\.?\d*)%\s+of\s+~?\s*(\S+)\s+at\s+(\S+)\s+ETA\s+(\S+)", RegexOptions.Compiled);
        private static readonly Regex DownloadedBytesRegex = new(@"\[download\]\s+(\d+\.?\d*)%\s+of\s+(\S+)", RegexOptions.Compiled);
        
        public YtDlpService(ILogger<YtDlpService> logger)
        {
            _logger = logger;
            _ytDlpPath = GetYtDlpPath();
            _cookiesPath = Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "data", "cookies.txt");
        }
        
        private string GetYtDlpPath()
        {
            // Check common locations
            var paths = new[]
            {
                "/usr/local/bin/yt-dlp",
                "/usr/bin/yt-dlp",
                Path.Combine(AppDomain.CurrentDomain.BaseDirectory, "yt-dlp"),
                "yt-dlp" // Will use PATH
            };
            
            foreach (var path in paths)
            {
                if (File.Exists(path))
                {
                    _logger.LogInformation("Found yt-dlp at: {Path}", path);
                    return path;
                }
            }
            
            // Default to PATH lookup
            return "yt-dlp";
        }
        
        public async Task<DownloadResult> DownloadVideoAsync(string url, string outputPath, IProgress<DownloadProgress>? progress = null, CancellationToken cancellationToken = default)
        {
            try
            {
                var result = new DownloadResult();
                var startTime = DateTime.UtcNow;
                
                // First get metadata
                var metadata = await GetVideoMetadataAsync(url, cancellationToken);
                result.Metadata = metadata;
                
                // Prepare download arguments
                var args = new List<string>
                {
                    "--no-warnings",
                    "--no-playlist",
                    "--format", "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best",
                    "--merge-output-format", "mp4",
                    "--output", outputPath,
                    "--newline",
                    "--no-colors"
                };
                
                // Add cookies if available
                if (File.Exists(_cookiesPath))
                {
                    args.AddRange(new[] { "--cookies", _cookiesPath });
                }
                
                args.Add(url);
                
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = _ytDlpPath,
                    Arguments = string.Join(" ", args),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                using var process = new Process { StartInfo = processStartInfo };
                var outputLines = new List<string>();
                
                process.OutputDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        outputLines.Add(e.Data);
                        ParseProgress(e.Data, progress);
                    }
                };
                
                process.ErrorDataReceived += (sender, e) =>
                {
                    if (!string.IsNullOrEmpty(e.Data))
                    {
                        _logger.LogWarning("yt-dlp error: {Error}", e.Data);
                    }
                };
                
                process.Start();
                process.BeginOutputReadLine();
                process.BeginErrorReadLine();
                
                await process.WaitForExitAsync(cancellationToken);
                
                result.Duration = DateTime.UtcNow - startTime;
                
                if (process.ExitCode == 0)
                {
                    result.Success = true;
                    result.FilePath = outputPath;
                    _logger.LogInformation("Successfully downloaded video to: {Path}", outputPath);
                }
                else
                {
                    result.Success = false;
                    result.ErrorMessage = $"yt-dlp exited with code {process.ExitCode}";
                    _logger.LogError("Download failed: {Error}", result.ErrorMessage);
                }
                
                return result;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error downloading video from {Url}", url);
                return new DownloadResult
                {
                    Success = false,
                    ErrorMessage = ex.Message
                };
            }
        }
        
        public async Task<List<SearchResult>> SearchVideosAsync(string query, int maxResults = 10, CancellationToken cancellationToken = default)
        {
            try
            {
                var searchUrl = $"ytsearch{maxResults}:{query}";
                var args = new List<string>
                {
                    "--no-warnings",
                    "--dump-json",
                    "--flat-playlist",
                    "--no-playlist",
                    searchUrl
                };
                
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = _ytDlpPath,
                    Arguments = string.Join(" ", args),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                using var process = Process.Start(processStartInfo);
                if (process == null)
                    throw new InvalidOperationException("Failed to start yt-dlp process");
                
                var output = await process.StandardOutput.ReadToEndAsync(cancellationToken);
                await process.WaitForExitAsync(cancellationToken);
                
                var results = new List<SearchResult>();
                var lines = output.Split('\n', StringSplitOptions.RemoveEmptyEntries);
                
                foreach (var line in lines)
                {
                    try
                    {
                        using var doc = JsonDocument.Parse(line);
                        var root = doc.RootElement;
                        
                        var result = new SearchResult
                        {
                            Id = root.GetProperty("id").GetString() ?? "",
                            Title = root.GetProperty("title").GetString() ?? "",
                            Url = root.GetProperty("url").GetString() ?? $"https://www.youtube.com/watch?v={root.GetProperty("id").GetString()}",
                            Channel = root.TryGetProperty("channel", out var channel) ? channel.GetString() : null,
                            ThumbnailUrl = root.TryGetProperty("thumbnail", out var thumb) ? thumb.GetString() : null
                        };
                        
                        if (root.TryGetProperty("duration", out var duration))
                        {
                            if (duration.TryGetDouble(out var seconds))
                            {
                                result.Duration = TimeSpan.FromSeconds(seconds);
                            }
                        }
                        
                        if (root.TryGetProperty("view_count", out var viewCount))
                        {
                            result.ViewCount = viewCount.GetInt64();
                        }
                        
                        results.Add(result);
                    }
                    catch (JsonException ex)
                    {
                        _logger.LogWarning(ex, "Failed to parse search result JSON");
                    }
                }
                
                return results;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error searching for videos with query: {Query}", query);
                return new List<SearchResult>();
            }
        }
        
        public async Task<YtDlpVideoMetadata> GetVideoMetadataAsync(string url, CancellationToken cancellationToken = default)
        {
            try
            {
                var args = new List<string>
                {
                    "--no-warnings",
                    "--dump-json",
                    "--no-playlist",
                    url
                };
                
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = _ytDlpPath,
                    Arguments = string.Join(" ", args),
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                using var process = Process.Start(processStartInfo);
                if (process == null)
                    throw new InvalidOperationException("Failed to start yt-dlp process");
                
                var output = await process.StandardOutput.ReadToEndAsync(cancellationToken);
                await process.WaitForExitAsync(cancellationToken);
                
                using var doc = JsonDocument.Parse(output);
                var root = doc.RootElement;
                
                var metadata = new YtDlpVideoMetadata
                {
                    Id = root.GetProperty("id").GetString() ?? "",
                    Title = root.GetProperty("title").GetString() ?? "",
                    Channel = root.TryGetProperty("channel", out var channel) ? channel.GetString() : null,
                    Description = root.TryGetProperty("description", out var desc) ? desc.GetString() : null,
                    ThumbnailUrl = root.TryGetProperty("thumbnail", out var thumb) ? thumb.GetString() : null
                };
                
                // Extract artist from title or uploader
                if (root.TryGetProperty("artist", out var artist))
                {
                    metadata.Artist = artist.GetString();
                }
                else if (root.TryGetProperty("uploader", out var uploader))
                {
                    metadata.Artist = uploader.GetString();
                }
                
                // Duration
                if (root.TryGetProperty("duration", out var duration) && duration.TryGetDouble(out var seconds))
                {
                    metadata.Duration = TimeSpan.FromSeconds(seconds);
                }
                
                // Upload date
                if (root.TryGetProperty("upload_date", out var uploadDate))
                {
                    var dateStr = uploadDate.GetString();
                    if (!string.IsNullOrEmpty(dateStr) && dateStr.Length == 8)
                    {
                        if (DateTime.TryParseExact(dateStr, "yyyyMMdd", null, System.Globalization.DateTimeStyles.None, out var date))
                        {
                            metadata.UploadDate = date;
                        }
                    }
                }
                
                // View count
                if (root.TryGetProperty("view_count", out var viewCount))
                {
                    metadata.ViewCount = viewCount.GetInt64();
                }
                
                // Like count
                if (root.TryGetProperty("like_count", out var likeCount))
                {
                    metadata.LikeCount = likeCount.GetInt64();
                }
                
                // Video dimensions
                if (root.TryGetProperty("width", out var width))
                {
                    metadata.Width = width.GetInt32();
                }
                
                if (root.TryGetProperty("height", out var height))
                {
                    metadata.Height = height.GetInt32();
                }
                
                // FPS
                if (root.TryGetProperty("fps", out var fps))
                {
                    metadata.Fps = fps.GetDouble();
                }
                
                // Codecs
                if (root.TryGetProperty("vcodec", out var vcodec))
                {
                    metadata.VideoCodec = vcodec.GetString();
                }
                
                if (root.TryGetProperty("acodec", out var acodec))
                {
                    metadata.AudioCodec = acodec.GetString();
                }
                
                // Tags
                if (root.TryGetProperty("tags", out var tags) && tags.ValueKind == JsonValueKind.Array)
                {
                    metadata.Tags = tags.EnumerateArray()
                        .Select(t => t.GetString())
                        .Where(t => !string.IsNullOrEmpty(t))
                        .Cast<string>()
                        .ToList();
                }
                
                return metadata;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting metadata for URL: {Url}", url);
                throw;
            }
        }
        
        public async Task<bool> ValidateInstallationAsync()
        {
            try
            {
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = _ytDlpPath,
                    Arguments = "--version",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                using var process = Process.Start(processStartInfo);
                if (process == null)
                    return false;
                
                await process.WaitForExitAsync();
                return process.ExitCode == 0;
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error validating yt-dlp installation");
                return false;
            }
        }
        
        public async Task<string> GetVersionAsync()
        {
            try
            {
                var processStartInfo = new ProcessStartInfo
                {
                    FileName = _ytDlpPath,
                    Arguments = "--version",
                    UseShellExecute = false,
                    RedirectStandardOutput = true,
                    RedirectStandardError = true,
                    CreateNoWindow = true
                };
                
                using var process = Process.Start(processStartInfo);
                if (process == null)
                    return "Unknown";
                
                var version = await process.StandardOutput.ReadToEndAsync();
                await process.WaitForExitAsync();
                
                return version.Trim();
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Error getting yt-dlp version");
                return "Unknown";
            }
        }
        
        private void ParseProgress(string line, IProgress<DownloadProgress>? progress)
        {
            if (progress == null) return;
            
            var match = ProgressRegex.Match(line);
            if (match.Success)
            {
                var downloadProgress = new DownloadProgress
                {
                    Status = "Downloading",
                    Percentage = double.Parse(match.Groups[1].Value),
                    DownloadSpeed = match.Groups[3].Value,
                    ETA = match.Groups[4].Value
                };
                
                progress.Report(downloadProgress);
            }
            else if (line.Contains("[download] Destination:"))
            {
                progress.Report(new DownloadProgress { Status = "Starting download", Percentage = 0 });
            }
            else if (line.Contains("[Merger]"))
            {
                progress.Report(new DownloadProgress { Status = "Merging audio and video", Percentage = 100 });
            }
            else if (line.Contains("[ExtractAudio]"))
            {
                progress.Report(new DownloadProgress { Status = "Extracting audio", Percentage = 95 });
            }
        }
    }
}